# Prelude
## Import
import argparse
import logging
import re
import sys
import time
from itertools import product
from pathlib import Path
from types import SimpleNamespace

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
from morphinder import identify_complex_stem_position
from pylingdocs.cldf import tables as pld_tables
from pylingdocs.preprocessing import preprocess_cldfviz
from segments import Profile, Tokenizer
from uniparser_yawarana import YawaranaAnalyzer
from writio import load
from yawarana_helpers import (
    find_detransitivizer,
    glossify,
    strip_form,
    trim_dic_suff,
)
from pylacoan.helpers import get_pos as _get_pos
from uniparser_yawarana import pos_list

def get_pos(gramm):
    return _get_pos(gramm, pos_list)


log = get_colorlog(__name__, sys.stdout, level=logging.INFO)

#################### PART 0: CONFIG ####################
# the cell-internal separator used in all sorts of tables
SEP = "; "
# derivations and bound roots
UP_DIR = Path("/home/florianm/Dropbox/development/uniparser-yawarana/data")
# all audio files
AUDIO_PATH = Path(
    "/home/florianm/Dropbox/research/cariban/yawarana/corpus/audio"
)
# wordform audio files
WORD_AUDIO_PATH = AUDIO_PATH / "wordforms"


def is_name(string):
    # identify personal names
    if isinstance(string, list):
        string = string[0]
    if re.match("^[A-Z]\.$", string):
        return True
    return False


def splitcol(df, col, sep="; "):
    df[col] = df[col].apply(lambda x: x.split(sep))


def cread(filename):
    # use pandas to read csvs and not use NaN
    # use ID as index, split (inherently multivalued) translations
    df = pd.read_csv(filename, encoding="utf-8", keep_default_na=False)
    if "Translation" in df.columns:
        splitcol(df, "Translation")
    if "ID" in df.columns:
        df.set_index("ID", drop=False)
    return df


# turn glosses into gloss IDs
def id_glosses(gloss, sep=None):
    if isinstance(gloss, list):
        return [id_glosses(x) for x in gloss]
    res = [humidify(g, key="glosses") for g in re.split(r"\.\b", gloss)]
    if sep is not None:
        return sep.join(res)
    return res


# cast to list
def split_if_not_list(s, sep=","):
    if not isinstance(s, list):
        return s.split(sep)
    return s


def splitform(s):
    return s.split("-")


