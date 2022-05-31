# A digital sketch grammar of Yawarana (v0.0.2.draft)

**CLDF Metadata**: [metadata.json](./metadata.json)

**Sources**: [sources.bib](./sources.bib)

#### The corpus

A corpus of [texts](texts) forms the basis of this grammar sketch.
They were collected by [Natalia Cáceres-Arandia](https://pages.uoregon.edu/nataliac/) in the course of the NSF funded project ['Documenting Linguistic Structure and Language Change in Yawarana'](https://nsf.gov/awardsearch/showAward?AWD_ID=1500714&HistoricalAwards=false).
They were transcribed in ELAN and enriched with morphological annotation by [uniparser-yawarana](https://github.com/fmatter/uniparser-yawarana/) ([matter2022uniparser](sources.bib?with_internal_ref_link&ref#cldf:matter2022uniparser))
The following excerpt showcases the features of the corpus:

[Example ctorat-03](ExampleTable?example_no=1#cldf:ctorat-03)

The first object line is a link to the entire text record ('sentence', 'example'...).
The second line contains links to individual word forms.
The third line contains links to individual morphs.
The link in parentheses leads to the (con-)text of the record.
Audio associated with the record is shown below it.
Translations are partially in English, partially in the contact language, Spanish.

Words that uniparser-yawarana was unable to parse are glossed with `***`:

[Example convrisamaj-28](ExampleTable?example_no=2#cldf:convrisamaj-28)

Words with multiple possible analyses (where none has been confirmed manually yet) are glossed with `?`:

[Example anfoperso-01](ExampleTable?example_no=3#cldf:anfoperso-01)

#### The 'dictionary'
The dictionary part of this app contains different kinds of entities.
At the moment, these are morphemes, morphs, and word forms.
They relate to each other as follows: word forms are forms that occur in the annotated corpus or were uttered in elicitation.
At the moment, there are no unattested (but existent) word forms.
Word forms are composed of morphs, which in turn belong to morphemes.
Word forms as well as morphemes and their morphs can have different meanings, depending on the context.

To illustrate: the form [](FormTable#cldf:f90c63ed-bd4c-43b7-b9f9-2709d3ff0ddd1-septcp) 's/he slept' is composed of the morphs [Morph f90c63ed-bd4c-43b7-b9f9-2709d3ff0ddd1](MorphTable?#cldf:f90c63ed-bd4c-43b7-b9f9-2709d3ff0ddd1) and [Morph septcp](MorphTable?#cldf:septcp), which in turn belong to the morphemes [Morpheme f90c63ed-bd4c-43b7-b9f9-2709d3ff0ddd](MorphsetTable?#cldf:f90c63ed-bd4c-43b7-b9f9-2709d3ff0ddd) and [Morpheme septcp](MorphsetTable?#cldf:septcp).
All of the preceding links lead to detail views of these entities, with information like morphological structure, associated word forms, and, most importantly, tokens from the corpus.

#### The grammar
...is under construction.
The text is written with [pylingdocs](https://github.com/fmatter/pylingdocs), and is available as individual chapters under [documents](documents).
A PDF version can be found [here](download).



property | value
 --- | ---
[dc:bibliographicCitation](http://purl.org/dc/terms/bibliographicCitation) | Matter, Florian, 2022. A digital grammar sketch of Yawarana
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF Generic](http://cldf.clld.org/v1.0/terms.rdf#Generic)
[dc:identifier](http://purl.org/dc/terms/identifier) | https://fl.mt/yawarana-sketch
[dc:license](http://purl.org/dc/terms/license) | https://creativecommons.org/licenses/by-sa/4.0/
[prov:wasGeneratedBy](http://www.w3.org/ns/prov#wasGeneratedBy) | <ol><li><strong>python</strong>: 3.7.13</li><li><strong>python-packages</strong>: <a href="./requirements.txt">requirements.txt</a></li></ol>
[rdf:ID](http://www.w3.org/1999/02/22-rdf-syntax-ns#ID) | yawarana-sketch
[rdf:type](http://www.w3.org/1999/02/22-rdf-syntax-ns#type) | http://www.w3.org/ns/dcat#Distribution


## <a name="table-chaptertable"></a>Table [ChapterTable](./ChapterTable)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 19


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
`Number` | `integer` | Chapter number (optional)

## <a name="table-contributortable"></a>Table [ContributorTable](./ContributorTable)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 3


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
`Email` | `string` | 
`Url` | `string` | 
`Order` | `integer` | 

## <a name="table-examplescsv"></a>Table [examples.csv](./examples.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ExampleTable](http://cldf.clld.org/v1.0/terms.rdf#ExampleTable)
[dc:extent](http://purl.org/dc/terms/extent) | 951


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)
[Primary_Text](http://cldf.clld.org/v1.0/terms.rdf#primaryText) | `string` | The example text in the source language.
[Analyzed_Word](http://cldf.clld.org/v1.0/terms.rdf#analyzedWord) | list of `string` (separated by `\t`) | The sequence of words of the primary text to be aligned with glosses
[Gloss](http://cldf.clld.org/v1.0/terms.rdf#gloss) | list of `string` (separated by `\t`) | The sequence of glosses aligned with the words of the primary text
[Translated_Text](http://cldf.clld.org/v1.0/terms.rdf#translatedText) | `string` | The translation of the example text in a meta language
[Meta_Language_ID](http://cldf.clld.org/v1.0/terms.rdf#metaLanguageReference) | `string` | References the language of the translated text<br>References [languages.csv::ID](#table-languagescsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
`Text_ID` | `string` | The text to which this record belongs<br>References [TextTable::ID](#table-texttable)
`Part` | `integer` | Position in the text
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)

## <a name="table-formscsv"></a>Table [forms.csv](./forms.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF FormTable](http://cldf.clld.org/v1.0/terms.rdf#FormTable)
[dc:extent](http://purl.org/dc/terms/extent) | 159


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | A reference to a language (or variety) the form belongs to<br>References [languages.csv::ID](#table-languagescsv)
[Form](http://cldf.clld.org/v1.0/terms.rdf#form) | `string` | The written expression of the form. If possible the transcription system used for the written form should be described in CLDF metadata (e.g. via adding a common property `dc:conformsTo` to the column description using concept URLs of the GOLD Ontology (such as [phonemicRep](http://linguistics-ontology.org/gold/2010/phonemicRep) or [phoneticRep](http://linguistics-ontology.org/gold/2010/phoneticRep)) as values).
[Segments](http://cldf.clld.org/v1.0/terms.rdf#segments) | list of `string` (separated by ` `) | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
[Parameter_ID](http://cldf.clld.org/v1.0/terms.rdf#parameterReference) | list of `string` (separated by `; `) | A reference to the meaning denoted by the form<br>References [parameters.csv::ID](#table-parameterscsv)
`POS` | `string` | Part of speech<br>References [POSTable::ID](#table-postable)

## <a name="table-parameterscsv"></a>Table [parameters.csv](./parameters.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ParameterTable](http://cldf.clld.org/v1.0/terms.rdf#ParameterTable)
[dc:extent](http://purl.org/dc/terms/extent) | 243


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 

## <a name="table-mediacsv"></a>Table [media.csv](./media.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF MediaTable](http://cldf.clld.org/v1.0/terms.rdf#MediaTable)
[dc:extent](http://purl.org/dc/terms/extent) | 405


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Media_Type](http://cldf.clld.org/v1.0/terms.rdf#mediaType) | `string` | 
[Download_URL](http://cldf.clld.org/v1.0/terms.rdf#downloadUrl) | `anyURI` | 

## <a name="table-languagescsv"></a>Table [languages.csv](./languages.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF LanguageTable](http://cldf.clld.org/v1.0/terms.rdf#LanguageTable)
[dc:extent](http://purl.org/dc/terms/extent) | 1


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Macroarea](http://cldf.clld.org/v1.0/terms.rdf#macroarea) | `string` | 
[Latitude](http://cldf.clld.org/v1.0/terms.rdf#latitude) | `decimal` | 
[Longitude](http://cldf.clld.org/v1.0/terms.rdf#longitude) | `decimal` | 
[Glottocode](http://cldf.clld.org/v1.0/terms.rdf#glottocode) | `string` | 
[ISO639P3code](http://cldf.clld.org/v1.0/terms.rdf#iso639P3code) | `string` | 

## <a name="table-formslices"></a>Table [FormSlices](./FormSlices)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 280


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
`Form_ID` | `string` | References [forms.csv::ID](#table-formscsv)
`Morph_ID` | `string` | References [MorphTable::ID](#table-morphtable)
`Index` | `string` | Specifies the position of a morph in a form.
`Morpheme_Meaning` | `string` | References [parameters.csv::ID](#table-parameterscsv)
`Form_Meaning` | `string` | References [parameters.csv::ID](#table-parameterscsv)

## <a name="table-postable"></a>Table [POSTable](./POSTable)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 11


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 

## <a name="table-exampleslices"></a>Table [ExampleSlices](./ExampleSlices)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 444


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
`Form_ID` | `string` | References [forms.csv::ID](#table-formscsv)
`Example_ID` | `string` | References [examples.csv::ID](#table-examplescsv)
`Slice` | `string` | Specifies the slice of forms.
[Parameter_ID](http://cldf.clld.org/v1.0/terms.rdf#parameterReference) | `string` | A reference to the meaning denoted by the form<br>References [parameters.csv::ID](#table-parameterscsv)

## <a name="table-morphtable"></a>Table [MorphTable](./MorphTable)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 265


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | A reference to a language (or variety) the form belongs to<br>References [languages.csv::ID](#table-languagescsv)
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Segments](http://cldf.clld.org/v1.0/terms.rdf#segments) | list of `string` (separated by ` `) | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
`Morpheme_ID` | `string` | The morpheme this form belongs to<br>References [MorphsetTable::ID](#table-morphsettable)
[Parameter_ID](http://cldf.clld.org/v1.0/terms.rdf#parameterReference) | list of `string` (separated by `; `) | A reference to the meaning denoted by the form<br>References [parameters.csv::ID](#table-parameterscsv)

## <a name="table-morphsettable"></a>Table [MorphsetTable](./MorphsetTable)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 191


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | A reference to a language (or variety) the morpheme belongs to<br>References [languages.csv::ID](#table-languagescsv)
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Parameter_ID](http://cldf.clld.org/v1.0/terms.rdf#parameterReference) | list of `string` (separated by `; `) | A reference to the meaning denoted by the form<br>References [parameters.csv::ID](#table-parameterscsv)

## <a name="table-phonemetable"></a>Table [PhonemeTable](./PhonemeTable)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 22


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 

## <a name="table-texttable"></a>Table [TextTable](./TextTable)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 9


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Title](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Type` | `string` | 
`Metadata` | `json` | 
