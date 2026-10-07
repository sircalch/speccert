"""
Extracts the precomputed vibrational scaling factors of NIST CCCBDB (Computational Chemistry Comparison and
Benchmark Database, SRD 101, https://cccbdb.nist.gov/vibscalejustx.asp) from the saved page
validation/data/cccbdb_vibscalejustx_2026-10-06.html into the package table speccert/data/cccbdb_scaling.csv
(columns: method, basis, factor). Only the rows used by SpecCert's method aliases are kept.

    python validation/extract_cccbdb.py
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "data", "cccbdb_vibscalejustx_2026-10-06.html")
DST = os.path.join(os.path.dirname(HERE), "speccert", "data", "cccbdb_scaling.csv")
METHODS = ["HF", "LSDA", "BLYP", "B3LYP", "B3PW91", "mPW1PW91", "M06-2X", "PBEPBE", "PBE1PBE", "HSEh1PBE", "TPSSh",
           "wB97X-D", "B97D3", "MP2", "B2PLYP", "CCSD(T)"]


def main():
    rows = []
    for t in pd.read_html(SRC)[2:4]:  # all-electron basis sets; effective-core-potential basis sets
        t = t.copy()
        t.columns = ["kind", "method"] + list(t.iloc[0, 2:])
        for _, r in t.iloc[1:].iterrows():
            if r["method"] not in METHODS:
                continue
            for basis, v in r.iloc[2:].items():
                if pd.notna(v) and pd.notna(basis):
                    rows.append({"method": r["method"], "basis": basis, "factor": float(v)})
    d = pd.DataFrame(rows).drop_duplicates(["method", "basis"])
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    d.to_csv(DST, index=False)
    print(len(d), "factors for", d.method.nunique(), "methods ->", DST)


if __name__ == "__main__":
    main()
