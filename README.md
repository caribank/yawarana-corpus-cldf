# A digital sketch grammar of Yawarana

The most recent release of this dataset is served [here](https://fl.mt/yawarana-sketch).
The document was written with [`pylingdocs`](https://github.com/fmatter/pylingdocs/).
The corresponding source is available [here](https://github.com/fmatter/yawarana-sketch/releases/tag/0.0.2.draft).

## Running the web app
You can run an app serving this version of the CLDF dataset as follows:

1. create a virtual environment
2. download the source code of the CLLD app: https://github.com/fmatter/yawarana-sketch-clld/releases/tag/0.0.1
3. enter app folder: `cd /path/to/yawarana-sketch-clld`
2. install app: `pip install -e .`
3. initialize database: `clld initdb development.ini --cldf /path/to/yawarana-sketch-cldf/cldf/metadata.json`
4. run server: `pserve --reload development.ini`

There is no audio for the moment, sorry.