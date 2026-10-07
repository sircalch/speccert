"""
Figures and tables for the SpecCert v2 manuscript, built from validation/results/, the ORCA outputs and the
NOMAD DOSCAR files.

    python validation/make_figures.py
"""
import csv
import os
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from speccert.parsers.orca_tddft import parse_orca_tddft_output  # noqa: E402
from speccert.parsers.orca_freq import parse_orca_freq_output  # noqa: E402
from speccert.parsers.vasp_doscar import parse_vasp_doscar  # noqa: E402
from speccert.core.uv_vis import calculate_uv_vis_spectrum, HC_EV_NM  # noqa: E402
from speccert.core.vibrational import calculate_scaled_vibrational_spectrum, CCCBDB_FACTORS  # noqa: E402
from speccert.core.dos_dband import calculate_dos_and_dband_center  # noqa: E402

RES, FIG, TAB = (os.path.join(HERE, x) for x in ("results", "figures", "tables"))
RUNS = os.path.join(HERE, "spec_runs")
MM = 1 / 25.4
DOUBLE = 174 * MM
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
NEW, OLD, REF, AUX = "#2a78d6", "#e87ba4", "#1baf7a", "#eda100"
# factors applied by SpecCert 1.0.0/1.1.0 for any basis set
LEGACY_FACTORS = {"B3LYP": 0.9679, "PBE1PBE": 0.9594, "wB97X-D": 0.9570, "M06-2X": 0.9520, "PBEPBE": 0.9850,
                  "HF": 0.8992, "MP2": 0.9427}
LABEL = {"PBE1PBE": "PBE0", "PBEPBE": "PBE"}


def setup():
    matplotlib.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "legend.fontsize": 6.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
        "ytick.color": INK2, "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
        "legend.frameon": False, "lines.linewidth": 1.2, "lines.markersize": 4, "savefig.dpi": 600,
        "pdf.fonttype": 42, "ps.fonttype": 42})


def panel(ax, letter, x=-0.15):
    ax.text(x, 1.03, f"({letter})", transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", color=INK)


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def orca_abs(mol):
    d = np.loadtxt(os.path.join(RUNS, mol, "tddft.out.ABS.dat"))
    return np.linspace(1.0, 12.0, d.shape[0]), d[:, 1]


def fig_uv():
    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE, 58 * MM), gridspec_kw={"width_ratios": [1, 1, 0.8]})
    for ax, mol, letter in ((axes[0], "butadiene", "a"), (axes[1], "naphthalene", "b")):
        t = parse_orca_tddft_output(os.path.join(RUNS, mol, "tddft.out"))
        e_ref, eps_ref = orca_abs(mol)
        win = (HC_EV_NM / 9.0, HC_EV_NM / 3.0)
        new = calculate_uv_vis_spectrum(t["energies_ev"], t["oscillator_strengths"], fwhm_ev=0.3,
                                        wavelength_range_nm=win, n_grid_points=3000)
        wl = np.array(new.wavelength_grid_nm)
        eps = np.array(new.extinction_coefficient_m_minus_1_cm_minus_1)
        m = (e_ref >= 3.0) & (e_ref <= 9.0)
        ax.plot(HC_EV_NM / e_ref[m], eps_ref[m] / 1e3, color=REF, lw=3.0, alpha=0.45, label="orca_mapspc")
        ax.plot(wl, eps / 1e3, color=NEW, lw=1.0, label="SpecCert 1.2.0")
        ax.plot(wl, eps * 2.174e4 / 2.8706e4 / 1e3, color=OLD, lw=1.0, ls="--", label="SpecCert 1.1.0")
        ax.set_xlabel("wavelength (nm)")
        ax.set_ylabel(r"$\varepsilon$ (10$^3$ L mol$^{-1}$ cm$^{-1}$)")
        ax.set_title(mol, pad=3)
        panel(ax, letter)
    axes[0].legend(loc="upper right", handlelength=1.5)
    u = pd.read_csv(os.path.join(RES, "uv_benchmark.csv"))
    y = np.arange(len(u))
    axes[2].barh(y, u.max_rel_dev_eps_vs_orca * 1e4, color=NEW, height=0.6)
    axes[2].set_yticks(y, u.molecule)
    axes[2].set_xlabel(r"max $|\varepsilon/\varepsilon_\mathrm{ORCA}-1|$ ($10^{-4}$)")
    axes[2].invert_yaxis()
    axes[2].grid(axis="y", visible=False)
    panel(axes[2], "c", x=-0.55)
    fig.tight_layout(w_pad=1.6)
    save(fig, "fig1_uv")


