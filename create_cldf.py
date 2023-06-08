# Prelude
## Import
import argparse
import logging
import re
import sys
import time
from writio import load
from pathlib import Path
from types import SimpleNamespace

from yawarana_helpers import split_cliticized
import pandas as pd
import pybtex
import yaml
from cffconvert.cli.create_citation import create_citation
from cffconvert.cli.validate_or_write_output import validate_or_write_output
from cldf_ldd import add_columns, add_keys
from cldf_ldd.components import tables as ldd_tables
from cldfbench import CLDFSpec
from cldfbench.cldf import CLDFWriter
from clldutils import jsonlib
from clldutils.loglib import get_colorlog
from humidifier import get_values, humidify
from pycldf.dataset import MD_SUFFIX
from pycldf.sources import Source
from pycldf.util import pkg_path
from pylingdocs.cldf import tables as pld_tables
from pylingdocs.preprocessing import preprocess_cldfviz
from segments import Profile, Tokenizer
from itertools import product
from uniparser_yawarana import YawaranaAnalyzer
from yawarana_helpers import (
    find_detransitivizer,
    glossify,
    trim_dic_suff,
    get_pos,
    strip_form,
)

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--full", action="store_true")
args = parser.parse_args()

start_time = time.perf_counter()

log = get_colorlog(__name__, sys.stdout, level=logging.INFO)

## Config

# the cell-internal separator used in all sort of tables
SEP = "; "
# derivations are stored here
UP_DIR = Path("/home/florianm/Dropbox/development/uniparser-yawarana/data")
# location where all audio is stored
AUDIO_PATH = Path(
    "/home/florianm/Dropbox/research/cariban/yawarana/yawarana_corpus/audio"
)
# wordform audio files
WORD_AUDIO_PATH = AUDIO_PATH / "wordforms"

## Global helpers
# use pandas to read csvs and not use NaN
def cread(filename):
    df = pd.read_csv(filename, encoding="utf-8", keep_default_na=False)
    if "Translation" in df.columns:
        splitcol(df, "Translation")
    if "ID" in df.columns:
        df.set_index("ID", drop=False)
    return df


# print current dataframes
def debug_dfs(key=None):
    for k, data in vars(df).items():
        if key and key != k:
            continue
        print(data)
        print(k)
    sys.exit()


# turn glosses into gloss IDs
def id_glosses(gloss, sep=None):
    if isinstance(gloss, list):
        return [id_glosses(x) for x in gloss]
    res = [humidify(g, key="glosses") for g in re.split(r"\.\b", gloss)]
    if sep is not None:
        return sep.join(res)
    return res


# combine several dataframes in the namespace
def join_dfs(name, *keys):
    setattr(df, name, pd.concat([vars(df)[key] for key in keys]).fillna(""))
    for key in keys:
        if key != name:
            delattr(df, key)


# tokenize into segments
phonemes = cread("etc/phonemes.csv")
prf = Profile(*phonemes.to_dict("records"))
t = Tokenizer(profile=prf)


def tokenize(s):
    return t(s, column="IPA").split(" ")


def timer(msg):
    toc = time.perf_counter()
    print(f"{msg}: {toc - start_time:0.4f} seconds")


# cast to list
def split_if_not_list(s, sep=","):
    if not isinstance(s, list):
        return s.split(sep)
    return s


def splitform(s):
    return s.split("-")


def splitcol(df, col, sep="; "):
    df[col] = df[col].apply(lambda x: x.split(sep))


def ipaify(s):
    return t(s, column="IPA", segment_separator="", separator=" ")


morph_dic = {}


def add_to_morph_dict(morph):
    for g in morph["Translation"]:
        morph_tuple = (f'{morph["Form"].strip("-")}', glossify(g))
        morph_dic.setdefault(morph_tuple, {})
        morph_dic[morph_tuple][morph["Morpheme_ID"]] = morph["ID"]


# namespace for storing dataframes
df = SimpleNamespace()

# Data from morphological and lexical analysis
## Bound morph(emes)

morph_infl_dict = {}


def add_morph_infl(rec):
    if rec["Value"]:
        morph_infl_dict[rec["ID"]] = rec["Value"]


### Inflectional, derivational and "misc" morph(eme)s
for kind in [
    "derivation",
    "inflection",
    "misc",
]:  # different manually entered morph(eme)s
    morphemes = cread(f"etc/{kind}_morphemes.csv")
    morphs = cread(f"etc/{kind}_morphs.csv")
    if kind == "inflection":
        morphemes.apply(add_morph_infl, axis=1)
        morphs["Value"] = morphs["Morpheme_ID"].map(morph_infl_dict).fillna("")
        morphs.apply(add_morph_infl, axis=1)
    morphs["Name"] = morphs["Form"]
    morphs["Language_ID"] = "yab"
    morphemes["Language_ID"] = "yab"
    morphemes["Parameter_ID"] = morphemes["Translation"]
    morph_meanings = dict(zip(morphemes["ID"], morphemes["Translation"]))
    morphs["Translation"] = morphs["Morpheme_ID"].map(morph_meanings)
    morphs["Parameter_ID"] = morphs["Translation"]
    morphs.apply(add_to_morph_dict, axis=1)
    morphs["Gloss"] = morphs["Translation"].apply(glossify)
    setattr(df, f"{kind}_morphs", morphs)
    setattr(df, f"{kind}_morphemes", morphemes)

# dictionary of derivational morphs for later enjoyment
deriv_proc_dic = {}


def add_to_proc_dict(x):
    deriv_proc_dic[x["ID"]] = {"Form": x["Name"], "Gloss": x["Translation"]}


df.derivation_morphemes.apply(add_to_proc_dict, axis=1)

