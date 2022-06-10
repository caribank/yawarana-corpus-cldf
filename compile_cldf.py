import json
import logging
import sys
from pathlib import Path
import pandas as pd
import pybtex
import pycldf
import pyigt
import yaml
from cffconvert.cli.create_citation import create_citation
from cffconvert.cli.validate_or_write_output import validate_or_write_output
from cldfbench import CLDFSpec
from cldfbench.cldf import CLDFWriter
from clld_morphology_plugin.cldf import (
    FormSlices,
    InflectionTable,
    LexemeLexemeParts,
    LexemeMorphemeParts,
    LexemeTable,
    MorphsetTable,
    MorphTable,
    POSTable,
)
from clldutils import jsonlib
from clldutils.loglib import get_colorlog
from pycldf.sources import Source
from pylacoan.annotator import Segmentizer
from pylacoan.helpers import get_pos, ortho_strip, sort_uniparser_ids
from pylingdocs.cldf import metadata as cldf_md
from pylingdocs.models import Text
from pylingdocs.preprocessing import preprocess_cldfviz
from slugify import slugify as sslug
from yawarana_helpers import add_gloss, generate_id, generate_if_empty

log = get_colorlog(__name__, sys.stdout, level=logging.INFO)


bare_slugs = 0
zero_slugged = {}

# for generating IDs for stuff that would just get ""
def slugify(input_str):
    global bare_slugs
    global zero_slugged
    slug = sslug(input_str)
    if slug == "":
        if input_str not in zero_slugged:
            bare_slugs += 1
            zero_slugged[input_str] = f"slug-{bare_slugs}"
        return zero_slugged[input_str]
    else:
        return slug


# easily modify an existing CLDF table column specification to add a separator
def custom_spec(component, column, separator="; "):
    path = (
        Path(pycldf.__file__)
        .resolve()
        .parent.joinpath("components", f"{component}-metadata.json")
    )
    metadata = json.load(open(path, "r"))
    for col in metadata["tableSchema"]["columns"]:
        if col["name"] == column:
            if separator:
                col["separator"] = separator
            elif "separator" in column:
                del col["separator"]
            return col


# only well-glossed texts and presentable documents make it into release versions
release = len(sys.argv) > 1 and sys.argv[1] == "release"

## use pandas to read csvs and not add np.nan
def cread(filename):
    df = pd.read_csv(filename, keep_default_na=False)
    return df


##location where all audio is stored
audio_path = Path(
    "/home/florianm/Dropbox/research/cariban/yawarana/yawarana_corpus/audio"
)

# used for tokenizing words
segmentizer = Segmentizer(
    segments=cread("etc/phonemes.csv").to_dict(orient="records"), delete=["-", "∅"]
)

# audio files potentially matching word forms
word_audios = {}
for filename in Path("/home/florianm/Downloads/New_Dictionary_Clippings").iterdir():
    leggo = filename.stem.split("_")[3].split("-")[0]
    word_audios.setdefault(leggo, [])
    word_audios[leggo].append(filename)

# version of the dataset is loaded from the pylingdocs metadata
version = yaml.load(open("raw/metadata.yaml"), Loader=yaml.SafeLoader)["version"]

# using cffconvert to easily create citation string for CLDF metadata
citation = create_citation(infile="CITATION.cff", url=None)
validate_or_write_output(
    outputformat="apalike",
    citation=citation,
    outfile="/tmp/citation.txt",
    validate_only=False,
)
citation = open("/tmp/citation.txt", "r", encoding="utf8").read().strip()