def fig_ir():
    fig, (a, b) = plt.subplots(1, 2, figsize=(DOUBLE, 66 * MM), gridspec_kw={"width_ratios": [1.05, 1]})
    methods = list(LEGACY_FACTORS)
    for i, mth in enumerate(methods):
        vals = sorted(v for (m, _), v in CCCBDB_FACTORS.items() if m == mth)
        x = np.full(len(vals), i) + np.linspace(-0.18, 0.18, len(vals))
        a.scatter(x, vals, s=8, color=NEW, linewidth=0, label="CCCBDB, one point per basis set" if i == 0 else None)
        a.plot([i - 0.32, i + 0.32], [LEGACY_FACTORS[mth]] * 2, color=OLD, lw=1.6,
               label="SpecCert 1.0.0/1.1.0 (any basis)" if i == 0 else None)
    a.set_xticks(range(len(methods)), [LABEL.get(m, m) for m in methods], rotation=30, ha="right")
    a.set_ylabel("frequency scaling factor")
    a.legend(loc="lower right", handletextpad=0.4)
    panel(a, "a")
    fq = parse_orca_freq_output(os.path.join(RUNS, "acrolein", "opt_freq.out"))
    real = calculate_scaled_vibrational_spectrum(fq["frequencies_cm1"], fq["ir_intensities_km_mol"],
                                                 custom_scaling_factor=0.9679, freq_range_cm1=(400, 3400),
                                                 n_grid_points=3001)
    fake = calculate_scaled_vibrational_spectrum(fq["frequencies_cm1"], [50.0] * fq["n_modes"],
                                                 custom_scaling_factor=0.9679, freq_range_cm1=(400, 3400),
                                                 n_grid_points=3001)
    g = np.array(real.frequency_grid_cm1)
    b.plot(g, real.ir_absorbance_convoluted, color=NEW, lw=1.0, label="ORCA intensities")
    b.plot(g, -np.array(fake.ir_absorbance_convoluted), color=OLD, lw=1.0,
           label="CLI of 1.0.0/1.1.0 (50 km/mol each)")
    b.axhline(0, color=INK2, lw=0.5)
    b.set_xlim(3400, 400)
    b.set_xlabel(r"scaled wavenumber (cm$^{-1}$)")
    b.set_ylabel(r"IR intensity (km mol$^{-1}$ per cm$^{-1}$)")
    b.set_title("acrolein", pad=3)
    b.legend(loc="center", handlelength=1.5)
    panel(b, "b")
    fig.tight_layout(w_pad=2.0)
    save(fig, "fig2_ir")


def per_ion_centres(system):
    p = parse_vasp_doscar(os.path.join(HERE, "data", "nomad", system, "DOSCAR.gz"))
    return [calculate_dos_and_dband_center(p["energies_ev"], p["total_dos"], d, p["fermi_energy_ev"]).d_band_center_filled_ev
            for d in p["projected_d_dos_by_ion"]]


