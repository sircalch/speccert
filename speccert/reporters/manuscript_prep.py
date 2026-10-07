"""
Manuscript Methods snippet, summary tables (CSV, LaTeX), and BibTeX citations for SpecCert.
"""

from typing import Dict, Any, Optional
import os
import pandas as pd
from speccert import __version__
from speccert.citation import BIBTEX
from speccert.core.scoring import SpectroscopyReport


def generate_speccert_manuscript_assets(
    report: SpectroscopyReport,
    output_dir: str
) -> Dict[str, str]:
    """
    Generates manuscript Methods paragraph, summary CSV/LaTeX tables, and BibTeX citations.

    Parameters
    ----------
    report : SpectroscopyReport
    output_dir : str

    Returns
    -------
    paths : dict
    """
    os.makedirs(output_dir, exist_ok=True)
    generated = {}

    rows = []
    meta = report.metadata

    rows.append({"Parameter": "System", "Value": f"{meta.get('system', 'not given')} ({meta.get('software', 'not given')})", "Status": ""})
    rows.append({"Parameter": "Level of theory", "Value": f"{meta.get('functional', 'not given')}", "Status": ""})

    if report.uv_vis:
        uv = report.uv_vis
        rows.append({"Parameter": "Absorption maximum (lambda_max)", "Value": f"{uv.lambda_max_nm:.1f} nm (largest f = {uv.max_oscillator_strength:.4f})", "Status": uv.status})
        rows.append({"Parameter": "Sum of oscillator strengths", "Value": f"{uv.total_oscillator_strength:.3f} ({uv.n_states} excited states)", "Status": ""})

    if report.vibrational:
        vib = report.vibrational
        rows.append({"Parameter": "Frequency scaling factor", "Value": f"{vib.scaling_factor_applied:.3f} ({vib.scaling_source})", "Status": vib.status})
        rows.append({"Parameter": "Vibrational modes", "Value": f"{vib.n_modes} modes ({vib.n_imaginary} imaginary)", "Status": ""})
        if vib.top_diagnostic_bands and vib.ir_absorbance_convoluted is not None:
            top1 = vib.top_diagnostic_bands[0]
            rows.append({"Parameter": "Strongest IR band", "Value": f"{top1.scaled_freq_cm1:.1f} cm^-1, {top1.ir_intensity_km_mol:.1f} km/mol ({top1.band_assignment})", "Status": ""})

    if report.dos_analysis:
        dos = report.dos_analysis
        if dos.d_band_center_filled_ev is not None:
            rows.append({"Parameter": "d-band centre, occupied part", "Value": f"{dos.d_band_center_filled_ev:.3f} eV rel. to E_F", "Status": dos.status})
            rows.append({"Parameter": "d-band centre, whole band", "Value": f"{dos.d_band_center_full_ev:.3f} eV rel. to E_F", "Status": ""})
            rows.append({"Parameter": "d-band width, occupied part", "Value": f"{dos.d_band_width_ev:.3f} eV", "Status": ""})
            rows.append({"Parameter": "d-band filling", "Value": f"{dos.d_band_filling_fraction * 100:.1f}%", "Status": ""})

    df_summary = pd.DataFrame(rows)

    # CSV
    csv_path = os.path.join(output_dir, "speccert_summary_table.csv")
    df_summary.to_csv(csv_path, index=False)
    generated["summary_csv"] = csv_path

    # LaTeX
    tex_path = os.path.join(output_dir, "speccert_summary_table.tex")
    tex_content = df_summary.to_latex(index=False, escape=False)
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("% SpecCert summary table\n")
        f.write(tex_content)
    generated["summary_tex"] = tex_path

    # 2. Methods text: states what was computed and what the checks found.
    methods_path = os.path.join(output_dir, "methods_snippet.txt")
    parts = [f"Spectra and electronic-structure descriptors of {meta.get('system', 'the system')} were computed with "
             f"{meta.get('software', 'an unstated program')} at {meta.get('functional', 'an unstated level of theory')} "
             f"and processed with SpecCert v{__version__}."]
    if report.uv_vis:
        uv = report.uv_vis
        parts.append(f"The absorption spectrum was obtained from {uv.n_states} vertical excitations broadened with "
                     f"Gaussians in energy and converted to molar absorption coefficients through "
                     f"f = 4.319e-9 * integral(eps d nu); its maximum lies at {uv.lambda_max_nm:.1f} nm (check: {uv.status}).")
    if report.vibrational:
        vib = report.vibrational
        sc = (f"scaled by {vib.scaling_factor_applied:.3f} ({vib.scaling_source})" if vib.scaling_factor_applied != 1.0
              else "not scaled (no tabulated factor for this method and basis set)")
        ir = (" and the IR spectrum was broadened with area-normalised Lorentzians"
              if vib.ir_absorbance_convoluted is not None else "; no IR intensities were available")
        parts.append(f"Harmonic frequencies ({vib.n_modes} modes) were {sc}{ir} (check: {vib.status}).")
    if report.dos_analysis and report.dos_analysis.d_band_center_filled_ev is not None:
        dos = report.dos_analysis
        parts.append(f"From the d-projected density of states, the centre of the occupied d band is "
                     f"{dos.d_band_center_filled_ev:.3f} eV and that of the whole d band {dos.d_band_center_full_ev:.3f} eV "
                     f"relative to the Fermi level (check: {dos.status}).")
    parts.append(f"Overall status: {report.overall_status} ({report.validation_score.lower()}).")
    if report.recommendations:
        parts.append("Issues: " + " ".join(report.recommendations))
    full_methods = " ".join(parts)

    with open(methods_path, "w", encoding="utf-8") as f:
        f.write(full_methods + "\n")
    generated["methods_text"] = methods_path

    # 3. BibTeX
    bib_path = os.path.join(output_dir, "citation.bib")
    with open(bib_path, "w", encoding="utf-8") as f:
        f.write(BIBTEX)
    generated["citation_bib"] = bib_path

    return generated