# main part
spec = CLDFSpec(dir="cldf", module="Generic", metadata_fname="metadata.json")
with CLDFWriter(spec) as writer:
    log.info("Setting up dataset properties")
    writer.cldf.properties.setdefault("rdf:ID", "yawarana-sketch")
    writer.cldf.properties.setdefault(
        "dc:title", f"A digital sketch grammar of Yawarana (v{version})"
    )
    writer.cldf.properties.setdefault("dc:bibliographicCitation", citation)
    writer.cldf.properties.setdefault(
        "dc:description",
        """This is a CLDF dataset containing a digital description of Yawarana.
The following linguistic entities and properties are encoded:
* sentences
* word forms
* lexemes
* morphemes
* morphs
* parts of speech

It also contains descriptive texts with references to the data.""",
    )
    writer.cldf.properties[
        "dc:license"
    ] = "https://creativecommons.org/licenses/by-sa/4.0/"
    writer.cldf.properties["dc:identifier"] = "https://fl.mt/yawarana-sketch"

    log.info("Adding chapters and authors")
    doc_path = Path("raw/docs")
    writer.cldf.add_component(cldf_md("ChapterTable"))
    chapters = pd.read_csv(doc_path / "chapters.csv")
    for chapter in chapters.to_dict("records"):
        writer.objects["ChapterTable"].append(
            {
                "ID": chapter["ID"],
                "Name": chapter["title"],
                "Number": chapter["Number"],
                "Description": open(doc_path / chapter["Filename"], "r").read(),
            }
        )

    writer.objects["ChapterTable"].append(
        {
            "ID": "landingpage",
            "Name": "Landing page",
            "Description": open("raw/landingpage.txt", "r").read(),
        }
    )

    if not release:
        writer.objects["ChapterTable"].append(
            {
                "ID": "ambiguity",
                "Name": "Manuscript: Parsing ambiguity",
                "Description": open("raw/ambiguity.txt", "r").read(),
            }
        )

    writer.cldf.add_component(cldf_md("ContributorTable"))
    for contributor in pd.read_csv("etc/contributors.csv").to_dict("records"):
        contributor["Name"] = contributor["First"] + " " + contributor["Given"]
        writer.objects["ContributorTable"].append(contributor)

    log.info("Adding linguistic components")
    writer.cldf.add_component("ExampleTable")
    writer.cldf.add_columns(
        "ExampleTable",
        # examples can refer to texts
        {
            "name": "Text_ID",
            "dc:extent": "singlevalued",
            "dc:description": "The text to which this record belongs",
            "datatype": "string",
        },
        # if they do, they have a number inside that text
        {
            "name": "Part",
            "dc:extent": "singlevalued",
            "dc:description": "Position in the text",
            "datatype": "integer",
        },
        # alternatively, they can come from a source
        {
            "name": "Source",
            "required": False,
            "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#source",
            "datatype": {"base": "string"},
            "separator": ";",
        },
        # contact language was spanish, we are keeping the translations
        {
            "name": "Original_Translation",
            "required": False,
            "dc:extent": "singlevalued",
            "dc:description": "The original translation of the example text.",
            "datatype": "string",
        },
        # a bunch of comma-separated sentence tags
        {"name": "Tags", "required": False, "datatype": "string", "separator": ","},
    )
    writer.cldf.add_component("FormTable")  # word forms
    writer.cldf.add_component("ParameterTable")  # meanings
    writer.cldf.add_component("MediaTable")  # audio files
    writer.cldf.add_component("LanguageTable")
    writer.cldf.add_component(
        LexemeMorphemeParts
    )  # what derivational morpheme creates a lexeme?
    writer.cldf.add_component(
        LexemeLexemeParts
    )  # what lexeme is a complex lexeme based on?
    writer.cldf.add_component(FormSlices)  # what morphs are part of a wordform?
    writer.cldf.add_component(POSTable)  # parts of speech
    writer.cldf.add_component(LexemeTable)
    writer.cldf.add_component(
        InflectionTable
    )  # what wordforms belong to what lexemes? no actual inflection yet
    writer.cldf.add_component(
        cldf_md("ExampleSlices")
    )  # what wordforms occur in what examples?
    writer.cldf.remove_columns(
        "FormTable", "Parameter_ID"
    )  # forms can have different translations / meanings
    writer.cldf.add_columns(
        "FormTable",
        custom_spec("FormTable", "Parameter_ID", separator="; "),
        {
            "name": "POS",
            "dc:extent": "singlevalued",
            "dc:description": "Part of speech",
            "datatype": "string",
        },  # and a part of speech
        {
            "name": "Translation",
            "required": False,
            "dc:extent": "singlevalued",
            "dc:description": "A human-friendly translation",
            "datatype": "string",
        },  # ...and a free translation not tied to the ParameterTable. this is only used by pylingdocs
    )
    writer.cldf.add_component(MorphTable)  # morphs (AKA 'allomorphs')
    writer.cldf.add_component(MorphsetTable)  # morphemes
    writer.cldf.add_component(jsonlib.load("etc/PhonemeTable-metadata.json"))
    writer.cldf.add_component(Text.cldf_metadata())

    # various foreign keys
    writer.cldf.add_foreign_key("FormTable", "POS", "POSTable", "ID")
    writer.cldf.add_foreign_key("MorphTable", "Morpheme_ID", "MorphsetTable", "ID")
    writer.cldf.add_foreign_key("FormSlices", "Form_ID", "FormTable", "ID")
    writer.cldf.add_foreign_key("FormSlices", "Morph_ID", "MorphTable", "ID")
    writer.cldf.add_foreign_key("FormSlices", "Form_Meaning", "ParameterTable", "ID")
    writer.cldf.add_foreign_key(
        "FormSlices", "Morpheme_Meaning", "ParameterTable", "ID"
    )
    writer.cldf.add_foreign_key("ExampleSlices", "Form_ID", "FormTable", "ID")
    writer.cldf.add_foreign_key("ExampleSlices", "Example_ID", "ExampleTable", "ID")
    writer.cldf.add_foreign_key("ExampleSlices", "Parameter_ID", "ParameterTable", "ID")
    writer.cldf.add_foreign_key("ExampleTable", "Text_ID", "TextTable", "ID")
    writer.cldf.add_foreign_key("InflectionTable", "Form_ID", "FormTable", "ID")
    writer.cldf.add_foreign_key("InflectionTable", "Lexeme_ID", "LexemeTable", "ID")
    writer.cldf.add_foreign_key(
        "LexemeMorphemeParts", "Morpheme_ID", "MorphsetTable", "ID"
    )
    writer.cldf.add_foreign_key("LexemeMorphemeParts", "Lexeme_ID", "LexemeTable", "ID")
    writer.cldf.add_foreign_key("LexemeLexemeParts", "Base_ID", "LexemeTable", "ID")
    writer.cldf.add_foreign_key("LexemeLexemeParts", "Lexeme_ID", "LexemeTable", "ID")

    log.info("Reading data")
    pos = cread("etc/pos.csv")
    pos_list = list(pos["ID"])

    # there are some texts that have no proper record IDs; we generate new ones for these
    bad_ids = ["GrMe", "grme"]

    def get_id(row):
        if row["ID"] not in bad_ids:
            return row["ID"].replace(".", "-").replace("​", "").lower()
        else:
            return row["ID"].lower() + "-" + str(int(float(row["Part"])))

    bad_texts = [
        "CtoOroAnPe"
    ]  # texts that should never ever make it into the corpus (as one piece)

    log.info("Corpus")
    examples = cread("../yawarana_corpus/yawarana_pylacoan/output/parsed.csv")
    # examples["Sentence"] = examples["Sentence"].replace("", "***") #don't know if this is necessary
    examples.rename(columns={"Sentence": "Primary_Text"}, inplace=True)
    examples["Language_ID"] = "yab"
    examples["Source"] = examples["Source"].str.split("; ")
    example_add = cread("etc/example_additions.csv")  # additional example data
    examples = examples.merge(example_add, on="ID", how="left")
    examples = examples.fillna("")
    for combine_col in [
        "Tags",
        "Comment",
    ]:  # these can come from either source, so we combine them
        examples[combine_col] = examples.apply(
            lambda x: " ".join([x[f"{combine_col}_y"], x[f"{combine_col}_x"]]).strip(),
            axis=1,
        )
    examples["ID"] = examples.apply(get_id, axis=1)
    examples = examples[~(examples["Text_ID"].isin(bad_texts))]

    # not all examples have english translations
    # those that don't will get the spanish translation
    # as the main one
    def sort_translations(row):
        if row["Translation_en"] != "":
            row["Original_Translation"] = row["Translated_Text"]
            row["Translated_Text"] = row["Translation_en"]
        else:
            row["Original_Translation"] = ""
        return row

    examples = examples.apply(lambda x: sort_translations(x), axis=1)

    texts = {}
    good_texts = open("raw/good_texts.txt", "r", encoding="utf8").read().split("\n")
    for f in Path("../yawarana_corpus/text_notes/").glob("*.yaml"):
        with open(f) as file:
            text_data = yaml.load(file, Loader=yaml.SafeLoader)
            text_id = text_data.pop("id")
            if release:
                if text_id in good_texts:
                    texts[text_id] = text_data
            else:
                texts[text_id] = text_data

    if release:
        bare_examples = pd.DataFrame()
    else:
        bare_examples = cread("../yawarana_corpus/flexports/yab_texts.csv")
        bare_examples = bare_examples[(bare_examples["Text_ID"]).isin(texts.keys())]
        bare_examples["ID"] = bare_examples.apply(get_id, axis=1)
        bare_examples = bare_examples.merge(example_add, on="ID", how="left")
        bare_examples["Translated_Text"] = bare_examples.apply(
            lambda x: x["Translation_en"]
            if not (pd.isnull(x["Translation_en"]) or x["Translation_en"] == "")
            else x["Translated_Text"],
            axis=1,
        )
        bare_examples = bare_examples.fillna("")
        bare_examples["Tags"] = bare_examples.apply(
            lambda x: x["Tags_y"] + " " + x["Tags_x"], axis=1
        )
        bare_examples = bare_examples[~(bare_examples["ID"].isin(examples["ID"]))]
        bare_examples["Primary_Text"] = bare_examples["Sentence"].apply(
            lambda x: ortho_strip(x, additions=["%", "¿", "###", "#"])
        )
        bare_examples.drop(columns=["Segmentation", "Gloss"], inplace=True)

    log.info("Morphemes and lexemes")
    # keys: morpheme IDs
    # values: different (allo)morph forms and associated morph IDs
    # used for converting uniparser's morpheme IDs into morph IDs
    id_dict = {}

    flexemes = cread("../yawarana_corpus/flexports/flexports.csv")
    flexemes = flexemes[~(flexemes["Form"].str.contains("-"))]
    flexemes = flexemes[~(flexemes["Form"].str.contains("="))]
    flexemes.rename(columns={"Gloss_en": "Gloss"}, inplace=True)
    flexemes["Language_ID"] = "yab"
    include = open("raw/include_flex.txt", "r").read().split("\n")
    include = [x.split(" #")[0] for x in include]
    flexemes = flexemes[(flexemes["ID"].isin(include))]

    manual_lexemes = cread("raw/lexemes.csv")
    generate_if_empty(manual_lexemes, "ID", lambda x: generate_id(x))
    manual_lexemes = manual_lexemes.apply(add_gloss, axis=1)

    etym_lexemes = cread("raw/etym_lexemes.csv")
    etym_lexemes["Language_ID"] = "yab"
    etym_lexemes["Name"] = etym_lexemes["Form"].apply(lambda x: x.split("; ")[0])
    etym_lexemes["ID"] = ""
    etym_lexemes["Comment"] = etym_lexemes["Comment"].apply(
        lambda x: (
            x + " " + "Etymological lexeme, only attested in derived lexemes."
        ).strip()
    )
    generate_if_empty(etym_lexemes, "ID", lambda x: generate_id(x))
    etym_lexemes = etym_lexemes.apply(add_gloss, axis=1)
    etym_lexemes["Description"] = etym_lexemes["Translation"]

    roots = cread("raw/dictionary_roots.csv")
    manual_lexemes = pd.concat([manual_lexemes, roots])
    infl_morphs = cread("etc/inflection_morphs.csv")
    infl_morphemes = cread("etc/inflection_morphemes.csv")
    deriv_morphs = cread("etc/derivation_morphs.csv")
    deriv_morphemes = cread("etc/derivation_morphemes.csv")
    misc_morphs = cread("etc/misc_morphs.csv")
    misc_morphemes = cread("etc/misc_morphemes.csv")
    for cdf in [
        infl_morphemes,
        infl_morphs,
        deriv_morphs,
        deriv_morphemes,
        misc_morphs,
        misc_morphemes,
    ]:
        cdf["Language_ID"] = "yab"
    for cdf in [infl_morphemes, deriv_morphemes, misc_morphemes]:
        cdf.rename(columns={"Gloss": "Parameter_ID"}, inplace=True)
    for a, b in [
        (infl_morphemes, infl_morphs),
        (deriv_morphemes, deriv_morphs),
        (misc_morphemes, misc_morphs),
    ]:
        morph_meanings = dict(zip(a["ID"], a["Parameter_ID"]))
        b["Parameter_ID"] = b["Morpheme_ID"].map(morph_meanings)

    log.info("Sources")
    found_refs = jsonlib.load("etc/refs.json")
    bib = pybtex.database.parse_file("etc/car.bib", bib_format="bibtex")
    sources = [
        Source.from_entry(k, e) for k, e in bib.entries.items() if k in found_refs
    ]
    writer.cldf.add_sources(*sources)

    log.info("POS")
    for p in pos.to_dict("records"):
        writer.objects["POSTable"].append(p)

    log.info("Morphemes")

    # the distinct meanings
    meanings = {"unknown": "***"}

    all_morphemes = pd.concat([infl_morphemes, deriv_morphemes, misc_morphemes])
    all_morphemes.set_index("ID", inplace=True, drop=False)
    all_morphemes["Comment"] = all_morphemes["Comment"].apply(
        lambda x: "".join(preprocess_cldfviz(x))
    )
    for morpheme_id, mp in all_morphemes.iterrows():
        mp["ID"] = morpheme_id
        if morpheme_id in id_dict:
            log.error(morpheme_id)
            raise ValueError
        id_dict[morpheme_id] = {}
        for g in mp["Parameter_ID"].split("; "):
            if slugify(g) not in meanings:
                meanings[slugify(g)] = g
        mp["Parameter_ID"] = [slugify(y) for y in mp["Parameter_ID"].split("; ")]
        writer.objects["MorphsetTable"].append(mp)

    for morph in pd.concat([infl_morphs, deriv_morphs, misc_morphs]).to_dict(
        orient="records"
    ):
        morpheme_id = morph["Morpheme_ID"]
        if pd.isnull(morph["Parameter_ID"]):
            log.error("Empty meaning for morph")
            log.error(morph)
            sys.exit(1)
        for g in morph["Parameter_ID"].split("; "):
            id_dict[morpheme_id][morph["Form"].strip("-") + ":" + g] = morph["ID"]
            if slugify(g) not in meanings:
                meanings[slugify(g)] = g
        morph["Parameter_ID"] = [slugify(y) for y in morph["Parameter_ID"].split("; ")]
        morph["Name"] = morph["Form"]
        writer.objects["MorphTable"].append(morph)

    for i, lexeme in enumerate(manual_lexemes.to_dict(orient="records")):
        morpheme_id = lexeme["ID"]
        if morpheme_id in id_dict:
            log.error(f"{morpheme_id} is already in id_dict")
            raise ValueError
        id_dict[morpheme_id] = {}
        forms = lexeme["Form"].split("; ")
        lexeme["Parameter_ID"] = [slugify(y) for y in lexeme["Gloss"].split("; ")]
        for j, form in enumerate(forms):
            morph_id = f"{morpheme_id}-{j}"
            for g in lexeme["Gloss"].split("; "):
                id_dict[morpheme_id][form + ":" + g.replace(" ", ".")] = morph_id
                if slugify(g) not in meanings:
                    meanings[slugify(g)] = g
            writer.objects["MorphTable"].append(
                {
                    "ID": morph_id,
                    "Name": form,
                    "Morpheme_ID": morpheme_id,
                    "Parameter_ID": lexeme["Parameter_ID"],
                    "Language_ID": "yab",
                }
            )

            # id_dict[morpheme_id][form + ":" + lexeme["Gloss_en"]] = morph_id
        writer.objects["MorphsetTable"].append(
            {
                "ID": morpheme_id,
                "Name": forms[0],
                "Parameter_ID": lexeme["Parameter_ID"],
                "Language_ID": "yab",
            }
        )

    for flexeme in flexemes.to_dict(orient="records"):
        if flexeme["Gloss"] == "":
            continue
        forms = flexeme["Form"].split("; ")
        forms = sorted(forms, key=lambda x: len(x), reverse=True)
        morpheme_id = flexeme["ID"]
        if morpheme_id in id_dict:
            log.error(morpheme_id)
            raise ValueError
        id_dict[morpheme_id] = {}
        flexeme["Parameter_ID"] = [slugify(y) for y in flexeme["Gloss"].split("; ")]
        for i, form in enumerate(forms):
            morph_id = f"{morpheme_id}{i}"
            for g in flexeme["Gloss"].split("; "):
                if slugify(g) not in meanings:
                    meanings[slugify(g)] = g
                id_dict[morpheme_id][form + ":" + g] = morph_id
            writer.objects["MorphTable"].append(
                {
                    "ID": morph_id,
                    "Name": form,
                    "Morpheme_ID": morpheme_id,
                    "Parameter_ID": flexeme["Parameter_ID"],
                    "Language_ID": flexeme["Language_ID"],
                }
            )

        writer.objects["MorphsetTable"].append(
            {
                "ID": morpheme_id,
                "Name": forms[0],
                "Parameter_ID": flexeme["Parameter_ID"],
                "Language_ID": flexeme["Language_ID"],
            }
        )

    log.info("Text")

    for text_id, text_data in texts.items():
        metadata = {x: text_data[x] for x in ["genre", "tags"] if x in text_data}
        writer.objects["TextTable"].append(
            {
                "ID": text_id,
                "Title": text_data["title_es"],
                "Description": text_data["summary"],
                "Comment": "; ".join(text_data.get("comments", [])),
                "Type": text_data["genre"],
                "Metadata": metadata,
            }
        )

    log.info("Lexemes")
    all_lexemes = pd.concat([manual_lexemes, flexemes])
    all_lexemes["Language_ID"] = "yab"
    all_lexemes["Form"] = all_lexemes["Form"].apply(lambda x: x.split("; "))
    all_lexemes["Name"] = all_lexemes["Form"].apply(lambda x: x[0])
    all_lexemes["Description"] = all_lexemes["Gloss"].apply(
        lambda x: x.split("; ")[0].replace(".", " ")
    )
    all_lexemes.set_index("ID", inplace=True, drop=False)
    derivations = cread("raw/derivations.csv")
    derivations["Language_ID"] = "yab"
    derivations["Description"] = derivations["Translation"]
    derivations["Name"] = derivations["Form"].apply(lambda x: x.replace("-", "+"))
    derivations["Form"] = derivations["Form"].apply(
        lambda x: x.replace("-", "").split("; ")
    )
    derivations.set_index("ID", inplace=True, drop=False)

    for lex in derivations.to_dict("records"):
        writer.objects["LexemeTable"].append(lex)

    for lex in all_lexemes.to_dict("records"):
        writer.objects["LexemeTable"].append(lex)

    log.info("Wordforms")
    # different form-meaning pairs, to avoid sorting IDs every time (slow)
    form_meanings = {}
    # the actual word forms, which can have different meanings
    forms = {}
    # lexemes occurring in the corpus
    corpus_lexemes = {}

    dangerous_glosses = ["all"]
    # these are some wordforms collected for the dictionary, parsed with uniparser
    dic_wordforms = cread("raw/parsed_forms.csv")
    for wf in dic_wordforms.to_dict("records"):
        # there are unparsed wordforms in here
        if wf["Gloss"] == "":
            if wf["Parameter_ID"] not in meanings:
                meanings[wf["Parameter_ID"]] = wf["Translation"]
            wf["Parameter_ID"] = [wf["Parameter_ID"]]
            forms[wf["ID"]] = wf
        else:
            form_slug = slugify(wf["Segmented"] + ":" + wf["Gloss"])
            if wf["Gloss"] in dangerous_glosses:
                meaning_slug = slugify(wf["Gloss"]) + "-1"
            else:
                meaning_slug = slugify(wf["Gloss"])
            if meaning_slug not in meanings:
                meanings[meaning_slug] = wf["Translation"]
            if form_slug not in form_meanings:
                morpheme_ids = sort_uniparser_ids(
                    id_list=wf["Morpheme_IDs"].split(","),
                    obj=wf["Segmented"],
                    gloss=wf["Gloss"],
                    id_dic=id_dict,
                    mode="morphemes",
                )
                morph_ids = sort_uniparser_ids(
                    id_list=wf["Morpheme_IDs"].split(","),
                    obj=wf["Segmented"],
                    gloss=wf["Gloss"],
                    id_dic=id_dict,
                )
                if None in morph_ids:
                    slug = wf["ID"]
                else:
                    slug = slugify("-".join(morph_ids))
                form_meanings[form_slug] = slug
                if slug not in forms:
                    forms[slug] = {
                        "Form": wf["Segmented"],
                        "Parameter_ID": [meaning_slug],
                        "POS": get_pos(wf["Gramm"], pos_list=pos_list),
                        "Source": wf["Source"],
                        "Translation": wf["Translation"],
                    }
                    writer.objects["InflectionTable"].append(
                        {
                            "ID": slug,
                            "Form_ID": slug,
                            "Lexeme_ID": slugify(wf["Lexeme_ID"]),
                        }
                    )
                    corpus_lexemes.setdefault(
                        slugify(wf["Lexeme_ID"]),
                        {"name": wf["Lexeme_ID"], "gloss": wf["Gloss"]},
                    )
                elif wf["Gloss"] not in forms[slug]["Parameter_ID"]:
                    forms[slug]["Parameter_ID"].append(meaning_slug)
                igt = pyigt.IGT(wf["Segmented"], wf["Gloss"])
                for morpheme_ids, word in zip(
                    wf["Morpheme_IDs"], igt.morphosyntactic_words
                ):
                    for morph_count, (morph_id, glossed_morph) in enumerate(
                        zip(morph_ids, word.glossed_morphemes)
                    ):
                        if morph_id:
                            writer.objects["FormSlices"].append(
                                {
                                    "ID": f"{form_slug}-{morph_count}",
                                    "Form_ID": slug,
                                    "Morph_ID": morph_id,
                                    "Index": str(morph_count),
                                    "Morpheme_Meaning": slugify(glossed_morph.gloss),
                                    "Form_Meaning": meaning_slug,
                                }
                            )
            else:
                slug = form_meanings[form_slug]
    # print(dic_wordforms)

    log.info("Examples")

    for ex in examples.to_dict("records"):
        if ex["Analyzed_Word"] == "":
            continue
        ex["Tags"] = ex["Tags"].split(" ")
        audio_path = audio_path / f'{ex["ID"]}.wav'
        if audio_path.is_file():
            writer.objects["MediaTable"].append({"ID": ex["ID"], "Media_Type": "wav"})
        ex["Analyzed_Word"] = ex["Analyzed_Word"].split(" ")
        ex["Gloss"] = ex["Gloss"].split(" ")
        ex["Morpheme_IDs"] = ex["Morpheme_IDs"].split(" ")
        if ex["Primary_Text"] == "***":
            continue
        if ex["Primary_Text"] == "###":
            continue
        igt = pyigt.IGT(ex["Analyzed_Word"], ex["Gloss"])
        if len(ex["Morpheme_IDs"]) != len(igt.morphosyntactic_words):
            for wc, word in enumerate(ex["Analyzed_Word"]):
                if "=" in word:
                    ex["Morpheme_IDs"].insert(wc, ex["Morpheme_IDs"][wc])
        word_count = -1
        for morpheme_ids, word, gramm, lexeme in zip(
            ex["Morpheme_IDs"],
            igt.morphosyntactic_words,
            ex["Gramm"].split(" "),
            ex["Lemmata"].split(" "),
        ):
            word_count += 1
            form_slug = slugify(word.word + ":" + word.gloss)
            if word.gloss in dangerous_glosses:
                meaning_slug = slugify(word.gloss) + "-1"
            else:
                meaning_slug = slugify(word.gloss)
            if meaning_slug not in meanings:
                meanings[meaning_slug] = word.gloss
            if form_slug not in form_meanings:
                if "***" in morpheme_ids:
                    slug = slugify(word.word)
                    if slug not in forms:
                        forms[slug] = {"Form": word.word, "Parameter_ID": ["unknown"]}
                    writer.objects["ExampleSlices"].append(
                        {
                            "ID": ex["ID"] + "-" + str(word_count),
                            "Form_ID": slug,
                            "Example_ID": ex["ID"],
                            "Slice": str(word_count),
                            "Parameter_ID": "unknown",
                        }
                    )
                    continue
                if morpheme_ids == "":
                    continue
                ids_for_slug = sort_uniparser_ids(
                    id_list=morpheme_ids.split(","),
                    obj=word.word,
                    gloss=word.gloss,
                    id_dic=id_dict,
                    mode="morphemes",
                )
                morph_ids = sort_uniparser_ids(
                    id_list=morpheme_ids.split(","),
                    obj=word.word,
                    gloss=word.gloss,
                    id_dic=id_dict,
                )
                if None in morph_ids:
                    msg = f"Unidentified morphs in {ex['ID']} {word.word} '{word.gloss}': {morpheme_ids} > {morph_ids}, using {lexeme} for ID"
                    log.error(msg)
                    slug = slugify("-".join([x if x else lexeme for x in morph_ids]))
                else:
                    slug = slugify("-".join(morph_ids))
                form_meanings[form_slug] = slug
                if " " in gramm:
                    print(ex["Gramm"], "eeek", gramm)
                if slug not in forms:
                    forms[slug] = {
                        "Form": word.word,
                        "Parameter_ID": [meaning_slug],
                        "POS": get_pos(gramm, pos_list=pos_list),
                        "Translation": word.gloss,
                    }
                    if lexeme in ["***", "?"]:
                        continue
                    corpus_lexemes.setdefault(
                        slugify(lexeme), {"name": lexeme, "gloss": word.gloss}
                    )
                    if "slug" in slugify(lexeme):
                        print(
                            slug,
                            "word: ",
                            word.word,
                            "parameter:",
                            meaning_slug,
                            "gramm:",
                            gramm,
                            "lexeme:",
                            lexeme,
                        )
                    writer.objects["InflectionTable"].append(
                        {
                            "ID": f"{form_slug}-{slugify(lexeme)}",
                            "Form_ID": slug,
                            "Lexeme_ID": slugify(lexeme),
                        }
                    )
                elif word.gloss not in forms[slug]["Parameter_ID"]:
                    forms[slug]["Parameter_ID"].append(meaning_slug)
                for morph_count, (morph_id, glossed_morph) in enumerate(
                    zip(morph_ids, word.glossed_morphemes)
                ):
                    if morph_id:
                        writer.objects["FormSlices"].append(
                            {
                                "ID": f"{form_slug}-{morph_count}",
                                "Form_ID": slug,
                                "Morph_ID": morph_id,
                                "Index": str(morph_count),
                                "Morpheme_Meaning": slugify(glossed_morph.gloss),
                                "Form_Meaning": meaning_slug,
                            }
                        )
            else:
                slug = form_meanings[form_slug]

            writer.objects["ExampleSlices"].append(
                {
                    "ID": ex["ID"] + "-" + str(word_count),
                    "Form_ID": slug,
                    "Example_ID": ex["ID"],
                    "Slice": str(word_count),
                    "Parameter_ID": meaning_slug,
                }
            )
        writer.objects["ExampleTable"].append(ex)

    all_lexemes = pd.concat([all_lexemes, derivations])
    all_morphemes["Gloss"] = all_morphemes["Parameter_ID"].apply(
        lambda x: meanings[slugify(x[0])]
    )
    for deriv in derivations.to_dict("records"):
        writer.objects["LexemeLexemeParts"].append(
            {
                "ID": f"{deriv['ID']}-base",
                "Lexeme_ID": deriv["ID"],
                "Base_ID": deriv["Base_Lexeme"],
            }
        )
        writer.objects["LexemeMorphemeParts"].append(
            {
                "ID": f"{deriv['ID']}-affix",
                "Lexeme_ID": deriv["ID"],
                "Morpheme_ID": deriv["Affix_ID"],
            }
        )

    # some lexemes are created on the fly by uniparser
    generated_lexemes = {}
    for key, data in corpus_lexemes.items():
        name = data["name"]
        if key in all_lexemes.index:  # monomorphemic lexemes (like 'wenaka-vomit')
            pass
        elif (
            name in derivations.index
        ):  # manually defined derivations (like 'dt1+wenaka-vomit')
            pass
        else:
            log.debug(f"Processing lexeme {key}: {name}")
            constituents = []
            for constituent in name.split("+"):
                if constituent in all_lexemes.index:
                    constituents.append(
                        {**dict(all_lexemes.loc[constituent]), **{"type": "lexeme"}}
                    )
                    pass
                else:
                    candidate_lexemes = all_lexemes[
                        all_lexemes["Form"].apply(lambda x: constituent in x)
                    ]
                    if len(candidate_lexemes) == 1:
                        constituents.append(
                            {**dict(candidate_lexemes.iloc[0]), **{"type": "lexeme"}}
                        )
                    elif len(candidate_lexemes) > 1:
                        identified = False
                        for g in data["gloss"].split("-"):
                            narrow_cands = candidate_lexemes[
                                candidate_lexemes["Gloss"].str.contains(g)
                            ]
                            if len(narrow_cands) == 1:
                                constituents.append(
                                    {**dict(narrow_cands.iloc[0]), **{"type": "lexeme"}}
                                )
                                identified = True
                        if not identified:
                            log.warning(f"Ambiguity alert for lexeme {key}: {name}")
                            print(data)
                            print(candidate_lexemes)
                    else:
                        if slugify(constituent) in all_morphemes.index:
                            constituents.append(
                                {
                                    **dict(all_morphemes.loc[slugify(constituent)]),
                                    **{"type": "morpheme"},
                                }
                            )
                            pass
                        else:
                            log.warning(constituent)
                            print(data)
            for c_count, constituent in enumerate(constituents):
                if constituent["type"] == "lexeme":
                    writer.objects["LexemeLexemeParts"].append(
                        {
                            "ID": f"{key}-{c_count}",
                            "Lexeme_ID": key,
                            "Base_ID": constituent["ID"],
                        }
                    )
                elif constituent["type"] == "morpheme":
                    writer.objects["LexemeMorphemeParts"].append(
                        {
                            "ID": f"{key}-{c_count}",
                            "Lexeme_ID": key,
                            "Morpheme_ID": constituent["ID"],
                        }
                    )
            lexeme_name = "+".join([x["Name"] for x in constituents]).replace("-", "")
            # print(constituents)
            lexeme_description = "-".join([x["Gloss"] for x in constituents])
            if key in generated_lexemes:
                log.warning(f"Lexeme ID {key} has already been generated.")
            generated_lexemes[key] = {
                "ID": key,
                "Name": lexeme_name,
                "Description": lexeme_description,
                "Language_ID": "yab",
            }

    for lex in generated_lexemes.values():
        writer.objects["LexemeTable"].append(lex)

    for lex in etym_lexemes.to_dict("records"):
        writer.objects["LexemeTable"].append(lex)
    log.info("Audio")

    for ex in bare_examples.to_dict("records"):
        ex["Tags"] = ex["Tags"].split(" ")
        file_path = audio_path / f'{ex["ID"]}.wav'
        if file_path.is_file():
            writer.objects["MediaTable"].append({"ID": ex["ID"], "Media_Type": "wav"})
        if ex["Primary_Text"] == "":
            continue
        writer.objects["ExampleTable"].append(ex)

    log.info("Phonemes")

    phonemes = cread("etc/phonemes.csv")
    done_phonemes = []
    for phoneme in phonemes.to_dict(orient="records"):
        if phoneme["IPA"] not in done_phonemes:
            done_phonemes.append(phoneme["IPA"])
            writer.objects["PhonemeTable"].append(
                {"ID": phoneme["ID"], "Name": phoneme["IPA"]}
            )

    log.info("Meanings")

    for meaning_id, meaning in meanings.items():
        writer.objects["ParameterTable"].append({"ID": meaning_id, "Name": meaning})

    log.info("Forms")
    for form_id, form in forms.items():
        if "Source" in form:
            form["Source"] = [form["Source"]]
        form["ID"] = form_id
        form["POS"] = form.get("POS", "")
        form["Segments"] = segmentizer.parse_string(form["Form"]).split(" ")
        form["Language_ID"] = "yab"
        writer.objects["FormTable"].append(form)
        form_slug = slugify(form["Form"].replace("-", "").replace("∅", ""))
        if form_slug in word_audios:
            writer.objects["MediaTable"].append(
                {
                    "ID": form_id,
                    "Media_Type": "wav",
                    "Name": word_audios.pop(form_slug)[0].stem,
                }
            )

    writer.objects["LanguageTable"].append(
        {
            "ID": "yab",
            "Name": "Yawarana",
            "Longitude": -54.7457,
            "Latitude": 1.49792,
            "Glottocode": "yaba1248",
        }
    )
    writer.write()

# for k in word_audios.keys():
#     print(k)