### Bound roots
# roots that don't occur as stems
df.bound_roots = cread(UP_DIR / "bound_roots.csv")
df.bound_roots["Language_ID"] = "yab"
df.bound_roots["Parameter_ID"] = df.bound_roots["Translation"]
df.bound_roots["Gloss"] = df.bound_roots["Translation"].apply(glossify)
df.bound_roots["ID"] = df.bound_roots.apply(
    lambda x: humidify(f'{x["Name"]}-{x["Translation"]}', key="morphemes"), axis=1
)
splitcol(df.bound_roots, "Form")
df.bound_root_morphs = df.bound_roots.explode("Form")
df.bound_root_morphs["Morpheme_ID"] = df.bound_root_morphs["ID"]
df.bound_root_morphs["ID"] = df.bound_root_morphs.apply(
    lambda x: humidify(f'{x["Form"]}-{x["Translation"]}', key="morphs"), axis=1
)

## Lexicon
# enriched LIFT export from MCMM
dic = pd.read_csv(
    "../yawarana_dictionary/annotated_dictionary.csv",
    keep_default_na=False,
)
# keep only roots
dic_roots = dic[dic["Translation_Root"] != ""].copy()
dic_roots.rename(columns={"Translation_Root": "Translation"}, inplace=True)
# cut off lemma-forming suffixes
dic_roots = dic_roots.apply(lambda x: trim_dic_suff(x, SEP), axis=1)
dic_roots["Translation"] = dic_roots["Translation"].apply(lambda x: x.replace("-", "_"))
dic_roots["Translation"] = dic_roots["Translation"].apply(lambda x: x.split(SEP))
dic_roots["Gloss"] = dic_roots["Translation"].apply(glossify)
# get variants
dic_roots["Form"] = dic_roots.apply(
    lambda x: SEP.join(list(x["Form"].split(SEP) + x["Variants"].split(SEP))).strip(
        SEP
    ),
    axis=1,
)


# manually entered roots
manual_roots = cread("etc/manual_roots.csv")
manual_roots["Gloss"] = manual_roots["Translation"]

# a dataframe containing root morphemes
df.roots = pd.concat([dic_roots, manual_roots])
df.roots["Language_ID"] = "yab"
# process roots
for split_col in ["Form"]:
    df.roots[split_col] = df.roots[split_col].apply(lambda x: x.split(SEP))
df.roots["Name"] = df.roots["Form"].apply(lambda x: x[0])
# create IDs
df.roots["ID"] = df.roots.apply(
    lambda x: humidify(f"{x.Name}-{x.Gloss[0]}", unique=True, key="morpheme"),
    axis=1,
)
df.roots["Gloss"] = df.roots["Gloss"].apply(glossify)
df.roots["Parameter_ID"] = df.roots["Gloss"]

keep_cols = [
    "ID",
    "Language_ID",
    "Name",
    "Form",
    "Translation",
    "Gloss",
    "Parameter_ID",
    "POS",
    "Comment",
]
df.roots = df.roots[keep_cols]


# ?roots["Description"] = roots["Parameter_ID"]
# only roots with these POS are assumed to be stems/lexemes (i.e., take inflectional morphology)
stem_pos_list = ["vt", "vi", "n", "postp", "pn", "adv"]
df.root_lex = df.roots[df.roots["POS"].isin(stem_pos_list)].copy()
df.stems = df.root_lex.explode("Form")
df.stems["Lexeme_IDs"] = df.stems["ID"]
df.stems["ID"] = df.stems.apply(
    lambda x: humidify(f"{x.Form}-{x.Gloss[0]}", unique=True, key="stems"), axis=1
)
df.root_lex["Main_Stem"] = df.root_lex["ID"]

df.stems["Morpho_Segments"] = df.stems["Form"].apply(
    lambda x: x.split(" ")
)  # todo does this do what it should?


df.root_morphs = df.roots.explode("Form")
df.root_morphs["Morpheme_ID"] = df.root_morphs["ID"]
df.root_morphs["ID"] = df.root_morphs.apply(
    lambda x: humidify(f"{x.Form}-{x.Gloss[0]}", unique=True, key="morphids"), axis=1
)
df.root_morphs.apply(add_to_morph_dict, axis=1)
df.root_morphs["Name"] = df.root_morphs["Form"]

stemparts = [
    {
        "ID": x["ID"],
        "Stem_ID": x["ID"],
        "Morph_ID": x["ID"],
        "Gloss": x["Gloss"][0],
        "Index": 0,
    }
    for i, x in df.stems.iterrows()
]

join_dfs(
    "morphs", "inflection_morphs", "derivation_morphs", "misc_morphs", "root_morphs"
)

join_dfs(
    "morphemes",
    "inflection_morphemes",
    "derivation_morphemes",
    "misc_morphemes",
    "roots",
)


## Complex lexical data

processes = []
derivations = {}

# derived stems
kavbz = cread(UP_DIR / "derivations/kavbz.csv")
tavbz = cread(UP_DIR / "derivations/tavbz.csv")
detrz = cread(UP_DIR / "derivations/detrz.csv")
macaus = cread(UP_DIR / "derivations/macaus.csv")
miscderiv = cread(UP_DIR / "derivations/misc_derivations.csv")
detrz["Affix_ID"] = detrz["Form"].apply(find_detransitivizer)
kavbz["Affix_ID"] = "kavbz"
tavbz["Affix_ID"] = "tavbz"
macaus["Affix_ID"] = "macaus"
detrz["POS"] = "vi"
tavbz["POS"] = "vi"
kavbz["POS"] = "vt"
macaus["POS"] = "vt"

complicated_stems = []


def get_stempart_cands(rec, part, process):
    cands = df.morphs[df.morphs["Form"].str.strip("-") == part]
    if len(cands) > 2 and process == "kavbz":
        cands = cands[cands["ID"] == "kavbz"]
    elif len(cands) > 2 and process == "tavbz":
        cands = cands[cands["ID"] == "tavbz"]
    elif len(cands) > 2 and process == "macaus":
        cands = cands[cands["ID"] == "macaus"]
    elif len(cands) > 1 and process == "detrz":
        cands = cands[cands["Parameter_ID"].apply(lambda x: x == ["DETRZ"])]
    if len(cands) == 0:
        # is the base a bound root?
        bound_root_base = df.bound_root_morphs[
            df.bound_root_morphs["ID"] == rec["Base_Stem"]
        ]
        if len(bound_root_base) == 1:
            cands = bound_root_base
        # or is it a complex form?
    if len(cands) > 1 and rec["Base_Stem"] in list(cands["ID"]):
        cands = cands[cands["ID"] == rec["Base_Stem"]]
    elif len(cands) > 1 and process in deriv_proc_dic:
        cands = cands[cands["ID"] == process]
    return cands