def fig_dband():
    d = pd.read_csv(os.path.join(RES, "dos_benchmark.csv"))
    fig, (a, b) = plt.subplots(1, 2, figsize=(DOUBLE, 64 * MM), gridspec_kw={"width_ratios": [1, 1.1]})
    lim = (-4.3, -1.2)
    a.plot(lim, lim, color=INK2, lw=0.6, ls=":")
    a.scatter(d.centre_filled_pymatgen, d.centre_filled_v110, s=26, marker="s", facecolor="none", edgecolor=OLD,
              linewidth=0.9, label="SpecCert 1.0.0/1.1.0")
    a.scatter(d.centre_filled_pymatgen, d.centre_filled_speccert, s=12, color=NEW, linewidth=0, label="SpecCert 1.2.0")
    for _, r in d.iterrows():
        a.annotate(r.system, (r.centre_filled_pymatgen, r.centre_filled_speccert), xytext=(3, -8),
                   textcoords="offset points", fontsize=5.5, color=INK2)
    a.set_xlim(lim)
    a.set_ylim(lim)
    a.set_xlabel(r"$\varepsilon_d$, occupied part, pymatgen (eV)")
    a.set_ylabel(r"$\varepsilon_d$, occupied part, SpecCert (eV)")
    a.legend(loc="upper left")
    panel(a, "a")
    for i, s in enumerate(["Fe39", "Ni47", "Co18"]):
        c = np.array(per_ion_centres(s))
        x = i + np.random.default_rng(1).uniform(-0.15, 0.15, len(c))
        b.scatter(x, c, s=7, color=INK2, alpha=0.6, linewidth=0, label="individual atoms" if i == 0 else None)
        r = d[d.system == s].iloc[0]
        b.plot([i - 0.28, i + 0.28], [r.centre_filled_speccert] * 2, color=NEW, lw=1.8,
               label="all atoms (1.2.0 = pymatgen)" if i == 0 else None)
        b.plot([i - 0.28, i + 0.28], [r.centre_filled_v110] * 2, color=OLD, lw=1.4, ls="--",
               label="1.0.0/1.1.0" if i == 0 else None)
        b.scatter([i + 0.33], [c[0]], marker="<", s=22, color=AUX, label="first atom" if i == 0 else None)
    b.set_xticks(range(3), [r"Fe$_{39}$", r"Ni$_{47}$", r"Co$_{18}$"])
    b.set_ylabel(r"$\varepsilon_d$, occupied part (eV)")
    b.legend(loc="lower right", fontsize=6)
    panel(b, "b")
    fig.tight_layout(w_pad=2.0)
    save(fig, "fig3_dband")


def tables():
    u = pd.read_csv(os.path.join(RES, "uv_benchmark.csv"))
    with open(os.path.join(TAB, "uv.tex"), "w") as fh:
        for _, r in u.iterrows():
            fh.write(f"{r.molecule} & {r.sum_f:.3f} & {r.f_from_eps_speccert:.3f} & {r.max_rel_dev_eps_vs_orca:.1e} & "
                     f"{r.eps_peak_ratio_v110:.3f} & {r.lambda_max_speccert:.1f} & {r.status_speccert.lower()} \\\\\n")
    d = pd.read_csv(os.path.join(RES, "dos_benchmark.csv"))
    with open(os.path.join(TAB, "dband.tex"), "w") as fh:
        for _, r in d.iterrows():
            name = {"Fe39": "Fe$_{39}$", "Ni47": "Ni$_{47}$", "Co18": "Co$_{18}$"}.get(r.system, r.system)
            fh.write(f"{name} & {int(r.ispin)} & {int(r.n_ions)} & {r.centre_filled_pymatgen:.3f} & "
                     f"{r.centre_filled_speccert:.3f} & {r.centre_full_speccert:.3f} & {r.centre_filled_v110:.3f} & "
                     f"{r.centre_filled_first_ion:.3f} \\\\\n")


def main():
    setup()
    for p in (FIG, TAB):
        os.makedirs(p, exist_ok=True)
    fig_uv()
    fig_ir()
    fig_dband()
    tables()
    d = pd.read_csv(os.path.join(RES, "dos_benchmark.csv"))
    u = pd.read_csv(os.path.join(RES, "uv_benchmark.csv"))
    i = pd.read_csv(os.path.join(RES, "ir_benchmark.csv"))
    print(f"UV: max |eps/ORCA-1| {u.max_rel_dev_eps_vs_orca.max():.1e}; 1.1.0 peak ratio "
          f"{u.eps_peak_ratio_v110.min():.4f}-{u.eps_peak_ratio_v110.max():.4f}; sum rule max dev "
          f"{(u.f_from_eps_speccert / u.sum_f - 1).abs().max():.1e}")
    print(f"IR: freq dev {i.max_abs_dev_freq.max()}, int dev {i.max_abs_dev_int.max():.4f}, area ratio "
          f"{i.area_over_sum_int.min():.4f}-{i.area_over_sum_int.max():.4f}")
    print(f"d-band: max |1.2.0 - pymatgen| centre_filled {d.diff_centre_filled.abs().max():.4f}, centre_full "
          f"{d.diff_centre_full.abs().max():.4f}, width {d.diff_width_filled.abs().max():.4f}, filling "
          f"{d.diff_filling.abs().max():.5f}; legacy error clusters "
          f"{(d.centre_filled_v110 - d.centre_filled_pymatgen)[d.ispin == 2].round(3).tolist()}; first-ion error "
          f"{(d.centre_filled_first_ion - d.centre_filled_pymatgen)[d.ispin == 2].round(3).tolist()}")


if __name__ == "__main__":
    main()
