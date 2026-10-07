"""
Graphical abstract for the SpecCert v2 manuscript (Molecular Physics: at most 525 pixels wide).

    python validation/make_graphical_abstract.py
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from speccert.parsers.orca_tddft import parse_orca_tddft_output  # noqa: E402
from speccert.core.uv_vis import calculate_uv_vis_spectrum, HC_EV_NM  # noqa: E402
from speccert.core.vibrational import CCCBDB_FACTORS  # noqa: E402
from make_figures import per_ion_centres  # noqa: E402

NEW, OLD, REF, INK2 = "#2a78d6", "#e87ba4", "#1baf7a", "#52514e"


def main():
    matplotlib.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                                "font.size": 7, "axes.spines.top": False, "axes.spines.right": False,
                                "axes.linewidth": 0.6})
    dpi = 150
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(525 / dpi, 240 / dpi))
    t = parse_orca_tddft_output(os.path.join(HERE, "spec_runs", "butadiene", "tddft.out"))
    r = calculate_uv_vis_spectrum(t["energies_ev"], t["oscillator_strengths"], fwhm_ev=0.3,
                                  wavelength_range_nm=(160, 230), n_grid_points=800)
    d = np.loadtxt(os.path.join(HERE, "spec_runs", "butadiene", "tddft.out.ABS.dat"))
    e = np.linspace(1, 12, d.shape[0])
    m = (HC_EV_NM / e > 160) & (HC_EV_NM / e < 230)
    eps = np.array(r.extinction_coefficient_m_minus_1_cm_minus_1)
    a.plot(HC_EV_NM / e[m], d[m, 1] / 1e3, color=REF, lw=3, alpha=0.45, label="ORCA")
    a.plot(r.wavelength_grid_nm, eps / 1e3, color=NEW, lw=0.9, label="1.2.0")
    a.plot(r.wavelength_grid_nm, eps * 0.7573 / 1e3, color=OLD, lw=0.9, ls="--", label="1.0.0")
    a.set_title("absorption coeff.", fontsize=7)
    a.set_yticks([])
    a.set_xlabel("nm", fontsize=6, labelpad=1)
    a.legend(fontsize=5, frameon=False, loc="upper right", handlelength=1)
    vals = sorted(v for (mth, _), v in CCCBDB_FACTORS.items() if mth == "B3LYP")
    b.scatter(np.linspace(-0.3, 0.3, len(vals)), vals, s=4, color=NEW, linewidth=0)
    b.axhline(0.9679, color=OLD, lw=1.2)
    b.set_xticks([])
    b.set_ylim(0.95, 0.98)
    b.set_title("B3LYP scaling,\nby basis set", fontsize=7)
    b.tick_params(labelsize=5)
    cen = np.array(per_ion_centres("Fe39"))
    c.scatter(np.random.default_rng(1).uniform(-0.2, 0.2, len(cen)), cen, s=4, color=INK2, linewidth=0)
    dd = pd.read_csv(os.path.join(HERE, "results", "dos_benchmark.csv")).set_index("system").loc["Fe39"]
    c.axhline(dd.centre_filled_speccert, color=NEW, lw=1.2)
    c.axhline(dd.centre_filled_v110, color=OLD, lw=1.2, ls="--")
    c.set_xticks([])
    c.set_title(r"Fe$_{39}$ d-band centre", fontsize=7)
    c.tick_params(labelsize=5)
    fig.tight_layout(pad=0.4)
    out = os.path.join(HERE, "figures", "graphical_abstract.png")
    fig.savefig(out, dpi=dpi)
    print(out)


if __name__ == "__main__":
    main()
