.PHONY: cldf

build: download cldf readme

cldf:
	python3 create_cldf.py

valid:
	cldf validate cldf/metadata.json
	cldf validate full/metadata.json

full:
	python3 create_cldf.py --full

readme:
	cldf markdown cldf/metadata.json > cldf/README.md

download:
	cp ../yawarana_corpus/annotation/output/good.csv raw/examples.csv
	cp ../yawarana_corpus/annotation/output/full.csv raw/full_examples.csv
	cp /home/florianm/Dropbox/research/cariban/yawarana/yawarana_corpus/flexports/sentences.csv raw/flexamples.csv

release:
# 	make cldf_release
# 	make github
# 	make readme
# 	make pdf
# 	make download_extra
# 	git add -f cldf
# 	git commit -am 'release $(VERSION)'
# 	git tag -a $(VERSION) -m 'release $(VERSION)'
# 	git push; git push --tags

github:
	python3 var/create_github_stuff.py

bib:
	biblatex2bibtex /home/florianm/Dropbox/research/cariban/cariban_references.bib --output etc/car.bib

examples:
	cldfbench cldfviz.examples cldf/metadata.json > examples.html; firefox examples.html

full_examples:
	cldfbench cldfviz.examples full_cldf/metadata.json > examples.html; firefox examples.html

check:
	python3 var/consistency_check.py
	grep -r "\['" cldf || true # check for cells containing lists
