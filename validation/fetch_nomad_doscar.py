"""
Downloads real VASP DOSCAR / vasprun.xml / INCAR / POSCAR files from NOMAD (https://nomad-lab.eu, uploads
licensed CC BY 4.0) for the d-band benchmark of SpecCert v2.

    python validation/fetch_nomad_doscar.py            # search and download
    python validation/fetch_nomad_doscar.py --list     # only list the selected entries

Selection: for each element, the first published PBE single-point calculation of the elemental bulk (mainfile
.../PBE/Accurate/.../single_point/vasprun.xml, the series of the first author of upload 'monomers_input') whose
INCAR has LORBIT = 11 and which ships a DOSCAR. That series is not spin-polarised; three spin-polarised
metal clusters (SPIN_ENTRIES) are added. The entry ids are written to validation/data/nomad/entries.csv, so the download is
reproducible without searching again.
"""
import csv
import gzip
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "nomad")
API = "https://nomad-lab.eu/prod/v1/api/v1"
ELEMENTS = ["Cu", "Ag", "Au", "Ni", "Pd", "Pt", "Rh", "Ir", "Fe", "Co"]
# spin-polarised (ISPIN = 2, LORBIT = 11) metal clusters, CC BY 4.0, found with a NOMAD query on
# results.properties.electronic.dos_electronic.spin_polarized = true (first hit with DOSCAR for each element)
SPIN_ENTRIES = {"Fe39": "-0RN7SIfS7oobLZfrxpq1cuxz5g7", "Ni47": "-0Lr18tvi0d9AaEobeiK3O63mjdM",
                "Co18": "-02_ILI1bWoJw1Y80KItPnGGvEq2"}


def post(path, body):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))


def get(path, raw=False):
    with urllib.request.urlopen(API + path, timeout=300) as r:
        return r.read() if raw else json.load(r)


def candidates(el):
    body = {"query": {"results.method.simulation.program_name": "VASP", "results.material.elements": {"all": [el]},
                      "results.material.n_elements": 1},
            "pagination": {"page_size": 200},
            "required": {"include": ["entry_id", "upload_id", "mainfile", "results.material.structural_type"]}}
    hits = post("/entries/query", body)["data"]
    return [h for h in hits if "/PBE/Accurate/" in h["mainfile"] and h["mainfile"].endswith("single_point/vasprun.xml")
            and h.get("results", {}).get("material", {}).get("structural_type") == "bulk"]


def incar(entry):
    txt = get(f"/entries/{entry}/raw/INCAR", raw=True).decode(errors="ignore")
    kv = {}
    for ln in txt.splitlines():
        if "=" in ln:
            k, v = ln.split("=", 1)
            kv[k.strip().upper()] = v.strip()
    return kv


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for el in ELEMENTS:
        chosen = None
        for h in sorted(candidates(el), key=lambda h: h["mainfile"]):
            files = [f["path"].split("/")[-1] for f in get(f"/entries/{h['entry_id']}/rawdir")["data"]["files"]]
            if "DOSCAR" not in files:
                continue
            kv = incar(h["entry_id"])
            if kv.get("LORBIT") != "11":
                continue
            chosen = (h, kv)
            if kv.get("ISPIN") == "2" or el not in ("Fe", "Co", "Ni"):
                break
        if chosen is None:
            print(el, "no suitable entry")
            continue
        h, kv = chosen
        up = get(f"/uploads/{h['upload_id']}")["data"]
        rows.append({"element": el, "entry_id": h["entry_id"], "upload_id": h["upload_id"], "mainfile": h["mainfile"],
                     "ISPIN": kv.get("ISPIN", "1"), "LORBIT": kv.get("LORBIT"), "license": up.get("license")})
        print(rows[-1])
        if "--list" in sys.argv:
            continue
        d = os.path.join(OUT, el)
        os.makedirs(d, exist_ok=True)
        for f in ("DOSCAR", "vasprun.xml", "INCAR", "POSCAR"):
            data = get(f"/entries/{h['entry_id']}/raw/{f}", raw=True)
            with gzip.open(os.path.join(d, f + ".gz"), "wb") as fh:
                fh.write(data)
    for label, entry in SPIN_ENTRIES.items():
        d0 = get(f"/entries/{entry}")["data"]
        kv = incar(entry)
        up = get(f"/uploads/{d0['upload_id']}")["data"]
        rows.append({"element": label, "entry_id": entry, "upload_id": d0["upload_id"], "mainfile": d0["mainfile"],
                     "ISPIN": kv.get("ISPIN", "1"), "LORBIT": kv.get("LORBIT"), "license": up.get("license")})
        print(rows[-1])
        if "--list" in sys.argv:
            continue
        d = os.path.join(OUT, label)
        os.makedirs(d, exist_ok=True)
        for f in ("DOSCAR", "vasprun.xml", "INCAR", "POSCAR"):
            data = get(f"/entries/{entry}/raw/{f}", raw=True)
            with gzip.open(os.path.join(d, f + ".gz"), "wb") as fh:
                fh.write(data)
    with open(os.path.join(OUT, "entries.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
