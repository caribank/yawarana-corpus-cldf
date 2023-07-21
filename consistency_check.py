import pandas as pd
from pathlib import Path
from writio import load
from itertools import combinations


# yawarana-specific formal alternations
reduced = ["j", "n"]
vowels = "aeiouïë"


def distance(a, b):
    # variation in vowels is rampant, ignore them altogether
    for vowel in vowels:
        a = a.replace(vowel, "V")
        b = b.replace(vowel, "V")
    # syllable reduction?
    for x, y in [(a, b), (b, a)]:
        if x[-1] in reduced:
            same = len(x) - 1
            if x[0:same] == y[0:same]:
                return 0
    # y-initial?
    for x, y in [(a, b), (b, a)]:
        if x[0] == "y" and x[1::] == y:
            return 0
    if a == b:
        return 0
    return 20


# potential variants
var_cands = ["morphemes", "lexemes"]
for file in var_cands:
    df = load(f"cldf/{file}.csv")
    dupe_meanings = df[
        df.duplicated(subset=["Parameter_ID", "Part_Of_Speech"], keep=False)
    ]
    for meaning, cands in dupe_meanings.groupby("Parameter_ID"):
        for a, b in combinations(cands["Name"], 2):
            dist = distance(a, b)
            if dist < 3 and dist < len(a):
                print(f"Unmerged variants in {file}: {a} ~ {b} '{meaning}'")

# potential duplicates
for file in ["morphs", "stems"]:
    df = load(f"cldf/{file}.csv")
    dupes = df[df.duplicated(subset=["Name", "Parameter_ID"], keep=False)]
    if len(dupes) > 0:
        print(f"Duplicate {file}:")
        print(dupes)
        print("")
