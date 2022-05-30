default:
	python3 compile_cldf.py
	cldf validate cldf/metadata.json

all:
	make default
	make doc
	
doc:
	cp /home/florianm/Dropbox/research/cariban/yawarana/yaw_sketch/output/latex/main.pdf ./yawarana-sketch.pdf