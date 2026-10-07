"""
UV-Vis and IR of SpecCert against ORCA 6.1.1 on the eight molecules of make_spec_inputs.py.

    python validation/benchmark_uv_ir.py [--legacy PATH_1.1.0] [--legacy100 PATH_1.0.0]

UV-Vis: the absorption spectrum of orca_mapspc (Gaussian, FWHM 0.3 eV, 1-12 eV, 11001 points), which ORCA
computes from the same transitions, is the reference for SpecCert's molar absorption coefficient; the
oscillator-strength sum rule f = 4.319e-9 * integral(eps d nu~) is checked on SpecCert's spectrum.
IR: frequencies and intensities read from the output are compared with the $ir_spectrum block of the .hess
file; the area of the broadened spectrum is compared with the sum of intensities in the window.
Outputs: validation/results/uv_benchmark.csv, validation/results/ir_benchmark.csv
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from speccert.parsers.orca_tddft import parse_orca_tddft_output  # noqa: E402
from speccert.parsers.orca_freq import parse_orca_freq_output  # noqa: E402
from speccert.core.uv_vis import calculate_uv_vis_spectrum, HC_EV_NM, F_EPS_COEFF  # noqa: E402
from speccert.core.vibrational import calculate_scaled_vibrational_spectrum  # noqa: E402

RUNS = os.path.join(HERE, "spec_runs")
MAPSPC = os.environ.get("ORCA_MAPSPC", r"C:\ORCA_6.1.1\orca_mapspc.exe")
FWHM = 0.30
LEGACY_UV = r"""
import json, sys
import numpy as np
from speccert.parsers.orca_tddft import parse_orca_tddft_output
from speccert.core.uv_vis import calculate_uv_vis_spectrum
try:
    d = parse_orca_tddft_output(sys.argv[1])
    r = calculate_uv_vis_spectrum(d["energies_ev"], d["oscillator_strengths"], fwhm_ev=0.30)
    wl = np.array(r.wavelength_grid_nm); eps = np.array(r.extinction_coefficient_m_minus_1_cm_minus_1)
    print(json.dumps({"lambda_max": r.lambda_max_nm, "eps_max": float(eps.max()), "status": r.status,
                      "n_states": r.n_states, "wl": wl.tolist(), "eps": eps.tolist()}))
except Exception as e:
    print(json.dumps({"error": type(e).__name__ + ": " + str(e)[:150]}))
"""


def mapspc(out):
    subprocess.run([MAPSPC, os.path.basename(out), "ABS", "-eV", "-x01", "-x112", f"-w{FWHM}", "-n11001"],
                   cwd=os.path.dirname(out), capture_output=True)
    d = np.loadtxt(out + ".ABS.dat")
    # the file prints energies with two decimals; the grid is the one requested (-x0, -x1, -n)
    return np.linspace(1.0, 12.0, d.shape[0]), d[:, 1]


def speccert_eps_at(energies_ev, f, e_query):
    """SpecCert's spectrum on a dense wavelength grid, interpolated to the query energies."""
    wl_lo, wl_hi = HC_EV_NM / e_query.max(), HC_EV_NM / e_query.min()
    r = calculate_uv_vis_spectrum(energies_ev, f, fwhm_ev=FWHM, wavelength_range_nm=(wl_lo, wl_hi),
                                  n_grid_points=200001)
    e = HC_EV_NM / np.array(r.wavelength_grid_nm)
    eps = np.array(r.extinction_coefficient_m_minus_1_cm_minus_1)
    return np.interp(e_query, e[::-1], eps[::-1])


def legacy_uv(out, checkout):
    env = dict(os.environ, PYTHONPATH=checkout)
    r = subprocess.run([sys.executable, "-c", LEGACY_UV, out], capture_output=True, text=True, env=env, cwd=checkout)
    return json.loads(r.stdout.strip().splitlines()[-1])


