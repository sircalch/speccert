"""
Publication-ready vector figures for UV-Vis spectra, scaled IR profiles, and DOS / d-band centers.
"""

from typing import List, Optional
import os
import numpy as np
import matplotlib.pyplot as plt
from speccert.core.scoring import SpectroscopyReport

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'figure.dpi': 300,
    'lines.linewidth': 2.0,
    'grid.alpha': 0.3,
    'grid.linestyle': '--'
})


def generate_speccert_figures(
    report: SpectroscopyReport,
    output_dir: str,
    formats: List[str] = ("png", "svg", "pdf")
) -> List[str]:
    """
    Generates publication figures: UV-Vis spectrum, Scaled IR spectrum, and DOS/PDOS plot.

    Parameters
    ----------
    report : SpectroscopyReport
    output_dir : str
    formats : list of str

    Returns
    -------
    saved_files : list of str
    """
    os.makedirs(output_dir, exist_ok=True)
    saved_files = []

    # 1. UV-Vis Optical Absorption Spectrum
    if report.uv_vis is not None:
        uv = report.uv_vis
        wl = np.asarray(uv.wavelength_grid_nm)
        eps = np.asarray(uv.extinction_coefficient_m_minus_1_cm_minus_1)

        fig, ax1 = plt.subplots(figsize=(7, 5))
        ax1.plot(wl, eps, color="#0284c7", linewidth=2.2, label="Convoluted Spectrum")
        ax1.set_xlabel(r"Wavelength $\lambda$ (nm)")
        ax1.set_ylabel(r"Molar Extinction $\varepsilon$ ($\mathrm{M}^{-1}\ \mathrm{cm}^{-1}$)")

        # Secondary y-axis for oscillator strength sticks
        ax2 = ax1.twinx()
        for tr in uv.transitions:
            if tr.oscillator_strength > 0.001:
                ax2.vlines(tr.wavelength_nm, 0, tr.oscillator_strength, color="#dc2626", linewidth=1.8, alpha=0.8)
        ax2.set_ylabel("Oscillator Strength $f$", color="#dc2626")
        ax2.tick_params(axis='y', labelcolor="#dc2626")
        ax2.set_ylim(0, max(0.2, uv.max_oscillator_strength * 1.3))

        ax1.set_title(rf"TD-DFT UV-Vis Spectrum — $\lambda_{{\mathrm{{max}}}} = {uv.lambda_max_nm:.1f}\ \mathrm{{nm}}$")
        ax1.grid(True)

        plt.tight_layout()
        for fmt in formats:
            p = os.path.join(output_dir, f"speccert_uv_vis_spectrum.{fmt}")
            plt.savefig(p, dpi=300, bbox_inches="tight")
            saved_files.append(p)
        plt.close()

    # 2. Scaled IR Vibrational Spectrum
    if report.vibrational is not None:
        vib = report.vibrational
        nu_grid = np.asarray(vib.frequency_grid_cm1)
        abs_grid = np.asarray(vib.ir_absorbance_convoluted)

        fig, ax = plt.subplots(figsize=(7.5, 5))
        ax.plot(nu_grid, abs_grid, color="#7c3aed", linewidth=2.0, label="Convoluted IR Profile")

        # Invert x-axis (standard in vibrational spectroscopy: 4000 -> 400 cm^-1)
        ax.set_xlim(max(nu_grid), min(nu_grid))
        ax.set_xlabel(r"Wavenumber $\tilde{\nu}$ ($\mathrm{cm}^{-1}$)")
        ax.set_ylabel("IR Absorbance (arb. units)")

        # Annotate top diagnostic peaks
        for band in vib.top_diagnostic_bands[:3]:
            if band.ir_intensity_km_mol > 50.0:
                ax.annotate(
                    f"{band.scaled_freq_cm1:.0f} cm⁻¹",
                    xy=(band.scaled_freq_cm1, np.interp(band.scaled_freq_cm1, nu_grid, abs_grid)),
                    xytext=(band.scaled_freq_cm1, np.interp(band.scaled_freq_cm1, nu_grid, abs_grid) * 1.15),
                    ha="center",
                    fontsize=9,
                    fontweight="bold",
                    color="#4c1d95"
                )

        ax.set_title(rf"IR Vibrational Spectrum — Scaled by {vib.scaling_factor_applied:.4f} ({vib.functional_name})")
        ax.grid(True)

        plt.tight_layout()
        for fmt in formats:
            p = os.path.join(output_dir, f"speccert_ir_vibrational_spectrum.{fmt}")
            plt.savefig(p, dpi=300, bbox_inches="tight")
            saved_files.append(p)
        plt.close()

    # 3. Density of States & d-Band Center
    if report.dos_analysis is not None:
        dos = report.dos_analysis
        e_rel = np.asarray(dos.energy_grid_rel_ef_ev)
        tdos = np.asarray(dos.total_dos)

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(e_rel, tdos, color="#0f172a", linewidth=1.8, label="Total DOS")

        if dos.projected_d_dos is not None:
            pdos_d = np.asarray(dos.projected_d_dos)
            ax.fill_between(e_rel, pdos_d, color="#f59e0b", alpha=0.35, label="Projected $d$-DOS")
            ax.plot(e_rel, pdos_d, color="#d97706", linewidth=2.0)

            # d-band center vertical line
            if dos.d_band_center_filled_ev is not None:
                eps_d = dos.d_band_center_filled_ev
                ax.axvline(eps_d, color="#dc2626", linestyle="--", linewidth=2.0, label=rf"$d$-Band Center $\varepsilon_d = {eps_d:.2f}\ \mathrm{{eV}}$")

        # Fermi level line at 0 eV
        ax.axvline(0.0, color="#2563eb", linestyle=":", linewidth=1.5, label=r"Fermi Level $E_F$")

        ax.set_xlabel(r"Energy $E - E_F$ (eV)")
        ax.set_ylabel(r"Density of States (states / eV)")
        ax.set_title("Electronic Density of States (DOS) & $d$-Band Analysis")
        ax.set_xlim(-8.0, 4.0)
        ax.grid(True)
        ax.legend(loc="upper right", frameon=True, fontsize=9)

        plt.tight_layout()
        for fmt in formats:
            p = os.path.join(output_dir, f"speccert_electronic_dos.{fmt}")
            plt.savefig(p, dpi=300, bbox_inches="tight")
            saved_files.append(p)
        plt.close()

    return saved_files
