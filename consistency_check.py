import pandas as pd
from pathlib import Path
from writio import load

# potential variants
var_cands = ["morphemes", "lexemes"]
for file in var_cands:
    df = load(f"cldf/{file}.csv")
    print(df)

# potential duplicates
for file in ["morphs", "stems"]:
    df = load(f"cldf/{file}.csv")
    dupes = df[df.duplicated(subset=["Name", "Parameter_ID"], keep=False)]
    if len(dupes) > 0:
        print(f"Duplicate {file}:")
        print(dupes)
        print("")