def create(full=False):
    start_time = time.perf_counter()

    # for tokenizing into segments
    phonemes = cread("etc/phonemes.csv")
    prf = Profile(*phonemes.to_dict("records"))
    t = Tokenizer(profile=prf)

    def tokenize(s):
        tokens = t(s, column="IPA").split(" ")
        if "�" in tokens:
            return []
        return tokens

    # time keeping purposes
    def timer(msg):
        toc = time.perf_counter()
        print(f"{msg}: {toc - start_time:0.4f} seconds")

    def ipaify(s):
        return t(s, column="IPA", segment_separator="", separator=" ")

    def add_to_morph_dic(morph):
        for g in morph["Translation"]:
            morph_tuple = (f'{morph["Form"].strip("-")}', glossify(g))
            morph_dic.setdefault(morph_tuple, {})
            morph_dic[morph_tuple][morph["Morpheme_ID"]] = morph["ID"]

    # print current dataframes
    def debug_dfs(key=None):
        for k, data in vars(df).items():
            if key and key != k:
                continue
            print(data)
            print(k)
        sys.exit()

    # combine several dataframes in the namespace
    def join_dfs(name, *keys):
        setattr(df, name, pd.concat([vars(df)[key] for key in keys]).fillna(""))
        for key in keys:
            if key != name:
                delattr(df, key)

    def idify(data, columns, key):
        columns = [(x, lambda y: y) if not isinstance(x, tuple) else x for x in columns]
        def recid(x):
            vals = []
            for col, func in columns:
                vals.append(func(x[col][0]) if isinstance(x[col], list) else func(x[col]))
            return "-".join(vals)

        return data.apply(lambda x: humidify(recid(x), key=key, unique=True), axis=1)

    def add_morph_infl(rec):
        if rec["Value"]:
            morph_infl_dict[rec["ID"]] = rec["Value"]

    def add_to_proc_dict(x):
        if x["Parameter_ID"] == ["DETRZ"]:
            process = "detrz"
        else:
            process = x["ID"]
        deriv_proc_dic[x["ID"]] = {
            "Form": x["Name"],
            "Gloss": x["Translation"],
            "Process": process,
        }

    # dictionary of derivational morphs for later enjoyment
    deriv_proc_dic = {}
    # keep a running dict of all morphs, used for identifying parts of forms and stems
    morph_dic = {}
    # namespace for storing dataframes
    df = SimpleNamespace()
    # mapping morpheme IDs to inflectional values
    morph_infl_dict = {}

    #################### PART 1.1: SIMPLE LEXICAL DATA ####################
    # load inflectional, derivational and "misc" morph(eme)s
    for kind in [
        "derivation",
        "inflection",
        "misc",
    ]:  # different manually entered morph(eme)s
        morphemes = cread(f"etc/{kind}_morphemes.csv")
        morphs = cread(f"etc/{kind}_morphs.csv")
        if (
            kind == "inflection"
        ):  # copy inflectional values from the morpheme to the morph table
            morphemes.apply(add_morph_infl, axis=1)
            morphs["Value"] = morphs["Morpheme_ID"].map(morph_infl_dict).fillna("")
            morphs.apply(add_morph_infl, axis=1)
        morphs["Name"] = morphs["Form"]  # todo: necessary?
        morphs["Language_ID"] = "yab"
        morphemes["Language_ID"] = "yab"
        morphemes["Parameter_ID"] = morphemes["Translation"]  # todo: necessary?
        morph_meanings = dict(zip(morphemes["ID"], morphemes["Translation"]))
        morphs["Translation"] = morphs["Morpheme_ID"].map(morph_meanings)
        morphs["Parameter_ID"] = morphs["Translation"]
        morphs.apply(add_to_morph_dic, axis=1)
        morphs["Gloss"] = morphs["Translation"].apply(glossify)
        setattr(df, f"{kind}_morphs", morphs)
        setattr(df, f"{kind}_morphemes", morphemes)

    df.derivation_morphemes.apply(add_to_proc_dict, axis=1)

    # bound roots; they don't occur as stems
    df.bound_roots = cread(UP_DIR / "bound_roots.csv")
    df.bound_roots["Language_ID"] = "yab"
    df.bound_roots["Parameter_ID"] = df.bound_roots["Translation"]
    df.bound_roots["Gloss"] = df.bound_roots["Translation"].apply(glossify)
    df.bound_roots["ID"] = idify(
        df.bound_roots, ["Name", "Translation"], key="morphemes"
    )
    splitcol(df.bound_roots, "Form")
    df.bound_root_morphs = df.bound_roots.explode("Form")
    df.bound_root_morphs["Morpheme_ID"] = df.bound_root_morphs["ID"]
    df.bound_root_morphs["Name"] = df.bound_root_morphs["Form"]
    df.bound_root_morphs["ID"] = idify(
        df.bound_root_morphs, ["Name", "Translation"], key="morphs"
    )

    # enriched LIFT export from MCMM
    dic = pd.read_csv(
        "../dictionary/annotated_dictionary.csv",
        keep_default_na=False,
    )
    dic_roots = dic[dic["Translation_Root"] != ""].copy()  # keep only roots
    dic_roots.rename(columns={"Translation_Root": "Translation"}, inplace=True)
    dic_roots = dic_roots.apply(
        lambda x: trim_dic_suff(x, SEP), axis=1
    )  # cut off lemma-forming suffixes
    splitcol(dic_roots, "Translation")
    dic_roots["Gloss"] = dic_roots["Translation"].apply(glossify)
    # retrieve variants from other column
    dic_roots["Form"] = dic_roots.apply(
        lambda x: SEP.join(list(x["Form"].split(SEP) + x["Variants"].split(SEP))).strip(
            SEP
        ),
        axis=1,
    )

    # manually entered roots
    manual_roots = cread("etc/manual_roots.csv")
    manual_roots["Gloss"] = manual_roots["Translation"]

    # build a dataframe containing root morphemes
    df.roots = pd.concat([dic_roots, manual_roots])
    df.roots["Language_ID"] = "yab"
    # process roots
    for split_col in ["Form"]:
        splitcol(df.roots, split_col)
    df.roots["Name"] = df.roots["Form"].apply(
        lambda x: x[0]
    )  # main allomorph is label for root
    # create IDs
    df.roots["temp"] = df.roots["ID"]
    df.roots["ID"] = idify(df.roots, ["Name", "Gloss"], key="morpheme")
    df.roots["ID"] = df.roots.apply(lambda x: x["ID"] if not x["temp"] or len(x["temp"]) > 20 else x["temp"],axis=1)
    df.roots["Parameter_ID"] = df.roots["Translation"]
    df.roots["Gloss"] = df.roots["Gloss"].apply(glossify)
    df.roots = df.roots[
        [
            "ID",
            "Language_ID",
            "Name",
            "Form",
            "Translation",
            "Gloss",
            "Parameter_ID",
            "POS",
            "Comment",
            "Tags"
        ]
    ]

    # roots["Description"] = roots["Parameter_ID"] # todo: needed?
    # only roots with these POS are assumed to be treated as stems/lexemes (i.e., take inflectional morphology)
    stem_pos_list = ["vt", "vi", "n", "postp", "pn", "adv"]
    df.root_lex = df.roots[df.roots["POS"].isin(stem_pos_list)].copy()

    df.root_lex = df.root_lex[~(df.root_lex["Translation"].apply(is_name))]

    df.stems = df.root_lex.explode("Form")
    df.root_lex["Main_Stem"] = df.root_lex["ID"]
    df.stems["Lexeme_ID"] = df.stems["ID"]
    df.stems["ID"] = idify(df.stems, ["Form", "Gloss"], key="stems")

    # all roots are also morphs
    df.root_morphs = df.roots.explode("Form")
    df.root_morphs["Morpheme_ID"] = df.root_morphs["ID"]
    df.root_morphs["ID"] = idify(df.root_morphs, ["Form", "Gloss"], key="morphs")
    df.root_morphs.apply(add_to_morph_dic, axis=1)
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

    #################### PART 1.2: COMPLEX LEXICAL DATA ####################
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

    complicated_stems = []  # not fully parsable stems
    derived_parts = {}  # mapping stem forms to stemparts

    def get_stempart_cands(rec, part, process):
        cands = df.morphs[df.morphs["Form"].str.strip("-") == part]
        if len(cands) > 2 and process == "kavbz":
            cands = cands[cands["ID"] == "kavbz"]
        elif len(cands) > 2 and process == "tavbz":
            cands = cands[cands["ID"] == "tavbz"]
        elif len(cands) > 2 and process == "macaus":
            cands = cands[cands["ID"] == "macaus"]
        elif (
            len(cands) > 1
            and process == "detrz"
            and "DETRZ" in list(cands["Parameter_ID"].apply(lambda x: x[0]))
        ):
            cands = cands[cands["Parameter_ID"].apply(lambda x: x == ["DETRZ"])]
        elif "DETRZ" in list(cands["Parameter_ID"].apply(lambda x: x[0])):
            cands = cands[cands["Parameter_ID"].apply(lambda x: x == ["DETRZ"])]
        if len(cands) == 0:
            # is the base a bound root?
            bound_root_base = df.bound_root_morphs[
                (df.bound_root_morphs["ID"] == rec["Base_Stem"])
                | (df.bound_root_morphs["ID"] == rec.get("Base_Root"))
                | (df.bound_root_morphs["Form"] == part)
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
            stem_id = humidify(strip_form(form) + "-" + rec["Translation"][0])
            parts = re.split(r"-|\+", form)
            new_form = []
            processes = []
            for part in parts:
                if part in derived_parts:
                    for subpart in derived_parts[part]:
                        new_form.append(subpart["Part"])
                        if subpart["Morph_ID"] in deriv_proc_dic:
                            processes.append(subpart["Morph_ID"])
                        else:
                            processes.append(process)
                else:
                    new_form.append(part)
                    processes.append(process)
            form = "+".join(new_form)
            parts = re.split(r"-|\+", form)
            form = strip_form(form)
            derived_parts[form] = []
            # print(parts)
            for idx, part in enumerate(parts):
                if is_name(part):
                    continue
                cands = get_stempart_cands(rec, part, processes[idx])
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
                    derived_parts[form].append(
                        {"Morph_ID": hit["ID"], "Index": idx, "Part": part}
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
                    complicated_stems.append(rec.copy())
                    log.warning(f"Could not find stempart {part} for stem {form}")
                    # exit()
                elif len(cands) > 1:
                    log.warning(f"Unable to disambiguate stem parts for {rec['Form']}")
                    print(cands)
                    # exit()
            rec["Morpho_Segments"].append(" ".join(parts))
        rec["Gloss"] = glossify(rec["Translation"], segmented=True)
        rec["Form"] = [x.replace("+", "") for x in rec["Form"]]
        return rec

    # add columns ID, Morpho_Segments, Gloss
    tavbz = tavbz.apply(lambda x: process_stem(x, "tavbz"), axis=1)
    kavbz = kavbz.apply(lambda x: process_stem(x, "kavbz"), axis=1)
    macaus = macaus.apply(lambda x: process_stem(x, "macaus"), axis=1)
    detrz = detrz.apply(lambda x: process_stem(x, "detrz"), axis=1)
    miscderiv = miscderiv.apply(lambda x: process_stem(x, None), axis=1)

    df.derived_lex = pd.concat([tavbz, kavbz, detrz, macaus, miscderiv])
    df.derived_lex["Language_ID"] = "yab"
    df.derived_lex["Lexeme_ID"] = df.derived_lex["ID"]
    df.derived_lex["Parameter_ID"] = df.derived_lex["Translation"]
    df.derived_lex["Name"] = df.derived_lex["Form"].apply(lambda x: strip_form(x[0]))

    df.derived_stems = df.derived_lex.explode(["Form", "Morpho_Segments"])
    df.derived_lex["Main_Stem"] = df.derived_lex["ID"]
    df.derived_stems["Lexeme_ID"] = df.derived_stems["ID"]
    df.derived_stems["ID"] = idify(df.derived_stems, [("Form", lambda x: x.replace("-", "")), "Gloss"], key="stems")
    df.stems["Morpho_Segments"] = df.stems["Form"]
    join_dfs("stems", "stems", "derived_stems")

    join_dfs("lexemes", "root_lex", "derived_lex")
    df.lexemes = df.lexemes.set_index("ID", drop=False)
    df.stems["Gloss_ID"] = df.stems["Gloss"].apply(id_glosses)
    df.stems["Name"] = df.stems["Form"].apply(strip_form)
    df.stems["Description"] = df.stems["Translation"]
    df.stems["Language_ID"] = "yab"
    df.stems["Segments"] = df.stems["Name"].apply(tokenize)
    splitcol(df.stems, "Morpho_Segments", sep=" ")

    stem_tuples = {}  # a dict mapping object-gloss tuples to stem IDs

    def add_to_stem_tuplest(stem):
        for g in stem["Gloss"]:
            stem_tuple = (f'{stem["Name"].strip("-")}', g)
            stem_tuples.setdefault(stem_tuple, {})
            stem_tuples[stem_tuple][stem["Lexeme_ID"]] = stem["ID"]

    df.stems.apply(add_to_stem_tuplest, axis=1)

    #################### PART 2: ATTESTED DATA ####################
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
    productive_lexemes = {}
    tuple_lookup = {}

    deriv_source_pos = {"anonmlz": ["adv", "postp"], "keprop": ["n"], "ninmlz": ["vt"]}

    def build_productive_stem(source_stem, process, obj):
        if process not in deriv_proc_dic:
            log.warning(f"Unidentifiable process: {process}")
            return None, None, None
        suff_form = deriv_proc_dic[process]["Form"]
        for part in splitform(obj):
            cands = get_stempart_cands(source_stem, part, process)
            if len(cands) == 1 and cands.iloc[0]["Morpheme_ID"] == process:
                suff_form = cands.iloc[0]["Form"]
        stem_form = f"{source_stem.Form}-{suff_form}".replace("--", "-")
        stem_glosses = [
            f"{x}-{y}"
            for x, y in list(
                product(source_stem.Gloss, deriv_proc_dic[process]["Gloss"])
            )
        ]
        stem_id = humidify(f"{strip_form(stem_form)}-{stem_glosses[0]}", key="stems")
        log.debug(
            f"The stem {stem_form} '{', '.join(stem_glosses)}' ({stem_id}) is derived from {source_stem.Form} '{', '.join(source_stem.Gloss)}' ({source_stem.ID}) with {deriv_proc_dic[process]['Form']} ({process})"
        )
        return stem_form, stem_glosses, stem_id

    semi_inflections = [
        "rinmlz",
        "tojpepurp",
        "sapenmlz",
        "jpenmlz",
        "septcp",
        "tanecncs",
        "neinf",
    ]  # todo: should these receive some different treatment?

    def resolve_productive_stem(lex_id, obj, gloss, pos):
        lex, process = lex_id.rsplit("&", 1)
        log.debug(
            f"Uniparser lexeme: {lex_id}\nactual wordform: {obj} '{gloss}'\nuniparser process: {process}\nlexeme form: {lex}"
        )
        if "&" in lex:  # a productively derived stem, as put out by uniparser-morph
            stem_id, sub_lex_id = resolve_productive_stem(lex, obj, gloss, pos)
            cands = df.lexemes[df.lexemes["ID"] == sub_lex_id]
        else:
            cands = df.lexemes[df.lexemes["Name"] == lex]
        if len(cands) > 1:
            cands = cands[
                cands.apply(
                    lambda x: len(set(set(x["Gloss"]) & set(gloss.split("-")))) > 0,
                    axis=1,
                )
            ]
            print("reduced cands:")
            print(cands)
        if len(cands) == 1:
            source_lex = cands.iloc[0]
        elif len(cands) > 1:
            log.warning(f"Could not disambiguate stem {lex}\n{cands.to_string()}")
            # exit()
        elif len(cands) == 0:
            log.warning(f"Found no candidates for stem {lex_id}")
            # exit()
            return None, None
        stem_cands = df.stems[df.stems["Lexeme_ID"] == source_lex.name]
        if len(stem_cands) > 1:
            stem_cands = stem_cands[stem_cands["Form"].isin(obj.split("-"))]
        if len(stem_cands) > 1:
            log.warning(
                f"Ambiguity in resolving productive derivation {obj}&{process}:"
            )
            print(stem_cands)
            return None, None
        if len(stem_cands) == 0:
            log.warning(
                f"Unable to resolve productive derivation {obj}&{process} in form {obj} '{gloss}'."
            )
            # exit()
            return None, None
        if "&" not in lex:
            source_stem = stem_cands.iloc[0]
            # todo: do these need to find their way back in?
            # if len(cands) == 0:
            #     cands = df.bound_root_morphs[df.bound_root_morphs["Form"] == obj]
            # if len(cands) > 1 and process in deriv_source_pos:
            #     cands = cands[cands["POS"].isin(deriv_source_pos[process])]
            if process in semi_inflections:
                print("semi_inflection", process, "only gets", source_stem["ID"], source_stem["Lexeme_ID"])
                # print(stem_cands)
                # print("src", source_stem)
                # print("obj", obj)
                # print("what now?")
                # exit()
                # new_stem_form, new_stem_gloss, new_stem_id = build_productive_stem(
                #     source_stem, process, obj
                # )
                return source_stem["ID"], source_stem["Lexeme_ID"]
            else:
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
                parsed_stem["Lexeme_ID"] = new_stem_id
                productive_stems[new_stem_id] = parsed_stem
            return new_stem_id, source_stem.Lexeme_ID
        else:
            return stem_id, sub_lex_id

    lex_stem_tuples = {}

    def lexeme2stem(lex, obj, pos):
        if (lex, obj) in lex_stem_tuples:
            return lex_stem_tuples[(lex, obj)]
        cands = df.stems[df.stems["Lexeme_ID"] == lex]
        if len(cands) > 1:
            cands = cands[cands["Form"].isin(splitform(obj))]
        if len(cands) == 0:
            if pos in stem_pos_list:
                log.warning(
                    f"lexeme2stem: could not identify stem for lexeme {lex} in form {obj}."
                )
            lex_stem_tuples[(lex, obj)] = lex
            return lex
        elif len(cands) == 1:
            stem_id = cands.iloc[0]["ID"]
            lex_stem_tuples[(lex, obj)] = stem_id
            return stem_id
        else:
            log.warning(
                f"lexeme2stem: could not resolve stem for lexeme {lex} in form {obj}"
            )
            lex_stem_tuples[(lex, obj)] = lex
            return lex

    def identify_part(obj, gloss, ids):
        kinds = {}
        if (obj, gloss) in morph_dic:
            cands = morph_dic[(obj, gloss)]
            kinds["morph"] = cands
        if (obj, gloss) in stem_tuples:
            cands = stem_tuples[(obj, gloss)]
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
        raise ValueError(
            f"Could not find any morph or stem {obj} '{gloss}'. IDs: {ids}"
        )

    # todo: this should only add inflectional values if they are in the gramm argument
    def process_wordform(obj, gloss, lex_id, gramm, morpheme_ids, **kwargs):
        log.debug(f"processing wordform {obj} '{gloss}'")
        if gloss in ["***", "?", ""]:
            return None
        wf_id = humidify(f"{strip_form(obj)}-{gloss}", unique=False, key="wordforms")
        if wf_id in wf_dict:
            return wf_id
        if morpheme_ids:
            if not isinstance(morpheme_ids, list):
                morpheme_ids = morpheme_ids.split(",")
            if "&" in lex_id:
                stem_id, source_id = resolve_productive_stem(
                    lex_id, obj, gloss, get_pos(gramm)
                )
                if stem_id:
                    if stem_id in productive_stems:
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
                            stemform = productive_stems[stem_id]["Form"][0]
                            if stemform in obj:
                                wf_stems.append(
                                    {
                                        "ID": f"{wf_id}-deriv-stem",
                                        "Index": identify_complex_stem_position(
                                            obj, stemform
                                        ),
                                        "Stem_ID": stem_id,
                                        "Wordform_ID": wf_id,
                                    }
                                )
                            else:
                                log.warning(
                                    f"The form {obj} '{gloss}' contains the stem {stemform} '{', '.join(productive_stems[stem_id]['Gloss'])}'; can it know about its wordformstem?"
                                )
                                # exit()
                else:
                    log.error(f"Could not find stem ID for wordform {obj} '{gloss}")
                if source_id:
                    morpheme_ids.append(source_id)
                else:
                    log.warning(
                        f"Unable to find derivational source for {obj} '{gloss}'"
                    )
                    # exit()
            elif "+" in lex_id:
                print(
                    "UH OH",
                    "lex_id",
                    lex_id,
                    "obj",
                    obj,
                    "gloss",
                    gloss,
                    get_pos(gramm),
                )
                exit()
            else:
                stem_id = lexeme2stem(lex_id, obj, get_pos(gramm))
            for idx, (part, partgloss) in enumerate(
                zip(obj.split("-"), gloss.split("-"))
            ):
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
                            stem_id in list(df.stems["ID"])
                            or stem_id in productive_stems
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
                            "Download_URL": f"{filename}",
                        }
                    )
                else:
                    f_audios.append(
                        {
                            "ID": humidify(filename, key="wf_audio", unique=True),
                            "Name": filename.replace(".wav", ""),
                            "Media_Type": "x/wav",
                            "Download_URL": f"{filename}",
                        }
                    )

        if "=" in wf["Gloss"]:
            # store as form
            f_id = humidify(strip_form(wf["Analysis"]) + "-" + wf["Translation"][0])
            form_dic = {
                "ID": f_id,
                "Form": strip_form(wf["Analysis"]),
                "Parameter_ID": wf["Gloss"],
                "Media_ID": filename.replace(".wav", ""),
            }
            def split_cliticized(wf):
                parts = []
                for k, v in wf.items():
                    if "=" in v:
                        for idx, part in enumerate(v.split("=")):
                            if len(parts) <= idx:
                                parts.append({})
                            parts[idx][k] = part
                return parts
            # create multiple wordform IDs
            wf_ids = {
                process_wordform(
                    x["Analysis"],
                    x["Gloss"],
                    x["Lexeme_IDs"],
                    x["Gramm"],
                    x["Morpheme_IDs"],
                    Source=["muller2021yawarana"],
                    Part_Of_Speech=x["POS"],
                ): x
                for x in split_cliticized(wf)
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

    # in-context wordforms

    ex_audios = []
    exampleparts = []
    split_cols = ["Analyzed_Word", "Gloss", "Lexeme_IDs", "Gramm", "Morpheme_IDs"]

    if full:
        df.examples = cread("raw/full_examples.csv")
    else:
        df.examples = cread("raw/examples.csv")
    df.examples.rename(columns={"Record_Number": "Sentence_Number"}, inplace=True)

    df.examples["Language_ID"] = "yab"
    df.examples["Primary_Text"] = df.examples["Primary_Text"].apply(
        lambda x: x.replace("#", "")
    )
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
                # print(morpheme_ids)
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
                    elif gloss not in ["***", "?"]:
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
                elif gloss not in ["***", "?"]:
                    log.warning(
                        f"Unidentifiable wordform {obj} '{gloss}' in {ex['ID']}"
                    )
        file_path = AUDIO_PATH / f'{ex["ID"]}.wav'
        if file_path.is_file():
            ex_audios.append(
                {
                    "ID": ex["ID"],
                    "Name": ex["ID"],
                    "Media_Type": "audio/wav",
                    "Download_URL": ex["ID"] + ".wav",
                }
            )
            examples_with_audio.append(ex["ID"])

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
    text_list = cread("../corpus/texts.csv")
    for text in text_list.to_dict("records"):
        # if text["id"] in text_metadata: # todo clean up this entire mess
        #     text.update(**text_metadata[text["id"]])
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
    #     "/home/florianm/Dropbox/research/cariban/yawarana/corpus/annotation/output/multiword.csv"
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
    #     "/home/florianm/Dropbox/research/cariban/yawarana/corpus/annotation/output/inflections.csv"
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
    splitcol(df.morphemes, "Tags", sep=",")

    df.productive_lexemes = pd.DataFrame.from_dict(productive_lexemes.values())
    df.productive_lexemes["Language_ID"] = "yab"
    join_dfs("lexemes", "lexemes", "productive_lexemes")

    df.productive_stems = pd.DataFrame.from_dict(productive_stems.values())
    df.productive_stems["Language_ID"] = "yab"

    join_dfs("stems", "stems", "productive_stems")
    df.stems.rename(columns={"POS": "Part_Of_Speech"}, inplace=True)

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
        {"ID": gloss_id, "Name": gloss}
        for gloss, gloss_id in get_values("glosses").items()
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
        "morphemes": [{"name": "Tags", "datatype": "string", "separator": ","}]
    }
    spec = CLDFSpec(dir="cldf", module="Generic", metadata_fname="metadata.json")
    if full:
        spec = CLDFSpec(dir="full", module="Generic", metadata_fname="metadata.json")
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