def process_stem(rec, process):
    rec["Form"] = rec["Form"]
    rec["Form"] = rec["Form"].split(SEP)
    rec["ID"] = humidify(f'{strip_form(rec["Form"][0])}-{rec["Translation"][0]}')
    if (
        rec["Base_Stem"] not in list(df.stems["ID"])
        and rec["Base_Stem"] not in derivations
        and rec["Base_Root"] not in list(df.bound_root_morphs["ID"])
    ):
        print(rec)
        print(df.stems)
        print(df.bound_root_morphs)
        print(derivations)
        raise ValueError(rec)
    if not process:
        process = rec["Affix_ID"]
    rec["Morpho_Segments"] = []
    for form in rec["Form"]:
        parts = re.split(r"-|\+", form)
        form = strip_form(form)
        stem_id = humidify(strip_form(form) + "-" + rec["Translation"][0])
        for idx, part in enumerate(parts):
            cands = get_stempart_cands(rec, part, process)
            if len(cands) == 1:
                hit = cands.iloc[0]
                stemparts.append(
                    {
                        "ID": f"{stem_id}-{idx}",
                        "Stem_ID": stem_id,
                        "Morph_ID": hit["ID"],
                        "Index": idx,
                        "Gloss": hit["Gloss"][0],
                    }
                )
                if hit["ID"] == rec["Affix_ID"]:
                    derivations[rec["ID"]] = {
                        "ID": rec["ID"],
                        "Process_ID": process,
                        "Target_ID": rec["ID"],
                        "Stempart_IDs": f"{stem_id}-{idx}",
                    }
                    if rec["Base_Stem"] in list(df.bound_root_morphs["ID"]):
                        derivations[rec["ID"]]["Root_ID"] = rec[
                            "Base_Stem"
                        ]  # these are not based on stems, but on roots that only occur bound
                    else:
                        derivations[rec["ID"]]["Source_ID"] = rec["Base_Stem"]
            elif len(cands) == 0:
                complicated_stems.append([rec.copy(), idx])
            elif len(cands) > 1:
                log.warning(f"Unable to disambiguate stem parts for {rec['Form']}")
                print(cands)
        rec["Morpho_Segments"].append(parts)
    rec["Gloss"] = glossify(rec["Translation"])
    rec["Form"] = [x.replace("+", "") for x in rec["Form"]]
    return rec


tavbz = tavbz.apply(lambda x: process_stem(x, "tavbz"), axis=1)
kavbz = kavbz.apply(lambda x: process_stem(x, "kavbz"), axis=1)
macaus = macaus.apply(lambda x: process_stem(x, "macaus"), axis=1)
detrz = detrz.apply(lambda x: process_stem(x, "detrz"), axis=1)
miscderiv = miscderiv.apply(lambda x: process_stem(x, None), axis=1)

df.derived_lex = pd.concat([tavbz, kavbz, detrz, macaus, miscderiv])
df.derived_lex["Language_ID"] = "yab"
df.derived_lex["Lexeme_IDs"] = df.derived_lex["ID"]
df.derived_lex["Parameter_ID"] = df.derived_lex["Translation"]

for iii, (stem, idx) in enumerate(complicated_stems):
    if stem["Base_Stem"] in derivations:
        log.warning(
            f"Stem {stem['Form']} is derived from {derivations[stem['Base_Stem']]['Target_ID']}; can it know its stemparts?"
        )
    else:
        log.warning(f"Cannot identify source of derived stem {stem['Form']}")
df.derived_stems = df.derived_lex.explode(["Form", "Morpho_Segments"])

df.derived_lex["Name"] = df.derived_lex["Form"].apply(lambda x: strip_form(x[0]))
df.derived_stems["Lexeme_IDs"] = df.derived_stems["ID"]
df.derived_stems["ID"] = df.derived_stems.apply(
    lambda x: humidify(f"{strip_form(x.Form)}-{x.Gloss[0]}", unique=True, key="stems"),
    axis=1,
)
df.derived_lex["Main_Stem"] = df.derived_lex["ID"]

# print(df.derived_stems[["ID", "Form", "Translation", "Lexeme_IDs", "Base_Stem", "Base_Root", "Morpho_Segments", "Lexeme_IDs"]].to_string())
# print(df.derived_lex[["ID", "Form", "Translation", "Lexeme_IDs", "Base_Stem", "Base_Root"]].to_string())

# print(df.derived_lex[["ID", "Form", "Translation", "Main_Stem"]].to_string())

join_dfs("stems", "stems", "derived_stems")
join_dfs("lexemes", "root_lex", "derived_lex")
df.lexemes = df.lexemes.set_index("ID", drop=False)
df.stems["Gloss_ID"] = df.stems["Gloss"].apply(id_glosses)
df.stems["Name"] = df.stems["Form"].apply(strip_form)
df.stems["Description"] = df.stems["Translation"]
df.stems["Language_ID"] = "yab"
df.stems["Segments"] = df.stems["Name"].apply(tokenize)

# a dict mapping object-gloss tuples to stem IDs
stem_dic = {}


def add_to_stem_dict(stem):
    for g in stem["Gloss"]:
        stem_tuple = (f'{stem["Name"].strip("-")}', g)
        stem_dic.setdefault(stem_tuple, {})
        stem_dic[stem_tuple][stem["Lexeme_IDs"]] = stem["ID"]


df.stems.apply(add_to_stem_dict, axis=1)
# Attested data


df.speakers = cread("etc/speakers.csv")
df.speakers["ID"] = df.speakers["Name"].apply(
    lambda x: humidify(x, key="speakers", unique=True)
)


# for every wordform, we want to know:
# morphological structure, i.e. morphs (WordformParts)
# inflectional values
# a meaning
# the part of speech
# the wordform dict
wf_dict = {}
wf_morphs = []
inflections = []
wf_stems = []
productive_stems = {}
productive_derivations = []
productive_lexemes = {}
tuple_lookup = {}