def hess_ir(path):
    lines = open(path).read().split("$ir_spectrum")[1].splitlines()
    n = int(lines[1])
    rows = [ln.split() for ln in lines[2:2 + n]]
    return [(float(r[0]), float(r[2])) for r in rows if float(r[0]) != 0.0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy", default=None)
    ap.add_argument("--legacy100", default=None)
    args = ap.parse_args()
    uv, ir = [], []
    for mol in sorted(os.listdir(RUNS)):
        d = os.path.join(RUNS, mol)
        if not os.path.isdir(d):
            continue
        # ---------------- UV-Vis
        out = os.path.join(d, "tddft.out")
        t = parse_orca_tddft_output(out)
        e_ref, eps_ref = mapspc(out)
        eps_sc = speccert_eps_at(t["energies_ev"], t["oscillator_strengths"], e_ref)
        mask = eps_ref > 0.01 * eps_ref.max()
        full = calculate_uv_vis_spectrum(t["energies_ev"], t["oscillator_strengths"], fwhm_ev=FWHM, n_grid_points=20001)
        # sum rule on a window wide enough to hold every band (+-6 sigma)
        lo, hi = min(t["energies_ev"]) - 1.5, max(t["energies_ev"]) + 1.5
        e_w = np.linspace(lo, hi, 60001)
        eps_w = speccert_eps_at(t["energies_ev"], t["oscillator_strengths"], e_w)
        f_from_eps = F_EPS_COEFF * np.trapezoid(eps_w, e_w * 8065.543937)
        row = {"molecule": mol, "n_states": len(t["energies_ev"]), "sum_f": float(np.sum(t["oscillator_strengths"])),
               "f_from_eps_speccert": float(f_from_eps),
               "max_rel_dev_eps_vs_orca": float(np.max(np.abs(eps_sc[mask] / eps_ref[mask] - 1))),
               "eps_max_orca": float(eps_ref.max()), "e_max_orca_ev": float(e_ref[np.argmax(eps_ref)]),
               "lambda_max_speccert": full.lambda_max_nm, "status_speccert": full.status,
               "e_highest_state_ev": float(max(t["energies_ev"]))}
        bright = [(e, f) for e, f in zip(t["energies_ev"], t["oscillator_strengths"]) if f >= 0.05]
        row["first_bright_nm"] = HC_EV_NM / bright[0][0] if bright else None
        for tag, path in (("v110", args.legacy), ("v100", args.legacy100)):
            if path:
                lg = legacy_uv(out, os.path.abspath(path))
                if "error" in lg:
                    row[f"error_{tag}"] = lg["error"]
                    continue
                wl, eps = np.array(lg["wl"]), np.array(lg["eps"])
                e_l = HC_EV_NM / wl
                ref_at = np.interp(e_l, e_ref, eps_ref)
                m2 = ref_at > 0.01 * eps_ref.max()
                row[f"eps_ratio_{tag}"] = float(np.median(eps[m2] / ref_at[m2])) if m2.any() else None
                row[f"eps_peak_ratio_{tag}"] = float(eps.max() / np.interp(e_l[np.argmax(eps)], e_ref, eps_ref))
                row[f"lambda_max_{tag}"] = lg["lambda_max"]
                row[f"status_{tag}"] = lg["status"]
                row[f"n_states_{tag}"] = lg["n_states"]
        uv.append(row)
        # ---------------- IR
        fq = parse_orca_freq_output(os.path.join(d, "opt_freq.out"))
        ref = hess_ir(os.path.join(d, "opt_freq.hess"))
        nu_ref = np.array([x for x, _ in ref])
        int_ref = np.array([y for _, y in ref])
        nu, inten = np.array(fq["frequencies_cm1"]), np.array(fq["ir_intensities_km_mol"])
        v = calculate_scaled_vibrational_spectrum(list(nu), list(inten), functional=fq["method"], basis=fq["basis"],
                                                  freq_range_cm1=(0.0, 5000.0), n_grid_points=500001)
        area = np.trapezoid(v.ir_absorbance_convoluted, v.frequency_grid_cm1)
        ir.append({"molecule": mol, "n_modes": len(nu), "n_modes_hess": len(nu_ref),
                   "max_abs_dev_freq": float(np.max(np.abs(nu - nu_ref))),
                   "max_abs_dev_int": float(np.max(np.abs(inten - int_ref))),
                   "area_over_sum_int": float(area / inten.sum()), "scaling_applied": v.scaling_factor_applied,
                   "scaling_source": v.scaling_source, "status": v.status, "method": fq["method"], "basis": fq["basis"]})
        print(mol, {k: (round(x, 5) if isinstance(x, float) else x) for k, x in uv[-1].items()
                    if k in ("max_rel_dev_eps_vs_orca", "f_from_eps_speccert", "sum_f", "eps_ratio_v110",
                             "lambda_max_speccert", "status_speccert", "error_v100")}, flush=True)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    pd.DataFrame(uv).to_csv(os.path.join(HERE, "results", "uv_benchmark.csv"), index=False)
    pd.DataFrame(ir).to_csv(os.path.join(HERE, "results", "ir_benchmark.csv"), index=False)
    print(pd.DataFrame(ir).to_string())


if __name__ == "__main__":
    main()
