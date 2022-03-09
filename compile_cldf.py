import pandas as pd
from cldfbench.cldf import CLDFWriter
from cldfbench import CLDFSpec
from pathlib import Path
from clldutils.loglib import Logging, get_colorlog
import logging
import sys
from clldutils import jsonlib
from cldfbench_cldf_desc import Dataset as dd 
from clldutils.misc import slug
import pybtex
from pycldf.sources import Source


log = get_colorlog(__name__, sys.stdout, level=logging.INFO)

def cread(filename):
    df = pd.read_csv(filename, keep_default_na=False)
    return df

spec = CLDFSpec(dir="cldf", module="Generic", metadata_fname="metadata.json")


examples = cread("../yawarana_corpus/yawarana_pylacoan/output/parsed.csv")
examples.rename(columns={"Sentence": "Primary_Text"}, inplace=True)
examples["Language_ID"] = "yab"


log.info("Writing CLDF data")
with CLDFWriter(spec) as writer:
    writer.cldf.properties.setdefault("rdf:ID", "yaw_gram")
    writer.cldf.properties.setdefault("dc:title", "Data for a digital sketch grammar of Yawarana")
    writer.cldf.properties.setdefault("dc:description", "Data for a digital sketch grammar of Yawarana")
    writer.cldf.add_component("ExampleTable")

    writer.cldf.add_component(
        component=dd.get_metadata(dd, "MorphTable")
    )

    writer.cldf.add_component(
        dd.get_metadata(dd, "MorphsetTable")
    )

    found_refs = jsonlib.load("etc/refs.json")
    bib = pybtex.database.parse_file("etc/car.bib", bib_format="bibtex")
    sources = [
        Source.from_entry(k, e) for k, e in bib.entries.items() if k in found_refs
    ]
    writer.cldf.add_sources(*sources)

    for ex in examples.to_dict("records"):
        ex["ID"] = ex["ID"].replace(".", "-").lower()
        print(ex)
        ex["Analyzed_Word"] = ex["Analyzed_Word"].split(" ")
        ex["Gloss"] = ex["Gloss"].split(" ")
        writer.objects["ExampleTable"].append(ex)

    for id, morph, gloss in [("sepst", "-se", "PST")]:
        writer.objects["MorphTable"].append({"ID": id, "Form": morph, "Parameter_ID": gloss, "Language_ID": "yab", "Morpheme_ID": id})

    for id, morph, gloss in [("sepst", "-se", "PST")]:
        writer.objects["MorphsetTable"].append({"ID": id, "Form": morph, "Parameter_ID": gloss, "Language_ID": "yab"})

    writer.write()