deriv_source_pos = {"anonmlz": ["adv", "postp"], "keprop": ["n"], "ninmlz": ["vt"]}


def build_productive_stem(source_stem, process, obj):
    if process not in deriv_proc_dic:
        log.warning(process)
        return None, None, None
    suff_form = deriv_proc_dic[process]["Form"]
    for part in splitform(obj):
        cands = get_stempart_cands(source_stem, part, process)
        if len(cands) == 1 and cands.iloc[0]["Morpheme_ID"] == process:
            suff_form = cands.iloc[0]["Form"]
    stem_form = f"{source_stem.Form}-{suff_form}".replace("--", "-")
    stem_glosses = [
        f"{x}-{y}"
        for x, y in list(product(source_stem.Gloss, deriv_proc_dic[process]["Gloss"]))
    ]
    stem_id = humidify(f"{strip_form(stem_form)}-{stem_glosses[0]}", key="stems")
    log.debug(
        f"The stem {stem_form} '{', '.join(stem_glosses)}' ({stem_id}) is derived from {source_stem.Form} '{', '.join(source_stem.Gloss)}' ({source_stem.ID}) with {deriv_proc_dic[process]['Form']} ({process})"
    )
    return stem_form, stem_glosses, stem_id


def resolve_productive_stem(lex, process, obj, gloss, pos):
    log.debug(
        f"Uniparser lexeme: {lex}\nactual wordform: {obj} '{gloss}'\nuniparser process: {process}"
    )
    cands = df.lexemes[df.lexemes["Name"] == lex]
    if len(cands) > 1:
        cands = cands[
            cands.apply(
                lambda x: len(set(set(x["Gloss"]) & set(gloss.split("-")))) > 0, axis=1
            )
        ]
    if len(cands) == 1:
        source_lex = cands.iloc[0]
    elif len(cands) > 1:
        log.warning(f"Could not disambiguate stem {lex}")
        log.warning(cands)
        exit()
    elif len(cands) == 0:
        log.warning(f"Found no candidates for stem {lex}")
        log.warning(lex)
        return None, None
    stem_cands = df.stems[df.stems["Lexeme_IDs"] == source_lex.name]
    if len(stem_cands) > 1:
        stem_cands = stem_cands[stem_cands["Form"].isin(obj.split("-"))]
    if len(stem_cands) > 1:
        log.warning(f"Ambiguity in resolving productive derivation {obj}&{process}:")
        print(stem_cands)
        return None, None
    if len(stem_cands) == 0:
        log.warning(
            f"Unable to resolve productive derivation {obj}&{process} in form {obj} '{gloss}'."
        )
        return None, None
    source_stem = stem_cands.iloc[0]
    # todo: do these need to find their way back in?
    # if len(cands) == 0:
    #     cands = df.bound_root_morphs[df.bound_root_morphs["Form"] == obj]
    # if len(cands) > 1 and process in deriv_source_pos:
    #     cands = cands[cands["POS"].isin(deriv_source_pos[process])]
    new_stem_form, new_stem_gloss, new_stem_id = build_productive_stem(
        source_stem, process, obj
    )
    if not new_stem_form:
        return None, None
    if new_stem_id not in productive_stems:
        stemrec = {
            "Form": new_stem_form,
            "Base_Stem": source_stem.ID,
            "Translation": new_stem_gloss,
            "Affix_ID": process,
            "POS": pos,
        }
        for part in splitform(new_stem_form):
            res = get_stempart_cands(stemrec, part, process)
            if len(res) == 1 and res.iloc[0]["Morpheme_ID"] == process:
                stemrec["Affix_ID"] = res.iloc[0]["ID"]
        parsed_stem = process_stem(
            stemrec,
            process,
        )
        parsed_stem["Parameter_ID"] = parsed_stem["Translation"]
        parsed_stem["Name"] = parsed_stem["Form"][0]
        productive_lexemes[new_stem_id] = parsed_stem
        parsed_stem["Lexeme_IDs"] = new_stem_id
        productive_stems[new_stem_id] = parsed_stem
    return new_stem_id, source_stem.Lexeme_IDs


lex_stem_dic = {}


def lexeme2stem(lex, obj, pos):
    if (lex, obj) in lex_stem_dic:
        return lex_stem_dic[(lex, obj)]
    cands = df.stems[df.stems["Lexeme_IDs"] == lex]
    if len(cands) > 1:
        cands = cands[cands["Form"].isin(splitform(obj))]
    if len(cands) == 0:
        if pos in stem_pos_list:
            log.warning(
                f"lexeme2stem: could not identify stem for lexeme {lex} in form {obj}."
            )
        lex_stem_dic[(lex, obj)] = lex
        return lex
    elif len(cands) == 1:
        stem_id = cands.iloc[0]["ID"]
        lex_stem_dic[(lex, obj)] = stem_id
        return stem_id
    else:
        log.warning(
            f"lexeme2stem: could not resolve stem for lexeme {lex} in form {obj}"
        )
        lex_stem_dic[(lex, obj)] = lex
        return lex


def identify_part(obj, gloss, ids):
    kinds = {}
    if (obj, gloss) in morph_dic:
        cands = morph_dic[(obj, gloss)]
        kinds["morph"] = cands
    if (obj, gloss) in stem_dic:
        cands = stem_dic[(obj, gloss)]
        kinds["stem"] = cands
    for kind, cands in kinds.items():
        if len(cands) == 1:
            abstract_id = next(iter(cands))
            concrete_id = cands[abstract_id]
            if abstract_id not in ids:
                log.warning(
                    f"identify_part: {obj} '{gloss}' is clearly the {kind} {abstract_id}. IDs: {ids}"
                )
            kinds[kind] = concrete_id
        for _id in ids:
            if _id in cands:
                kinds[kind] = cands[_id]
    if kinds:
        return kinds
    raise ValueError(f"Could not find any morph or stem {obj} '{gloss}'. IDs: {ids}")


