# Yawarana corpus

**CLDF Metadata**: [metadata.json](./metadata.json)

**Sources**: [sources.bib](./sources.bib)

This is a CLDF dataset containing a text corpus of Yawarana speech.
The following linguistic entities and properties are encoded:

* sentences
* word forms
* lexemes
* morphemes
* morphs
* parts of speech

property | value
 --- | ---
[dc:bibliographicCitation](http://purl.org/dc/terms/bibliographicCitation) | Cáceres, Natalia and Matter, Florian and Mattéi-Müller, Marie-Claude and Gildea, Spike, 2023. Yawarana corpus [CLDF dataset].
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF Generic](http://cldf.clld.org/v1.0/terms.rdf#Generic)
[dc:license](http://purl.org/dc/terms/license) | https://creativecommons.org/licenses/by-sa/4.0/
[prov:wasGeneratedBy](http://www.w3.org/ns/prov#wasGeneratedBy) | <ol><li><strong>python</strong>: 3.8.10</li><li><strong>python-packages</strong>: <a href="./requirements.txt">requirements.txt</a></li></ol>
[rdf:ID](http://www.w3.org/1999/02/22-rdf-syntax-ns#ID) | yawarana-corpus
[rdf:type](http://www.w3.org/1999/02/22-rdf-syntax-ns#type) | http://www.w3.org/ns/dcat#Distribution


## <a name="table-wordformscsv"></a>Table [wordforms.csv](./wordforms.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 318


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | A reference to a language (or variety) the form belongs to<br>References [languages.csv::ID](#table-languagescsv)
[Form](http://cldf.clld.org/v1.0/terms.rdf#form) | `string` | The written expression of the form.
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | A human-readable description
[Part_Of_Speech](http://cldf.clld.org/v1.0/terms.rdf#partOfSpeech) | `string` | References [partsofspeech.csv::ID](#table-partsofspeechcsv)
`Parameter_ID` | list of `string` (separated by `; `) | A reference to the meaning denoted by the form
`Morpho_Segments` | list of `string` (separated by ` `) | A representation of the morphologically segmented form.
`Stem_ID` | `string` | The stem of which this wordform is an inflected form.<br>References [stems.csv::ID](#table-stemscsv)
[Segments](http://cldf.clld.org/v1.0/terms.rdf#segments) | list of `string` (separated by ` `) | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Media_ID` | `string` | 

## <a name="table-stemscsv"></a>Table [stems.csv](./stems.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 624


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | A reference to a language (or variety) the stem belongs to<br>References [languages.csv::ID](#table-languagescsv)
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
`Lexeme_ID` | `string` | The lexeme this stem belongs to.<br>References [lexemes.csv::ID](#table-lexemescsv)
`Parameter_ID` | list of `string` (separated by `; `) | A reference to the meaning denoted by the stem.
`Morpho_Segments` | list of `string` (separated by ` `) | A representation of the morphologically segmented stem.
[Segments](http://cldf.clld.org/v1.0/terms.rdf#segments) | list of `string` (separated by ` `) | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `; `) | References [sources.bib::BibTeX-key](./sources.bib)
[Part_Of_Speech](http://cldf.clld.org/v1.0/terms.rdf#partOfSpeech) | `string` | References [partsofspeech.csv::ID](#table-partsofspeechcsv)

## <a name="table-morphscsv"></a>Table [morphs.csv](./morphs.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 765


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | A reference to a language (or variety) the form belongs to<br>References [languages.csv::ID](#table-languagescsv)
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | A human-readable description.
[Segments](http://cldf.clld.org/v1.0/terms.rdf#segments) | list of `string` (separated by ` `) | 
`Morpheme_ID` | `string` | The morpheme this form belongs to.<br>References [morphemes.csv::ID](#table-morphemescsv)
`Parameter_ID` | list of `string` (separated by `; `) | A reference to the meaning denoted by the morph.
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `; `) | References [sources.bib::BibTeX-key](./sources.bib)
[Part_Of_Speech](http://cldf.clld.org/v1.0/terms.rdf#partOfSpeech) | `string` | References [partsofspeech.csv::ID](#table-partsofspeechcsv)

## <a name="table-inflectionscsv"></a>Table [inflections.csv](./inflections.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 157


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
`Stem_ID` | `string` | The stem this wordform is an inflected form of.<br>References [stems.csv::ID](#table-stemscsv)
`Value_ID` | `string` | The inflectional value being expressed.<br>References [inflectionalvalues.csv::ID](#table-inflectionalvaluescsv)
`Wordformpart_ID` | list of `string` (separated by `,`) | The part of the wordform expressing this value.<br>References [wordformparts.csv::ID](#table-wordformpartscsv)
`Form_ID` | `string` | The multi-word form this inflection references.<br>References [forms.csv::ID](#table-formscsv)

## <a name="table-inflectionalvaluescsv"></a>Table [inflectionalvalues.csv](./inflectionalvalues.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 17


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
`Category_ID` | `string` | The inflectional category the value belongs to.<br>References [inflectionalcategories.csv::ID](#table-inflectionalcategoriescsv)
`Gloss_ID` | `string` | The gloss for the inflectional value.<br>References [glosses.csv::ID](#table-glossescsv)

## <a name="table-inflectionalcategoriescsv"></a>Table [inflectionalcategories.csv](./inflectionalcategories.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 7


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
`Value_Order` | list of `string` (separated by `,`) | The order in which the values of this category should be ordered (contains inflectionalvalue IDs).

## <a name="table-lexemescsv"></a>Table [lexemes.csv](./lexemes.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 508


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | A reference to a language (or variety) the lexeme belongs to<br>References [languages.csv::ID](#table-languagescsv)
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | A human-readable description
[Part_Of_Speech](http://cldf.clld.org/v1.0/terms.rdf#partOfSpeech) | `string` | 
`Parameter_ID` | list of `string` (separated by `; `) | A reference to the meaning denoted by the lexeme.
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
`Paradigm_View` | `json` | A dict with 'x' and 'y' keys containing lists of derivational category IDs.
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)

## <a name="table-morphemescsv"></a>Table [morphemes.csv](./morphemes.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 596


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | A reference to a language (or variety) the morpheme belongs to.<br>References [languages.csv::ID](#table-languagescsv)
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | A human-readable description.
`Parameter_ID` | list of `string` (separated by `; `) | A reference to the meaning denoted by the morpheme.
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `; `) | References [sources.bib::BibTeX-key](./sources.bib)
[Part_Of_Speech](http://cldf.clld.org/v1.0/terms.rdf#partOfSpeech) | `string` | References [partsofspeech.csv::ID](#table-partsofspeechcsv)

## <a name="table-derivationscsv"></a>Table [derivations.csv](./derivations.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 95


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
`Process_ID` | `string` | The derivational process involved.<br>References [derivationalprocesses.csv::ID](#table-derivationalprocessescsv)
`Target_ID` | `string` | The derived stem.<br>References [stems.csv::ID](#table-stemscsv)
`Source_ID` | `string` | The stem to which the derivational process applies.<br>References [stems.csv::ID](#table-stemscsv)
`Root_ID` | `string` | The root to which the derivational process applies.<br>References [morphs.csv::ID](#table-morphscsv)
`Stempart_IDs` | list of `string` (separated by `,`) | Specifies one or multiple morphs in the stem marking the derivation.<br>References [stemparts.csv::ID](#table-stempartscsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 

## <a name="table-derivationalprocessescsv"></a>Table [derivationalprocesses.csv](./derivationalprocesses.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 17


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)

## <a name="table-wordformpartscsv"></a>Table [wordformparts.csv](./wordformparts.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 516


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
`Wordform_ID` | `string` | The involved wordform.<br>References [wordforms.csv::ID](#table-wordformscsv)
`Morph_ID` | `string` | The involved morph.<br>References [morphs.csv::ID](#table-morphscsv)
`Index` | `string` | Specifies the position of a morph in a wordform.
`Gloss_ID` | list of `string` (separated by `,`) | The gloss the morph has in the wordform.<br>References [glosses.csv::ID](#table-glossescsv)

## <a name="table-wordformstemscsv"></a>Table [wordformstems.csv](./wordformstems.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 292


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
`Wordform_ID` | `string` | The associated wordform.<br>References [wordforms.csv::ID](#table-wordformscsv)
`Stem_ID` | `string` | The stem of the associated wordform.<br>References [stems.csv::ID](#table-stemscsv)
`Index` | list of `integer` (separated by `,`) | Specifies the position(s) of an stem in a wordform.

## <a name="table-stempartscsv"></a>Table [stemparts.csv](./stemparts.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 732


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
`Stem_ID` | `string` | The involved stem.<br>References [stems.csv::ID](#table-stemscsv)
`Morph_ID` | `string` | The involved morph.<br>References [morphs.csv::ID](#table-morphscsv)
`Index` | `string` | Specifies the position of a morph in a stem.
`Gloss_ID` | list of `string` (separated by `,`) | The gloss the morph has in the stem.<br>References [glosses.csv::ID](#table-glossescsv)

## <a name="table-glossescsv"></a>Table [glosses.csv](./glosses.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 531


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 

## <a name="table-partsofspeechcsv"></a>Table [partsofspeech.csv](./partsofspeech.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 11


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | A reference to a language (or variety) the form belongs to<br>References [languages.csv::ID](#table-languagescsv)
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | A human-readable description
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)

## <a name="table-textscsv"></a>Table [texts.csv](./texts.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 3


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Type` | `string` | 
`Metadata` | `json` | 

## <a name="table-examplepartscsv"></a>Table [exampleparts.csv](./exampleparts.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 815


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
`Wordform_ID` | `string` | References [wordforms.csv::ID](#table-wordformscsv)
`Example_ID` | `string` | References [examples.csv::ID](#table-examplescsv)
`Index` | `string` | Specifies the position of a form in a sentence.
[Parameter_ID](http://cldf.clld.org/v1.0/terms.rdf#parameterReference) | `string` | A reference to the meaning denoted by the form

## <a name="table-phonemescsv"></a>Table [phonemes.csv](./phonemes.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 23


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | A human-readable description.
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | A reference to a language (or variety) the phoneme belongs to<br>References [languages.csv::ID](#table-languagescsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)

## <a name="table-speakerscsv"></a>Table [speakers.csv](./speakers.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 11


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 

## <a name="table-contributorscsv"></a>Table [contributors.csv](./contributors.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 3


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
`Email` | `string` | 
`Orcid` | `string` | 
`Url` | `string` | 
`Order` | `integer` | 

## <a name="table-examplescsv"></a>Table [examples.csv](./examples.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ExampleTable](http://cldf.clld.org/v1.0/terms.rdf#ExampleTable)
[dc:extent](http://purl.org/dc/terms/extent) | 153


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)
[Primary_Text](http://cldf.clld.org/v1.0/terms.rdf#primaryText) | `string` | The example text in the source language.
[Analyzed_Word](http://cldf.clld.org/v1.0/terms.rdf#analyzedWord) | list of `string` (separated by `	`) | The sequence of words of the primary text to be aligned with glosses
[Gloss](http://cldf.clld.org/v1.0/terms.rdf#gloss) | list of `string` (separated by `	`) | The sequence of glosses aligned with the words of the primary text
[Translated_Text](http://cldf.clld.org/v1.0/terms.rdf#translatedText) | `string` | The translation of the example text in a meta language
[Meta_Language_ID](http://cldf.clld.org/v1.0/terms.rdf#metaLanguageReference) | `string` | References the language of the translated text<br>References [languages.csv::ID](#table-languagescsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Media_ID](http://cldf.clld.org/v1.0/terms.rdf#mediaReference) | `string` | References [media.csv::ID](#table-mediacsv)
`Part_Of_Speech` | list of `string` (separated by `	`) | 
`Original_Translation` | `string` | The original translation of the example text.
`Text_ID` | `string` | The larger discourse context in which this record was uttered.<br>References [texts.csv::ID](#table-textscsv)
`Record_Number` | `integer` | The positions of this record in the text.
`Speaker_ID` | `string` | The speaker who uttered this record.<br>References [speakers.csv::ID](#table-speakerscsv)

## <a name="table-formscsv"></a>Table [forms.csv](./forms.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF FormTable](http://cldf.clld.org/v1.0/terms.rdf#FormTable)
[dc:extent](http://purl.org/dc/terms/extent) | 2


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | A reference to a language (or variety) the form belongs to<br>References [languages.csv::ID](#table-languagescsv)
[Parameter_ID](http://cldf.clld.org/v1.0/terms.rdf#parameterReference) | `string` | A reference to the meaning denoted by the form
[Form](http://cldf.clld.org/v1.0/terms.rdf#form) | `string` | The written expression of the form. If possible the transcription system used for the written form should be described in CLDF metadata (e.g. via adding a common property `dc:conformsTo` to the column description using concept URLs of the GOLD Ontology (such as [phonemicRep](http://linguistics-ontology.org/gold/2010/phonemicRep) or [phoneticRep](http://linguistics-ontology.org/gold/2010/phoneticRep)) as values).
[Segments](http://cldf.clld.org/v1.0/terms.rdf#segments) | list of `string` (separated by ` `) | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Media_ID` | `string` | 
`Morpho_Segments` | list of `string` (separated by ` `) | The form, segmented into morphological segments.

## <a name="table-mediacsv"></a>Table [media.csv](./media.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF MediaTable](http://cldf.clld.org/v1.0/terms.rdf#MediaTable)
[dc:extent](http://purl.org/dc/terms/extent) | 234


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Media_Type](http://cldf.clld.org/v1.0/terms.rdf#mediaType) | `string` | 
[Download_URL](http://cldf.clld.org/v1.0/terms.rdf#downloadUrl) | `anyURI` | 
[Path_In_Zip](http://cldf.clld.org/v1.0/terms.rdf#pathInZip) | `string` | 

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
