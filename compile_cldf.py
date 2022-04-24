import pandas as pd
from cldfbench.cldf import CLDFWriter
from cldfbench import CLDFSpec
from pathlib import Path
from clldutils.loglib import Logging, get_colorlog
import logging
import sys
from clldutils import jsonlib
from clldutils.misc import slug
import pybtex
from pycldf.sources import Source
from pylingdocs.models import Morpheme, Morph

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
    writer.cldf.add_component("LanguageTable")

    writer.cldf.add_component(Morph.cldf_metadata())

    writer.cldf.add_component(Morpheme.cldf_metadata())


    flexemes = cread("../yawarana_corpus/flexports/flexports.csv")
    flexemes = flexemes[~(flexemes["Form"].str.contains("-"))]
    flexemes = flexemes[~(flexemes["Form"].str.contains("="))]
    flexemes["Language_ID"] = "yab"

    infl_morphs = cread("/home/florianm/Dropbox/development/uniparser-yawarana/compile_parser/morphosyntax/inflection.csv")
    infl_morphs["Language_ID"] = "yab"
    infl_morphemes = cread("/home/florianm/Dropbox/development/uniparser-yawarana/compile_parser/morphosyntax/inflection_morphemes.csv")
    infl_morphemes["Language_ID"] = "yab"
    infl_morphemes.rename(
        columns={"Name": "Form", "Gloss": "Parameter_ID"}, inplace=True
    )
    morph_meanings = dict(zip(infl_morphemes["ID"], infl_morphemes["Parameter_ID"]))
    infl_morphs["Parameter_ID"] = infl_morphs["Morpheme_ID"].map(morph_meanings)

    found_refs = jsonlib.load("etc/refs.json")
    bib = pybtex.database.parse_file("etc/car.bib", bib_format="bibtex")
    sources = [
        Source.from_entry(k, e) for k, e in bib.entries.items() if k in found_refs
    ]
    writer.cldf.add_sources(*sources)

    autocomplete_data = []

    for ex in examples.to_dict("records"):
        ex["ID"] = ex["ID"].replace(".", "-").lower()
        ex["Analyzed_Word"] = ex["Analyzed_Word"].split(" ")
        ex["Gloss"] = ex["Gloss"].split(" ")
        writer.objects["ExampleTable"].append(ex)
        autocomplete_data.append(
            (
                f"ex:{ex['ID']} {' '.join(ex['Analyzed_Word'])} ‘{ex['Translated_Text']}’",
                f"[ex]({ex['ID']})",
            )
        )
    for morph in infl_morphs.to_dict(orient="records"):
        writer.objects["MorphTable"].append(morph)
        autocomplete_data.append((f"m:{morph['Form']}", f"[m]({morph['ID']})"))

    for morpheme in infl_morphemes.to_dict(orient="records"):
        writer.objects["MorphsetTable"].append(morpheme)
        autocomplete_data.append((f"mp:{morpheme['Form']}", f"[mp]({morpheme['ID']})"))

    for flexeme in flexemes.to_dict(orient="records"):
        if flexeme["Gloss_en"] == "":
            continue
        forms = flexeme["Form"].split("; ")
        forms = sorted(forms, key=lambda x: len(x), reverse=True)
        for i, form in enumerate(forms):
            id = f'{flexeme["ID"]}-{i}'
            writer.objects["MorphTable"].append({
                "ID": id,
                "Form": form,
                "Morpheme_ID": flexeme["ID"],
                "Parameter_ID": flexeme["Gloss_en"],
                "Language_ID": flexeme["Language_ID"]
            })
            autocomplete_data.append((f"m:{form}", f"[m]({id})"))
        writer.objects["MorphsetTable"].append({
            "ID": flexeme["ID"],
            "Form": forms[0],
            "Parameter_ID": flexeme["Gloss_en"],
            "Language_ID": flexeme["Language_ID"]
        })
        autocomplete_data.append((f"mp:{forms[0]}", f"[mp]({flexeme['ID']})"))

    writer.objects["LanguageTable"].append({"ID": "yab", "Name": "Yawarana", "Longitude": -54.7457, "Latitude": 1.49792, "Glottocode": "yaba1248"})
    writer.write()
    jsonlib.dump(
        autocomplete_data, "../yaw_sketch/content/.autocomplete_data.json", indent=4
    )