# todo: this should only add inflectional values if they are in the gramm argument
def process_wordform(obj, gloss, lex_id, gramm, morpheme_ids, **kwargs):
    if gloss in ["***", "?", ""]:
        return None
    wf_id = humidify(f"{strip_form(obj)}-{gloss}", unique=False, key="wordforms")
    if wf_id in wf_dict:
        return wf_id
    if wf_id in ["pe-ess", "taro-say-ipfv"]:
        log.error(obj)
        log.error(gloss)
        log.error(kwargs)
    if morpheme_ids:
        if not isinstance(morpheme_ids, list):
            morpheme_ids = morpheme_ids.split(",")
        if "&" in lex_id:
            source_lex, process = lex_id.rsplit("&", 1)
            # print(source_lex, process)
            stem_id, source_id = resolve_productive_stem(
                source_lex, process, obj, gloss, get_pos(gramm)
            )
            if stem_id:
                if gloss in productive_stems[stem_id]["Gloss"]:
                    # todo: it would be great if I could figure out the positions of ANY productive stem in the wordform
                    wf_stems.append(
                        {
                            "ID": f"{wf_id}-deriv-stem",
                            "Index": [0, len(obj.split("-")) - 1],
                            "Stem_ID": stem_id,
                            "Wordform_ID": wf_id,
                        }
                    )
                else:
                    log.warning(
                        f"The form {obj} '{gloss}' contains the stem {productive_stems[stem_id]['Form']} '{', '.join(productive_stems[stem_id]['Gloss'])}'; can it know about its wordformstem?"
                    )
            if source_id:
                morpheme_ids.append(source_id)
            else:
                log.warning(f"{obj} '{gloss}'")
        else:
            stem_id = lexeme2stem(lex_id, obj, get_pos(gramm))
        # print(obj, gloss)
        for idx, (part, partgloss) in enumerate(zip(obj.split("-"), gloss.split("-"))):
            if partgloss == "***":
                continue
            if (part, partgloss) in tuple_lookup:
                parts = tuple_lookup[(part, partgloss)]
            else:
                parts = identify_part(part, partgloss, morpheme_ids)
                if not parts:
                    raise ValueError(part, partgloss)
            for kind, part_id in parts.items():
                if kind == "stem":
                    wf_stems.append(
                        {
                            "ID": f"{wf_id}-{idx}",
                            "Index": [idx],
                            "Stem_ID": part_id,
                            "Wordform_ID": wf_id,
                        }
                    )
                elif kind == "morph":
                    wf_morphs.append(
                        {
                            "ID": f"{wf_id}-{idx}",
                            "Index": idx,
                            "Morph_ID": part_id,
                            "Wordform_ID": wf_id,
                            "Gloss_ID": id_glosses(partgloss),
                        }
                    )
                    if part_id in morph_infl_dict and (
                        stem_id in list(df.stems["ID"]) or stem_id in productive_stems
                    ):
                        infl = morph_infl_dict[part_id]
                        inflections.append(
                            {
                                "ID": f"{wf_id}-{idx}-{infl}",
                                "Value_ID": infl,
                                "Wordformpart_ID": [f"{wf_id}-{idx}"],
                                "Stem_ID": stem_id,
                            }
                        )

    wf_dict[wf_id] = {
        "ID": wf_id,
        "Form": obj.replace("-", "").replace("∅", ""),
        "Parameter_ID": [gloss],
        "Language_ID": "yab",
        "Morpho_Segments": obj.split("-"),
        **kwargs,
    }
    return wf_id


wf_audios = []
f_audios = []
dic_forms = []
## Out-of-context wordforms
dic_wordforms = cread(UP_DIR / "../annotation/parsed_dictionary_wordforms.csv")
dic_wordforms.rename(columns={"Lexeme_ID": "Lexeme_IDs"}, inplace=True)
for wf in dic_wordforms.to_dict("records"):
    kwargs = {}
    if wf["Audio"]:
        filename = wf["Audio"].split("/")[-1]
        audio_path = WORD_AUDIO_PATH / filename
        if audio_path.is_file():
            if "=" not in wf["Gloss"]:
                kwargs["Media_ID"] = filename.replace(".wav", "")
                wf_audios.append(
                    {
                        "ID": humidify(filename, key="wf_audio", unique=True),
                        "Name": filename.replace(".wav", ""),
                        "Media_Type": "x/wav",
                        "Download_URL": f"audio/{filename}",
                    }
                )
            else:
                f_audios.append(
                    {
                        "ID": humidify(filename, key="wf_audio", unique=True),
                        "Name": filename.replace(".wav", ""),
                        "Media_Type": "x/wav",
                        "Download_URL": f"audio/{filename}",
                    }
                )

    if "=" in wf["Gloss"]:
        f_id = humidify(strip_form(wf["Analysis"]) + "-" + wf["Translation"][0])
        form_dic = {
            "ID": f_id,
            "Form": strip_form(wf["Analysis"]),
            "Parameter_ID": wf["Gloss"],
            "Media_ID": filename.replace(".wav", ""),
        }
        res = split_cliticized(wf)
        wf_ids = {
            process_wordform(
                gwf["Analysis"],
                gwf["Gloss"],
                gwf["Lexeme_IDs"],
                gwf["Gramm"],
                gwf["Morpheme_IDs"],
                Source=["muller2021yawarana"],
                Part_Of_Speech=gwf["POS"],
                **kwargs,
            ): gwf
            for gwf in res
        }
        form_dic["Wordform_ID"] = ",".join(wf_ids.keys())
        dic_forms.append(form_dic)
    else:
        process_wordform(
            wf["Analysis"],
            wf["Gloss"],
            wf["Lexeme_IDs"],
            wf["Gramm"],
            wf["Morpheme_IDs"],
            Source=["muller2021yawarana"],
            Part_Of_Speech=get_pos(wf["Gramm"]),
            Parameter_ID=wf["Translation"] or wf["Gloss"],
            **kwargs,
        )

## In-context wordforms

ex_audios = []
exampleparts = []
split_cols = ["Analyzed_Word", "Gloss", "Lexeme_IDs", "Gramm", "Morpheme_IDs"]


if args.full:
    df.examples = cread("raw/full_examples.csv")
