# A digital sketch grammar of Yawarana

The most recent release of this dataset is served [here](https://fl.mt/yawarana-sketch).
The [`pylingdocs`](https://github.com/fmatter/pylingdocs/) source is available [here](https://github.com/fmatter/yawarana-sketch/releases/tag/0.0.2.draft).
Released versions of this dataset can be found [here](releases), for the latest click [here](https://github.com/fmatter/yawarana-sketch-cldf/releases/tag/0.0.2.draft).

## Running the app
To reproduce the interactive version of the grammar, you will need [python](https://www.python.org/) with [pip and a virtual environment manager](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/), and [git](https://git-scm.com/).
Follow these steps to run the digital grammar app on your machine:

1. create a virtual environment
2. download the corresponding version of the CLLD app: https://github.com/fmatter/yawarana-sketch-clld/releases/tag/0.0.1
2. rename folder: `mv /path/to/yawarana-sketch-clld-0.0.1 /path/to/yawarana-sketch-clld`
3. enter app folder: `cd /path/to/yawarana-sketch-clld`
2. install app: `pip install -e .`
3. initialize database: `clld initdb development.ini --cldf /path/to/yawarana-sketch-cldf-0.0.2.draft/cldf/metadata.json`
4. run server: `pserve --reload development.ini`

There is no audio for the moment, sorry.