import pandas as pd
from cldfbench.cldf import CLDFWriter
from cldfbench import CLDFSpec
from clldutils.loglib import get_colorlog
from pathlib import Path
import logging
import sys
from clldutils import jsonlib
import pybtex
from pycldf.sources import Source
from pylingdocs.models import Morpheme, Morph, Text
from pylingdocs.cldf import metadata as cldf_md
from clld_morphology_plugin.cldf import MorphTable, MorphsetTable, FormSlices
from pylacoan.helpers import ortho_strip


from slugify import slugify as sslug
import pyigt
from pylacoan.helpers import sort_uniparser_ids
from pylacoan.annotator import Segmentizer
import yaml
import pycldf
import json

bare_slugs = 0
zero_slugged = {}


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


def custom_spec(component, column, separator):
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


log = get_colorlog(__name__, sys.stdout, level=logging.INFO)
example_audios = Path(
    "/home/florianm/Dropbox/research/cariban/yawarana/yawarana_corpus/audio"
)


def cread(filename):
    df = pd.read_csv(filename, keep_default_na=False)
    return df


spec = CLDFSpec(dir="cldf", module="Generic", metadata_fname="metadata.json")

segmentizer = Segmentizer(
    segments=cread("etc/phonemes.csv").to_dict(orient="records"), delete=["-", "∅"]
)

word_audios = {}
for filename in Path("/home/florianm/Downloads/New_Dictionary_Clippings").iterdir():
    leggo = filename.stem.split("_")[3].split("-")[0]
    word_audios.setdefault(leggo, [])
    word_audios[leggo].append(filename)