else:
    df.examples = cread("raw/examples.csv")
df.examples["Language_ID"] = "yab"
df.examples["Primary_Text"] = df.examples["Primary_Text"].apply(lambda x: x.replace("#", ""))
df.examples = df.examples[~(df.examples["Primary_Text"] == "")]
df.examples["Part_Of_Speech"] = df.examples["Gramm"].apply(
    lambda y: "\t".join([get_pos(x) if get_pos(x) else "?" for x in y.split("\t")])
)
splitcol(df.examples, "Part_Of_Speech", sep="\t")

examples_with_audio = []
for col in split_cols:
    splitcol(df.examples, col, sep="\t")
for ex in df.examples.to_dict("records"):
    g_shift = 0  # to keep up to date with how many g-words there are in total
    for idx, (obj, gloss, stem_id, gramm, morpheme_ids) in enumerate(
        zip(*[ex[col] for col in split_cols])
    ):
        if "=" in gloss:
            f_id = humidify(strip_form(obj) + "-" + gloss)
            res = split_cliticized(
                {
                    "ID": f_id,
                    "Gramm": gramm,
                    "Analysis": obj,
                    "Gloss": gloss,
                    "Lexeme_IDs": stem_id,
                    "Morpheme_IDs": morpheme_ids,
                }
            )
            print(obj, gloss)
            wf_ids = {
                process_wordform(
                    gwf["Analysis"],
                    gwf["Gloss"],
                    gwf["Lexeme_IDs"],
                    gwf["Gramm"],
                    gwf["Morpheme_IDs"],
                    Part_Of_Speech=get_pos(gwf["Gramm"]),
                ): gwf
                for gwf in res
            }
            for wf_id, form in wf_ids.items():
                if wf_id and gloss != "?":
                    exampleparts.append(
                        {
                            "ID": f'{ex["ID"]}-{idx+g_shift}',
                            "Example_ID": ex["ID"],
                            "Wordform_ID": wf_id,
                            "Index": idx + g_shift,
                        }
                    )
                elif gloss != "***":
                    log.warning(
                        f"Unidentifiable wordform {obj} '{gloss}' in {ex['ID']}"
                    )
                g_shift += 1
            g_shift -= 1
        else:
            wf_id = process_wordform(
                obj,
                gloss,
                stem_id,
                gramm,
                morpheme_ids,
                Part_Of_Speech=get_pos(gramm),
            )
            if wf_id and gloss != "?":
                exampleparts.append(
                    {
                        "ID": f'{ex["ID"]}-{idx+g_shift}',
                        "Example_ID": ex["ID"],
                        "Wordform_ID": wf_id,
                        "Index": idx + g_shift,
                    }
                )
            elif gloss != "***":
                log.warning(f"Unidentifiable wordform {obj} '{gloss}' in {ex['ID']}")
    file_path = AUDIO_PATH / f'{ex["ID"]}.wav'
    if file_path.is_file():
        ex_audios.append(
            {
                "ID": ex["ID"],
                "Name": ex["ID"],
                "Media_Type": "audio/wav",
                "Download_URL": "audio/" + ex["ID"] + ".wav",
            }
        )
        examples_with_audio.append(ex["ID"])

# # glossed examples from FLEx database
# df.flexamples = cread("raw/flexamples.csv")
# df.flexamples["Language_ID"] = "yab"
# df.flexamples = df.flexamples[~(df.flexamples["ID"].isin(df.examples["ID"]))]
# df.flexamples.rename(columns={"gls_nl_phrase": "Speaker_ID"}, inplace=True)
# for col in ["Analyzed_Word", "Gloss"]:
#     df.flexamples[col] = df.flexamples[col].apply(lambda x: x.replace("\t=", "\t"))
#     df.flexamples[col] = df.flexamples[col].apply(lambda x: x.replace("\t=", "\t"))
#     df.flexamples[col] = df.flexamples[col].apply(lambda x: x.replace("==", "="))
#     df.flexamples[col] = df.flexamples[col].apply(lambda x: x.split("\t"))

# if args.full:
#     df.flexamples = df.flexamples[
#         [
#             "ID",
#             "Language_ID",
#             "Primary_Text",
#             "Analyzed_Word",
#             "Gloss",
#             "Translated_Text",
#             "Text_ID",
#             "Record_Number",
#             "Speaker_ID",
#         ]
#     ]

#     cache = SimpleNamespace()
#     a = YawaranaAnalyzer()
#     a.load_grammar()
#     if Path("wf_cache.json").is_file():
#         cache.wordforms = jsonlib.load("wf_cache.json")
#     else:
#         cache.wordforms = {}

#     def process_flexample(ex):
#         g_shift = 0  # to keep up to date with how many g-words there are in total
#         for idx, obj in enumerate(ex["Analyzed_Word"]):
#             if obj == "":
#                 continue
#             if obj in cache.wordforms:
#                 wf = cache.wordforms[obj]
#             else:
#                 anas = a.analyze_words(strip_form(obj))
#                 if len(anas) > 1 or anas[0].wfGlossed == "":
#                     continue
#                 wf = anas[0].to_json()
#                 cache.wordforms[obj] = wf
#             for g_word_idx, (real_obj, real_gloss) in enumerate(
#                 zip(wf["wfGlossed"].split("="), wf["gloss"].split("="))
#             ):
#                 real_idx = idx + g_word_idx + g_shift
#                 wf_id = process_wordform(
#                     real_obj,
#                     real_gloss,
#                     wf["lemma"],
#                     wf["gramm"],
#                     wf["id"],
#                     Part_Of_Speech=get_pos(wf["gramm"]),
#                 )
#                 if wf_id:
#                     exampleparts.append(
#                         {
#                             "ID": f'{ex["ID"]}-{real_idx}',
#                             "Example_ID": ex["ID"],
#                             "Wordform_ID": wf_id,
#                             "Index": real_idx,
#                         }
#                     )
#                 else:
#                     print(real_obj, real_gloss)
#                     exit()

