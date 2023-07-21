from writio import load
import configparser
from datetime import datetime
from jinja2 import Template

md = load("etc/metadata.yaml")
md["authors"] = []
a_dic = {
    "Given": "family-names",
    "First": "given-names",
    "Orcid": "orcid",
    "Email": "email",
    "Affiliation": "affiliation",
}
authors = load("etc/contributors.csv", mode="csv2dict", keep_default_na=False).values()
for author in authors:
    md["authors"].append({v: author[k] for k, v in a_dic.items() if author[k] != ""})
config = configparser.ConfigParser()
now = datetime.now()
md["date"] = now.strftime("%Y-%m-%d")
template = open("var/CITATION_templ.cff", "r", encoding="utf-8").read()
j2_template = Template(template)
with open("CITATION.cff", "w", encoding="utf-8") as f:
    f.write(j2_template.render(md))
