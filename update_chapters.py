from pycldf import Dataset
from pathlib import Path
import pandas as pd
from pylingdocs.cldf import metadata as cldf_md

ds = Dataset.from_metadata("cldf/metadata.json")
try:
    ds.remove_table("ChapterTable")
except:
    pass
ds.add_component(cldf_md("ChapterTable"))

doc_path = Path("raw/docs")
chapters = pd.read_csv(doc_path / "chapters.csv")

chapterlist = []
for chapter in chapters.to_dict("records"):
    chapterlist.append(
        {
            "ID": chapter["ID"],
            "Name": chapter["title"],
            "Number": chapter["Number"],
            "Description": open(doc_path / chapter["Filename"], "r").read(),
        }
    )

chapterlist.append(
    {
        "ID": "landingpage",
        "Name": "Landing page",
        "Description": open("raw/landingpage.txt", "r").read(),
    }
)

ds.write(ChapterTable=chapterlist)