#             g_shift += g_word_idx
#         file_path = AUDIO_PATH / f'{ex["ID"]}.wav'
#         if file_path.is_file():
#             ex_audios.append(
#                 {
#                     "ID": ex["ID"],
#                     "Name": ex["ID"],
#                     "Media_Type": "audio/wav",
#                     "Download_URL": "audio/" + ex["ID"] + ".wav",
#                 }
#             )
#             examples_with_audio.append(ex["ID"])

#     tic = time.perf_counter()

#     df.flexamples.apply(process_flexample, axis=1)
#     jsonlib.dump(cache.wordforms, "wf_cache.json")

#     toc = time.perf_counter()
#     df.flexamples.rename(
#         columns={"Part": "Record_Number", "gls_nl_phrase": "Speaker_ID"}, inplace=True
#     )
#     print(f"Parsed examples in {toc - tic:0.4f} seconds")
#     join_dfs("examples", "examples", "flexamples")
# else:
#     doc_ex = load("manex.txt").split("\n")
#     for mdfile in Path(
#         "/home/florianm/Dropbox/research/cariban/yawarana/yawarana-pld-sketch/content"
#     ).glob("*.md"):
#         with open(mdfile, "r", encoding="utf-8") as f:
#             for ex_ids in re.findall(r"\[ex\]\((.*?)\)", f.read()):
#                 for hit in ex_ids.split(","):
#                     doc_ex.extend(hit.split("?"))
#     df.flexamples = df.flexamples[df.flexamples["ID"].isin(doc_ex)]
#     df.flexamples.rename(
#         columns={"Part": "Record_Number", "gls_nl_phrase": "Speaker_ID"}, inplace=True
#     )
#     join_dfs("examples", "examples", "flexamples")


# todo: remove this at some point
speaker_fix = {
    "IrDI": "IrDi",
    "MaFlo": "MaFl",
    "IrDi x": "IrDi",
    "AmGu’": "AmGu",
    "CaME": "CaMe",
    "GrME": "GrMe",
}
df.examples["Speaker_ID"] = df.examples["Speaker_ID"].replace(speaker_fix)
df.examples["Speaker_ID"] = df.examples["Speaker_ID"].apply(
    lambda x: humidify(x, key="speakers")
)

found_texts = set(list(df.examples["Text_ID"]))

texts = {}
text_list = cread("../yawarana_corpus/text_metadata.csv")
with open("../yawarana_corpus/text_metadata.yaml", "r", encoding="utf-8") as file:
    text_metadata = yaml.load(file, Loader=yaml.SafeLoader)
for text in text_list.to_dict("records"):
    if text["id"] in text_metadata:
        text.update(**text_metadata[text["id"]])
    if text["id"] in found_texts:
        texts[text["id"]] = text

df.texts = []
for text_id, text_data in texts.items():
    metadata = {x: text_data[x] for x in ["genre", "tags"] if x in text_data}
    df.texts.append(
        {
            "ID": text_id,
            "Name": text_data["title_es"],
            "Description": text_data["summary"],
            "Comment": "; ".join(text_data.get("comments", [])),
            "Type": text_data["genre"],
            "Metadata": metadata,
        }
    )


df.wordforms = pd.DataFrame.from_dict(wf_dict.values()).set_index("ID", drop=False)
df.wordforms = list(wf_dict.values())
df.wordformstems = pd.DataFrame.from_dict(wf_stems)
df.wordformparts = pd.DataFrame.from_dict(wf_morphs)
df.inflections = inflections
df.exampleparts = exampleparts

# # Multiword forms
# pn_v_forms = cread(
#     "/home/florianm/Dropbox/research/cariban/yawarana/yawarana_corpus/annotation/output/multiword.csv"
# )
# pn_v_forms.rename(columns={"Gloss": "Parameter_ID"}, inplace=True)
# pn_v_forms = pd.concat([pn_v_forms, pd.DataFrame.from_dict(dic_forms)])

pn_v_forms = pd.DataFrame.from_dict(dic_forms)
pn_v_forms["Language_ID"] = "yab"
pn_v_forms = pn_v_forms.fillna("")
formparts = []


def add_formparts(rec):
    for idx, wfid in enumerate(rec["Wordform_ID"].split(",")):
        formparts.append(
            {
                "ID": f'{rec["ID"]}-{idx}',
                "Form_ID": rec["ID"],
                "Wordform_ID": wfid,
                "Index": idx,
            }
        )


# pn_v_forms.apply(add_formparts, axis=1)
# df.formparts = formparts
df.forms = pn_v_forms

# pn_v_infl = cread(
#     "/home/florianm/Dropbox/research/cariban/yawarana/yawarana_corpus/annotation/output/inflections.csv"
# )


def resolve_wf_data(rec):

    partcands = df.wordformparts[
        (df.wordformparts["Wordform_ID"] == rec["Wordform_ID"])
        & (df.wordformparts["Index"] == rec["Part_Index"])
    ]
    stemcands = df.wordformstems[
        (df.wordformstems["Wordform_ID"] == rec["Lexeme_Wordform"])
    ]
    if len(partcands) == 1:
        wfpart = partcands.iloc[0]["ID"]
    else:
        wfpart = ""
        # print("part", rec["Wordform_ID"])
    if len(stemcands) == 1:
        wfstem = stemcands.iloc[0]["Stem_ID"]
    else:
        wfstem = ""
        # print("stem", rec["Lexeme_Wordform"])
    rec["Stem_ID"] = wfstem
    rec["Wordformpart_ID"] = [wfpart]
    return rec


# df.pnvinfl = pn_v_infl.apply(resolve_wf_data, axis=1)
# df.pnvinfl = df.pnvinfl[df.pnvinfl["Stem_ID"] != ""]
df.inflections = pd.DataFrame.from_dict(df.inflections)

# combine dataframes
df.derivations = pd.DataFrame.from_dict(derivations.values())
df.derivations.fillna("", inplace=True)
df.stemparts = pd.DataFrame.from_dict(stemparts)

df.stemparts["Gloss_ID"] = df.stemparts["Gloss"].apply(id_glosses)
splitcol(df.derivations, "Stempart_IDs")
join_dfs("morphs", "morphs", "bound_root_morphs")
join_dfs("morphemes", "morphemes", "bound_roots")
# join_dfs("inflections", "inflections", "pnvinfl")

