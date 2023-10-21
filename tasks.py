from invoke import task
from cldf_creator import create
from writio import load
# VERSION = $(shell yq -p=props .bumpversion.cfg | yq eval ".current_version"  )
# .PHONY: cldf full
version = load("etc/metadata.yaml")


@task
def cldf(c):
    load(c)
    create()

@task
def full(c):
    load(c)
    create(full=True)

@task
def load(c):
    c.run(
        """cp ../yawarana_corpus/annotation/output/good.csv raw/examples.csv
    cp ../yawarana_corpus/annotation/output/full.csv raw/full_examples.csv
    cp /home/florianm/Dropbox/research/cariban/yawarana/yawarana_corpus/flexports/sentences.csv raw/flexamples.csv
"""
    )


# release:
#     git commit -am 'release $(VERSION)'
#     git tag -a $(VERSION) -m 'release $(VERSION)'
#     git checkout main
#     git merge dev
#     git push
#     git push --tags
#     git checkout dev
#     git merge main
#     bump2version patch
#     git commit -am "bump"; git push

@task
def readme(c):
    c.run("cldf markdown cldf/metadata.json > cldf/README.md")

# bib:
#     biblatex2bibtex /home/florianm/Dropbox/research/cariban/cariban_references.bib --output etc/car.bib

# examples:
#     cldfbench cldfviz.examples cldf/metadata.json > examples.html; firefox examples.html

# full_examples:
#     cldfbench cldfviz.examples full_cldf/metadata.json > examples.html; firefox examples.html

# valid:
#     cldf validate cldf/metadata.json
#     cldf validate full/metadata.json