with CLDFWriter(spec) as writer:
    writer.cldf.properties.setdefault("rdf:ID", "yawarana-dataset")
    writer.cldf.properties.setdefault("dc:title", "A descriptive dataset of Yawarana")
    writer.cldf.properties.setdefault("dc:bibliographicCitation", "Matter, Florian, 2022. A digital grammar sketch of Yawarana")
    writer.cldf.properties.setdefault(
        "dc:description",
        "This data is primarily intended for a digital sketch grammar of Yawarana.",
    )

    log.info("Adding components")
    # set up components
    writer.cldf.add_component("ExampleTable")
    # examples can refer to texts
    writer.cldf.add_columns(
        "ExampleTable",
        {
            "name": "Text_ID",
            "dc:extent": "singlevalued",
            "dc:description": "The text to which this record belongs",
            "datatype": "string",
        },
{
                "name": "Source",
                "required": False,
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#source",
                "datatype": {
                    "base": "string"
                },
                "separator": ";"
            }
    )
    writer.cldf.add_component("FormTable")
    writer.cldf.add_component("ParameterTable")
    writer.cldf.add_component("MediaTable")
    writer.cldf.add_component("LanguageTable")
    writer.cldf.add_component(FormSlices)
    writer.cldf.add_component(cldf_md("ExampleSlices"))
    writer.cldf.remove_columns("FormTable", "Parameter_ID")
    writer.cldf.add_columns(
        "FormTable", custom_spec("FormTable", "Parameter_ID", separator="; ")
    )

    # custom metadata from pylingdocs models
    writer.cldf.add_component(MorphTable)
    writer.cldf.add_component(MorphsetTable)
    writer.cldf.add_component(jsonlib.load("etc/PhonemeTable-metadata.json"))
    writer.cldf.add_component(Text.cldf_metadata())

    # various foreign keys
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

    log.info("Reading data")

    examples = cread("../yawarana_corpus/yawarana_pylacoan/output/parsed.csv")
    examples["Sentence"] = examples["Sentence"].replace("", "***")
    examples.rename(columns={"Sentence": "Primary_Text"}, inplace=True)
    examples["Language_ID"] = "yab"
    examples["Source"] = examples["Source"].str.split("; ")

    example_add = cread("etc/example_additions.csv")
    examples = examples.merge(example_add, on="ID", how="left")
    examples["Translated_Text"] = examples.apply(
        lambda x: x["Translation_en"]
        if not (pd.isnull(x["Translation_en"]) or x["Translation_en"] == "")
        else x["Translated_Text"],
        axis=1,
    )



    texts = {}
    for f in Path("../yawarana_corpus/text_notes/").glob("*.yaml"):
        with open(f) as file:
            text_data = yaml.load(file, Loader=yaml.SafeLoader)
            texts[text_data.pop("id")] = text_data


    bare_examples = cread("../yawarana_corpus/flexports/yab_texts.csv")
    bare_examples["ID"] = bare_examples["ID"].apply(lambda x: x.replace(".", "-").lower())
    bare_examples = bare_examples[~(bare_examples["ID"].isin(examples["ID"]))]
    bare_examples["Primary_Text"] = bare_examples["Sentence"].apply(lambda x: ortho_strip(x, additions=["%", "¿", "###", "#"]))
    bare_examples.drop(columns=["Segmentation", "Gloss"], inplace=True)
    bare_examples = bare_examples[(bare_examples["Text_ID"]).isin(texts.keys())]

    # keys: morpheme IDs
    # values: different (allo)morph forms and associated morph IDs
    # used for converting uniparser's morpheme IDs into morph IDs
    id_dict = {}

    flexemes = cread("../yawarana_corpus/flexports/flexports.csv")
    flexemes = flexemes[~(flexemes["Form"].str.contains("-"))]
    flexemes = flexemes[~(flexemes["Form"].str.contains("="))]
    flexemes["Language_ID"] = "yab"

    manual_lexemes = cread(
        "/home/florianm/Dropbox/development/uniparser-yawarana/compile_parser/lexicon/lexemes.csv"
    )
    roots = cread(
        "/home/florianm/Dropbox/development/uniparser-yawarana/compile_parser/lexicon/roots.csv"
    )
    manual_lexemes = pd.concat([manual_lexemes, roots])
    infl_morphs = cread("etc/inflection_morphs.csv")
    infl_morphemes = cread("etc/inflection_morphemes.csv")
    deriv_morphs = cread("etc/derivation_morphs.csv")
    deriv_morphemes = cread("etc/derivation_morphemes.csv")
    for cdf in [infl_morphemes, infl_morphs, deriv_morphs, deriv_morphemes]:
        cdf["Language_ID"] = "yab"
    for cdf in [infl_morphemes, deriv_morphemes]:
        cdf.rename(columns={"Gloss": "Parameter_ID"}, inplace=True)
    morph_meanings = dict(zip(infl_morphemes["ID"], infl_morphemes["Parameter_ID"]))
    infl_morphs["Parameter_ID"] = infl_morphs["Morpheme_ID"].map(morph_meanings)
    morph_meanings = dict(zip(deriv_morphemes["ID"], deriv_morphemes["Parameter_ID"]))
    deriv_morphs["Parameter_ID"] = deriv_morphs["Morpheme_ID"].map(morph_meanings)

    log.info("Sources")
    found_refs = jsonlib.load("etc/refs.json")
    bib = pybtex.database.parse_file("etc/car.bib", bib_format="bibtex")
    sources = [
        Source.from_entry(k, e) for k, e in bib.entries.items() if k in found_refs
    ]
    writer.cldf.add_sources(*sources)

    log.info("Writing morphemes")

    # the distinct meanings
    meanings = {}

    for mp in pd.concat([infl_morphemes, deriv_morphemes]).to_dict(orient="records"):
        morpheme_id = mp["ID"]
        if morpheme_id in id_dict:
            log.error(morpheme_id)
            raise ValueError
        id_dict[morpheme_id] = {}
        for g in mp["Parameter_ID"].split("; "):
            if slugify(g) not in meanings:
                meanings[slugify(g)] = g
        mp["Parameter_ID"] = [slugify(y) for y in mp["Parameter_ID"].split("; ")]
        writer.objects["MorphsetTable"].append(mp)

    for morph in pd.concat([infl_morphs, deriv_morphs]).to_dict(orient="records"):
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
        if lexeme["ID"] == "":
            morpheme_id = slugify(f'{lexeme["Form"]}-{lexeme["Gloss_en"]}')
        else:
            morpheme_id = lexeme["ID"]
        if morpheme_id in id_dict:
            log.error(morpheme_id)
            raise ValueError
        id_dict[morpheme_id] = {}
        forms = lexeme["Form"].split("; ")
        lexeme["Parameter_ID"] = [slugify(y) for y in lexeme["Gloss_en"].split("; ")]
        for j, form in enumerate(forms):
            morph_id = f"{morpheme_id}-{j}"
            for g in lexeme["Gloss_en"].split("; "):
                id_dict[morpheme_id][form + ":" + g] = morph_id
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
        if flexeme["Gloss_en"] == "":
            continue
        forms = flexeme["Form"].split("; ")
        forms = sorted(forms, key=lambda x: len(x), reverse=True)
        morpheme_id = flexeme["ID"]
        if morpheme_id in id_dict:
            log.error(morpheme_id)
            raise ValueError
        id_dict[morpheme_id] = {}
        flexeme["Parameter_ID"] = [slugify(y) for y in flexeme["Gloss_en"].split("; ")]
        for i, form in enumerate(forms):
            morph_id = f"{morpheme_id}{i}"
            for g in flexeme["Gloss_en"].split("; "):
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

    for text_id, text_data in texts.items():
        metadata = {x: text_data[x] for x in ["genre", "tags"] if x in text_data}
        writer.objects["TextTable"].append(
            {
                "ID": text_id,
                "Title": text_data["title_es"],
                "Description": text_data["summary"],
                "Comment": "; ".join(text_data["comments"]),
                "Type": text_data["genre"],
                "Metadata": metadata,
            }
        )

    # print(id_dict)
    # store all word forms in the corpus
    # word forms are treated as identical based on their morphological makeup
    # i.e., one form can have different meanings, depending on the context


    # different form-meaning pairs, to avoid sorting IDs every time (slow)
    form_meanings = {}
    # the actual word forms, which can have different meanings
    forms = {}



    # these are some wordforms collected for the dictionary, parsed with uniparser
    dic_wordforms  = cread(
        "/home/florianm/Dropbox/development/uniparser-yawarana/var/parsed_forms.csv"
    )
    for wf in dic_wordforms.to_dict("records"):
        form_slug = slugify(wf["Segmented"] + ":" + wf["Gloss"])
        meaning_slug = slugify(wf["Gloss"])
        if meaning_slug not in meanings:
            meanings[meaning_slug] = wf["Translation"]
        if form_slug not in form_meanings:
            morph_ids = sort_uniparser_ids(
                id_list=wf["Morpheme_IDs"].split(","),
                obj=wf["Segmented"],
                gloss=wf["Gloss"],
                id_dic=id_dict,
            )
            if None in morph_ids:
                msg = f"Unidentified morphs in {wf['ID']}!"
                log.error(msg)
                continue
            slug = slugify("-".join(morph_ids))
            form_meanings[form_slug] = slug
            if slug not in forms:
                forms[slug] = {"Form": wf["Segmented"], "Parameter_ID": [meaning_slug]}
            elif wf["Gloss"] not in forms[slug]["Parameter_ID"]:
                forms[slug]["Parameter_ID"].append(meaning_slug)
            igt = pyigt.IGT(wf["Segmented"], wf["Gloss"])
            for morpheme_ids, word in zip(wf["Morpheme_IDs"], igt.morphosyntactic_words):
                for morph_count, (morph_id, glossed_morph) in enumerate(
                    zip(morph_ids, word.glossed_morphemes)
                ):
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


    for ex in examples.to_dict("records"):
        audio_path = example_audios / f'{ex["ID"]}.wav'
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
        for morpheme_ids, word in zip(ex["Morpheme_IDs"], igt.morphosyntactic_words):
            word_count += 1
            form_slug = slugify(word.word + ":" + word.gloss)
            meaning_slug = slugify(word.gloss)
            if meaning_slug not in meanings:
                meanings[meaning_slug] = word.gloss
            if form_slug not in form_meanings:
                if "***" in morpheme_ids:
                    continue
                if morpheme_ids == "":
                    continue
                morph_ids = sort_uniparser_ids(
                    id_list=morpheme_ids.split(","),
                    obj=word.word,
                    gloss=word.gloss,
                    id_dic=id_dict,
                )
                if None in morph_ids:
                    msg = f"Unidentified morphs in {ex['ID']} {word.word} '{word.gloss}': {morpheme_ids} > {morph_ids}"
                    log.error(msg)
                    continue
                slug = slugify("-".join(morph_ids))
                form_meanings[form_slug] = slug
                if slug not in forms:
                    forms[slug] = {"Form": word.word, "Parameter_ID": [meaning_slug]}
                elif word.gloss not in forms[slug]["Parameter_ID"]:
                    forms[slug]["Parameter_ID"].append(meaning_slug)
                for morph_count, (morph_id, glossed_morph) in enumerate(
                    zip(morph_ids, word.glossed_morphemes)
                ):
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

    for ex in bare_examples.to_dict("records"):
        audio_path = example_audios / f'{ex["ID"]}.wav'
        if audio_path.is_file():
            writer.objects["MediaTable"].append({"ID": ex["ID"], "Media_Type": "wav"})
        writer.objects["ExampleTable"].append(ex)

    phonemes = cread("etc/phonemes.csv")
    done_phonemes = []
    for phoneme in phonemes.to_dict(orient="records"):
        if phoneme["IPA"] not in done_phonemes:
            done_phonemes.append(phoneme["IPA"])
            writer.objects["PhonemeTable"].append({"ID": phoneme["ID"], "Name": phoneme["IPA"]})

    for meaning_id, meaning in meanings.items():
        writer.objects["ParameterTable"].append({"ID": meaning_id, "Name": meaning})

    for form_id, form in forms.items():
        writer.objects["FormTable"].append(
            {
                "ID": form_id,
                "Language_ID": "yab",
                "Parameter_ID": form["Parameter_ID"],
                "Form": form["Form"],
                "Segments": segmentizer.parse_string(form["Form"]).split(" "),
            }
        )
        form_slug = slugify(form["Form"].replace("-", "").replace("∅", ""))
        if form_slug in word_audios:
            writer.objects["MediaTable"].append(
                {
                    "ID": form_id,
                    "Media_Type": "wav",
                    "Name": word_audios[form_slug][0].stem,
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