df.productive_lexemes = pd.DataFrame.from_dict(productive_lexemes.values())
df.productive_lexemes["Language_ID"] = "yab"
join_dfs("lexemes", "lexemes", "productive_lexemes")

df.productive_stems = pd.DataFrame.from_dict(productive_stems.values())
df.productive_stems["Language_ID"] = "yab"


join_dfs("stems", "stems", "productive_stems")


df.examples["Media_ID"] = df.examples.apply(
    lambda x: x["ID"] if x["ID"] in examples_with_audio else "", axis=1
)


df.lexemes.rename(columns={"POS": "Part_Of_Speech"}, inplace=True)
df.morphs["Segments"] = df.morphs["Form"].apply(strip_form).apply(tokenize)

df.derivationalprocesses = cread("etc/derivationalprocesses.csv")
df.derivationalprocesses["Language_ID"] = "yab"


## POS
df.partsofspeech = cread("etc/pos.csv")
df.partsofspeech["Language_ID"] = "yab"
## Texts
## Contributors
df.contributors = cread("etc/contributors.csv")
df.contributors["Name"] = df.contributors.apply(
    lambda x: x["First"] + " " + x["Given"], axis=1
)
## Inflection
values = cread("etc/values.csv")
values["Gloss_ID"] = values["Gloss"].apply(lambda x: id_glosses(x, sep=""))
df.inflectionalvalues = values
df.inflectionalcategories = cread("etc/categories.csv")
## Media (& refs)
df.media = wf_audios + ex_audios

phonemes["Language_ID"] = "yab"
df.phonemes = phonemes.rename(columns={"IPA": "Name"})
## Tags?
df.languages = [
    {
        "ID": "yab",
        "Name": "Yawarana",
        "Longitude": -54.7457,
        "Latitude": 1.49792,
        "Glottocode": "yaba1248",
    }
]

df.glosses = [
    {"ID": gloss_id, "Name": gloss} for gloss, gloss_id in get_values("glosses").items()
]
## Compile: meanings
# Writing the CLDF dataset
cldf_names = {}
for component_filename in pkg_path("components").iterdir():
    component = jsonlib.load(component_filename)
    cldf_names[component["url"].replace(".csv", "")] = str(
        component_filename.name
    ).replace(
        MD_SUFFIX, ""
    )  # "examples": Example

additional_columns = {
    "wordforms": ["Media_ID"],
    "forms": ["Media_ID"],
    "examples": [
        {
            "name": "Media_ID",
            "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#mediaReference",
        },
        {"name": "Part_Of_Speech", "datatype": "string", "separator": "\t"},
        {
            "name": "Original_Translation",
            "required": False,
            "dc:extent": "singlevalued",
            "dc:description": "The original translation of the example text.",
            "datatype": "string",
        },
    ],
}
spec = CLDFSpec(dir="cldf", module="Generic", metadata_fname="metadata.json")
if args.full:
    spec = CLDFSpec(dir="full_cldf", module="Generic", metadata_fname="metadata.json")
with CLDFWriter(spec) as writer:
    # metadata

    writer.cldf.properties.setdefault("rdf:ID", "yawarana-corpus")
    writer.cldf.properties.setdefault("dc:title", "Yawarana corpus")
    writer.cldf.properties[
        "dc:license"
    ] = "https://creativecommons.org/licenses/by-sa/4.0/"
    writer.cldf.properties.setdefault(
        "dc:bibliographicCitation",
        "Cáceres, Natalia and Matter, Florian and Mattéi-Müller, Marie-Claude and Gildea, Spike, 2023. Yawarana corpus [CLDF dataset].",
    )
    writer.cldf.properties.setdefault(
        "dc:description",
        open("etc/description.md", "r").read(),
    )

    tables = vars(df)
    for table in ldd_tables + pld_tables:
        handle = table["url"].replace(".csv", "")
        if handle in tables:
            log.debug(f"Writing {handle}")
            writer.cldf.add_component(table)
            for col in additional_columns.get(handle, []):
                writer.cldf.add_columns(table["url"], col)
            data = tables.pop(handle)
            if not isinstance(data, list):
                data = data.to_dict("records")
            for rec in data:
                writer.objects[table["url"]].append(rec)

    # now only native CLDF components should be left over
    for handle, data in tables.items():  # examples.csv
        if handle not in cldf_names:
            log.warning(f"Leftover dataframe {handle}")
            continue
        writer.cldf.add_component(cldf_names[handle])
        for col in additional_columns.get(handle, []):
            writer.cldf.add_columns(cldf_names[handle], col)
        if not isinstance(data, list):
            data = data.to_dict("records")
        for rec in data:
            writer.objects[cldf_names[handle]].append(rec)

    add_columns(writer.cldf)
    found_refs = jsonlib.load("etc/refs.json")
    bib = pybtex.database.parse_file("etc/car.bib", bib_format="bibtex")
    car_sources = [
        Source.from_entry(k, e) for k, e in bib.entries.items() if k in found_refs
    ]
    bib2 = pybtex.database.parse_file("etc/misc.bib", bib_format="bibtex")
    misc_sources = [Source.from_entry(k, e) for k, e in bib2.entries.items()]
    writer.cldf.add_sources(*car_sources)
    writer.cldf.add_sources(*misc_sources)

    ds = writer.cldf
    add_keys(ds)


# # use cffconvert to easily create citation string for CLDF metadata
# # todo: fix and use this for repo
# citation = create_citation(infile="CITATION.cff", url=None)
# validate_or_write_output(
#     outputformat="apalike",
#     citation=citation,
#     outfile="/tmp/citation.txt",
#     validate_only=False,
# )
# with open("/tmp/citation.txt", "r", encoding="utf-8") as f:
#     citation = f.read().strip()
# log.info(f"Citation: {citation}")

ds.validate(log=log)
sys.exit()


bad_texts = [
    "ctooroanpe"
]  # texts that should never ever make it into the corpus (as one piece; individual sentences can appear in documents)
examples = examples[~(examples["Text_ID"].isin(bad_texts))]
