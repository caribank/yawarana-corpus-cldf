import pandas as pd
from cldfbench.cldf import CLDFWriter
from cldfbench import CLDFSpec
from clldutils.loglib import get_colorlog
import logging
import sys
from clldutils import jsonlib
import pybtex
from pycldf.sources import Source
from pylingdocs.models import Morpheme, Morph
from pylingdocs.cldf import metadata as cldf_md
from slugify import slugify
import pyigt
from pylacoan.helpers import sort_uniparser_ids

log = get_colorlog(__name__, sys.stdout, level=logging.INFO)


def cread(filename):
    df = pd.read_csv(filename, keep_default_na=False)
    return df


spec = CLDFSpec(dir="cldf", module="Generic", metadata_fname="metadata.json")


examples = cread("../yawarana_corpus/yawarana_pylacoan/output/parsed.csv")
examples["Sentence"] = examples["Sentence"].replace("", "***")
examples.rename(columns={"Sentence": "Primary_Text"}, inplace=True)
examples["Language_ID"] = "yab"


log.info("Writing CLDF data")
with CLDFWriter(spec) as writer:
    writer.cldf.properties.setdefault("rdf:ID", "yaw_gram")
    writer.cldf.properties.setdefault(
        "dc:title", "Data for a digital sketch grammar of Yawarana"
    )
    writer.cldf.properties.setdefault(
        "dc:description", "Data for a digital sketch grammar of Yawarana"
    )
    writer.cldf.add_component("ExampleTable")
    writer.cldf.add_component("FormTable")
    writer.cldf.add_component("LanguageTable")
    writer.cldf.add_component(cldf_md("FormSlices"))
    writer.cldf.add_component(cldf_md("ExampleSlices"))

    writer.cldf.add_component(Morph.cldf_metadata())

    writer.cldf.add_component(Morpheme.cldf_metadata())

    writer.cldf.add_foreign_key(
        "MorphTable", "Morpheme_ID", "MorphsetTable", "ID"
    )
    writer.cldf.add_foreign_key(
        "FormSlices", "Form_ID", "FormTable", "ID"
    )
    writer.cldf.add_foreign_key(
        "FormSlices", "Morph_ID", "MorphTable", "ID"
    )
    writer.cldf.add_foreign_key(
        "ExampleSlices", "Form_ID", "FormTable", "ID"
    )
    writer.cldf.add_foreign_key(
        "ExampleSlices", "Example_ID", "ExampleTable", "ID"
    )

    # keys: morpheme IDs
    # values: different (allo)morph forms and associated morph IDs
    id_dict = {}

    flexemes = cread("../yawarana_corpus/flexports/flexports.csv")
    flexemes = flexemes[~(flexemes["Form"].str.contains("-"))]
    flexemes = flexemes[~(flexemes["Form"].str.contains("="))]
    flexemes["Language_ID"] = "yab"

    manual_lexemes = cread(
        "/home/florianm/Dropbox/development/uniparser-yawarana/compile_parser/lexicon/lexemes.csv"
    )

    infl_morphs = cread(
        "/home/florianm/Dropbox/development/uniparser-yawarana/compile_parser/morphosyntax/inflection.csv"
    )
    infl_morphemes = cread(
        "/home/florianm/Dropbox/development/uniparser-yawarana/compile_parser/morphosyntax/inflection_morphemes.csv"
    )
    deriv_morphs = cread(
        "/home/florianm/Dropbox/development/uniparser-yawarana/compile_parser/morphosyntax/derivation_morphs.csv"
    )
    deriv_morphemes = cread(
        "/home/florianm/Dropbox/development/uniparser-yawarana/compile_parser/morphosyntax/derivation_morphemes.csv"
    )

    for cdf in [infl_morphemes, infl_morphs, deriv_morphs, deriv_morphemes]:
        cdf["Language_ID"] = "yab"
    for cdf in [infl_morphemes, deriv_morphemes]:
        cdf.rename(columns={"Name": "Form", "Gloss": "Parameter_ID"}, inplace=True)
    morph_meanings = dict(zip(infl_morphemes["ID"], infl_morphemes["Parameter_ID"]))
    infl_morphs["Parameter_ID"] = infl_morphs["Morpheme_ID"].map(morph_meanings)
    morph_meanings = dict(zip(deriv_morphemes["ID"], deriv_morphemes["Parameter_ID"]))
    deriv_morphs["Parameter_ID"] = deriv_morphs["Morpheme_ID"].map(morph_meanings)

    found_refs = jsonlib.load("etc/refs.json")
    bib = pybtex.database.parse_file("etc/car.bib", bib_format="bibtex")
    sources = [
        Source.from_entry(k, e) for k, e in bib.entries.items() if k in found_refs
    ]
    writer.cldf.add_sources(*sources)

    autocomplete_data = []

    for morpheme in pd.concat([infl_morphemes, deriv_morphemes]).to_dict(
        orient="records"
    ):
        morpheme_id = morpheme["ID"]
        if morpheme_id in id_dict:
            log.error(morpheme_id)
            raise ValueError
        id_dict[morpheme_id] = {}
        writer.objects["MorphsetTable"].append(morpheme)
        autocomplete_data.append((f"mp:{morpheme['Form']}", f"[mp]({morpheme['ID']})"))

    for morph in pd.concat([infl_morphs, deriv_morphs]).to_dict(orient="records"):
        morpheme_id = morph["Morpheme_ID"]
        for g in morph["Parameter_ID"].split("; "):
            id_dict[morpheme_id][morph["Form"].strip("-") + ":" + g] = morph["ID"]
        writer.objects["MorphTable"].append(morph)
        autocomplete_data.append((f"m:{morph['Form']}", f"[m]({morph['ID']})"))

    for i, lexeme in enumerate(manual_lexemes.to_dict(orient="records")):
        if lexeme["ID"] == "":
            morpheme_id = f"manlex{i}"
        else:
            morpheme_id = lexeme["ID"]
        if morpheme_id in id_dict:
            log.error(morpheme_id)
            raise ValueError
        id_dict[morpheme_id] = {}
        forms = lexeme["Form"].split("; ")
        for j, form in enumerate(forms):
            morph_id = f"{morpheme_id}-{j}"
            writer.objects["MorphTable"].append(
                {
                    "ID": morph_id,
                    "Form": form,
                    "Morpheme_ID": morpheme_id,
                    "Parameter_ID": lexeme["Gloss_en"],
                    "Language_ID": "yab",
                }
            )
            for g in lexeme["Gloss_en"].split("; "):
                id_dict[morpheme_id][form + ":" + g] = morph_id
            # id_dict[morpheme_id][form + ":" + lexeme["Gloss_en"]] = morph_id
            autocomplete_data.append((f"m:{form}", f"[m]({morph_id})"))
        writer.objects["MorphsetTable"].append(
            {
                "ID": morpheme_id,
                "Form": forms[0],
                "Parameter_ID": lexeme["Gloss_en"],
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
        for i, form in enumerate(forms):
            morph_id = f"{morpheme_id}{i}"
            writer.objects["MorphTable"].append(
                {
                    "ID": morph_id,
                    "Form": form,
                    "Morpheme_ID": morpheme_id,
                    "Parameter_ID": flexeme["Gloss_en"],
                    "Language_ID": flexeme["Language_ID"],
                }
            )
            for g in flexeme["Gloss_en"].split("; "):
                id_dict[morpheme_id][form + ":" + g] = morph_id
            autocomplete_data.append((f"m:{form}", f"[m]({morph_id})"))
        writer.objects["MorphsetTable"].append(
            {
                "ID": morpheme_id,
                "Form": forms[0],
                "Parameter_ID": flexeme["Gloss_en"],
                "Language_ID": flexeme["Language_ID"],
            }
        )
        autocomplete_data.append((f"mp:{forms[0]}", f"[mp]({morpheme_id})"))

    # print(id_dict["manlex6"])
    # store all word forms in the corpus
    forms = {}
    form_slices = []
    example_slices = []

    for ex in examples.to_dict("records"):
        ex["ID"] = ex["ID"].replace(".", "-").lower()
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
            slug = slugify(word.word + ":" + word.gloss)
            # if ex["ID"] == "convrisamaj-47":
            #     print(morpheme_ids, word.word, word.gloss)
            if slug not in forms:
                forms[slug] = {"IGT": word}
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
                for morph_count, morph_id in enumerate(morph_ids):
                    writer.objects["FormSlices"].append(
                        {
                            "ID": f"{slug}-{morph_count}",
                            "Form_ID": slug,
                            "Morph_ID": morph_id,
                            "Slice": str(morph_count)
                        }
                    )

            writer.objects["ExampleSlices"].append(
                {
                    "ID": ex["ID"]+"-"+str(word_count),
                    "Form_ID": slug,
                    "Example_ID": ex["ID"],
                    "Slice": str(word_count)
                }
            )
        writer.objects["ExampleTable"].append(ex)
        autocomplete_data.append(
            (
                f"ex:{ex['ID']} {' '.join(ex['Analyzed_Word'])} ‘{ex['Translated_Text']}’",
                f"[ex]({ex['ID']})",
            )
        )

    for form_id, form in forms.items():
        writer.objects["FormTable"].append(
            {
                "ID": form_id,
                "Language_ID": "yab",
                "Parameter_ID": form["IGT"].gloss,
                "Form": form["IGT"].word,
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
    jsonlib.dump(
        autocomplete_data, "../yaw_sketch/content/.autocomplete_data.json", indent=4
    )
