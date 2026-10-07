"""
d-band centre, width and filling of SpecCert (reading DOSCAR) against pymatgen (reading vasprun.xml of the
same VASP calculation), for the nine NOMAD calculations of fetch_nomad_doscar.py; with the values of the older
SpecCert versions for comparison.

    python validation/benchmark_dos.py [--legacy PATH_1.1.0] [--legacy100 PATH_1.0.0]

Needs pymatgen (tested with 2026.9.24). Output: validation/results/dos_benchmark.csv
Definitions compared (energies relative to the Fermi level, both spins, all atoms):
  centre_filled = int_{E<=0} E rho_d / int_{E<=0} rho_d       pymatgen get_band_center(erange=(-inf, 0))
  centre_full   = int E rho_d / int rho_d                      pymatgen get_band_center()
  width_filled  = sqrt(second central moment below E_F)        pymatgen get_band_width(erange=(-inf, 0))
  filling       = int_{E<0} rho_d / int rho_d                  pymatgen get_band_filling()
"""
import argparse
import gzip
import json
import os
import subprocess
import sys
import tempfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from speccert.parsers.vasp_doscar import parse_vasp_doscar  # noqa: E402
from speccert.core.dos_dband import calculate_dos_and_dband_center  # noqa: E402

from pymatgen.io.vasp.outputs import Vasprun  # noqa: E402
from pymatgen.electronic_structure.core import OrbitalType  # noqa: E402

DATA = os.path.join(HERE, "data", "nomad")
LEGACY_CODE = r"""
import json, sys
from speccert.parsers.vasp_doscar import parse_vasp_doscar
from speccert.core.dos_dband import calculate_dos_and_dband_center
try:
    d = parse_vasp_doscar(sys.argv[1])
    r = calculate_dos_and_dband_center(d["energies_ev"], d["total_dos"], d["projected_d_dos"], d["fermi_energy_ev"])
    print(json.dumps({"centre_filled": r.d_band_center_filled_ev, "centre_full": r.d_band_center_full_ev,
                      "filling": r.d_band_filling_fraction, "status": r.status}))
except Exception as e:
    print(json.dumps({"error": type(e).__name__ + ": " + str(e)[:120]}))
"""


def legacy(doscar_plain, checkout):
    env = dict(os.environ, PYTHONPATH=checkout)
    r = subprocess.run([sys.executable, "-c", LEGACY_CODE, doscar_plain], capture_output=True, text=True, env=env,
                       cwd=checkout)
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy", default=None)
    ap.add_argument("--legacy100", default=None)
    args = ap.parse_args()
    ids = pd.read_csv(os.path.join(DATA, "entries.csv"))
    rows = []
    for _, e in ids.iterrows():
        d = os.path.join(DATA, e.element)
        p = parse_vasp_doscar(os.path.join(d, "DOSCAR.gz"))
        s = calculate_dos_and_dband_center(p["energies_ev"], p["total_dos"], p["projected_d_dos"], p["fermi_energy_ev"])
        v = Vasprun(os.path.join(d, "vasprun.xml.gz"), parse_potcar_file=False, parse_eigen=False)
        cd = v.complete_dos
        big = 1e9
        row = {"system": e.element, "ispin": p["ispin"], "n_ions": p["n_ions"],
               "efermi_doscar": p["fermi_energy_ev"], "efermi_vasprun": cd.efermi,
               "centre_filled_speccert": s.d_band_center_filled_ev,
               "centre_filled_pymatgen": cd.get_band_center(OrbitalType.d, erange=(-big, 0.0)),
               "centre_full_speccert": s.d_band_center_full_ev,
               "centre_full_pymatgen": cd.get_band_center(OrbitalType.d),
               "width_filled_speccert": s.d_band_width_ev,
               "width_filled_pymatgen": cd.get_band_width(OrbitalType.d, erange=(-big, 0.0)),
               "filling_speccert": s.d_band_filling_fraction,
               "filling_pymatgen": cd.get_band_filling(OrbitalType.d)}
        # the first ion alone, as the earlier parser used
        first = calculate_dos_and_dband_center(p["energies_ev"], p["total_dos"], p["projected_d_dos_by_ion"][0],
                                               p["fermi_energy_ev"])
        row["centre_filled_first_ion"] = first.d_band_center_filled_ev
        with tempfile.TemporaryDirectory() as tmp:
            plain = os.path.join(tmp, "DOSCAR")
            with gzip.open(os.path.join(d, "DOSCAR.gz"), "rt") as fi, open(plain, "w") as fo:
                fo.write(fi.read())
            for tag, path in (("v110", args.legacy), ("v100", args.legacy100)):
                if path:
                    lg = legacy(plain, os.path.abspath(path))
                    row[f"centre_filled_{tag}"] = lg.get("centre_filled")
                    row[f"filling_{tag}"] = lg.get("filling")
                    row[f"error_{tag}"] = lg.get("error")
        rows.append(row)
        print(e.element, {k: (round(x, 4) if isinstance(x, float) else x) for k, x in row.items()
                          if k.startswith("centre_filled")}, flush=True)
    out = pd.DataFrame(rows)
    for q in ("centre_filled", "centre_full", "width_filled", "filling"):
        out[f"diff_{q}"] = out[f"{q}_speccert"] - out[f"{q}_pymatgen"]
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out.to_csv(os.path.join(HERE, "results", "dos_benchmark.csv"), index=False)
    print(out[[c for c in out.columns if c.startswith("diff_")] + ["system"]].to_string())


if __name__ == "__main__":
    main()
