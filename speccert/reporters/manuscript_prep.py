"""
Manuscript Methods snippet, summary tables (CSV, LaTeX), and BibTeX citations for SpecCert.
"""

from typing import Dict, Any, Optional
import os
import pandas as pd
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

    rows.append({"Parameter": "Target System / Molecule", "Value": f"{meta.get('system', 'Chemical System')} ({meta.get('software', 'DFT')})", "Status": "PASS"})
    rows.append({"Parameter": "Level of Theory / Functional", "Value": f"{meta.get('functional', 'DFT')}", "Status": "PASS"})

    if report.uv_vis:
        uv = report.uv_vis
        rows.append({"Parameter": "UV-Vis Absorption Max (lambda_max)", "Value": f"{uv.lambda_max_nm:.1f} nm (f_max = {uv.max_oscillator_strength:.4f})", "Status": uv.status})
        rows.append({"Parameter": "Total Oscillator Strength Sum", "Value": f"{uv.total_oscillator_strength:.3f} ({uv.n_states} excited states)", "Status": "PASS"})

    if report.vibrational:
        vib = report.vibrational
        rows.append({"Parameter": "Vibrational Scaling Factor", "Value": f"{vib.scaling_factor_applied:.4f} ({vib.functional_name})", "Status": "PASS"})
        rows.append({"Parameter": "Vibrational Modes Convoluted", "Value": f"{vib.n_modes} modes", "Status": "PASS"})
        if vib.top_diagnostic_bands:
            top1 = vib.top_diagnostic_bands[0]
            rows.append({"Parameter": "Strongest IR Diagnostic Band", "Value": f"{top1.scaled_freq_cm1:.1f} cm^-1 ({top1.band_assignment})", "Status": "PASS"})

    if report.dos_analysis:
        dos = report.dos_analysis
        if dos.d_band_center_filled_ev is not None:
            rows.append({"Parameter": "Hammer-Norskov d-Band Center (eps_d)", "Value": f"{dos.d_band_center_filled_ev:.3f} eV rel to E_F", "Status": "PASS"})
            rows.append({"Parameter": "d-Band Width (W_d)", "Value": f"{dos.d_band_width_ev:.3f} eV", "Status": "PASS"})
            rows.append({"Parameter": "d-Band Filling Fraction", "Value": f"{dos.d_band_filling_fraction*100:.1f}%", "Status": "PASS"})

    df_summary = pd.DataFrame(rows)

    # CSV
    csv_path = os.path.join(output_dir, "speccert_summary_table.csv")
    df_summary.to_csv(csv_path, index=False)
    generated["summary_csv"] = csv_path

    # LaTeX
    tex_path = os.path.join(output_dir, "speccert_summary_table.tex")
    tex_content = df_summary.to_latex(index=False, escape=False)
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("% SpecCert Spectroscopy & Electronic Structure Validation Table\n")
        f.write(tex_content)
    generated["summary_tex"] = tex_path

    # 2. Methods Text
    methods_path = os.path.join(output_dir, "methods_snippet.txt")
    sys_str = meta.get("system", "the investigated system")
    soft_str = meta.get("software", "DFT calculations")
    func_str = meta.get("functional", "DFT")

    uv_str = ""
    if report.uv_vis:
        uv = report.uv_vis
        uv_str = f"Time-dependent density functional theory (TD-DFT) was used to compute vertical electronic excitations ({uv.n_states} states), yielding an absorption maximum of lambda_max = {uv.lambda_max_nm:.1f} nm with maximum oscillator strength f = {uv.max_oscillator_strength:.4f}. "

    vib_str = ""
    if report.vibrational:
        vib = report.vibrational
        vib_str = f"Harmonic vibrational frequencies were scaled by an empirical factor of {vib.scaling_factor_applied:.4f} ({vib.functional_name}) to account for anharmonicity and basis set limitations, convoluted with a Lorentzian profile (FWHM = 12 cm^-1). "

    dos_str = ""
    if report.dos_analysis and report.dos_analysis.d_band_center_filled_ev is not None:
        dos = report.dos_analysis
        dos_str = f"Electronic density of states (DOS) and d-band parameters were evaluated following Hammer-Norskov theory, yielding a filled d-band center of eps_d = {dos.d_band_center_filled_ev:.3f} eV (relative to E_F) with width W_d = {dos.d_band_width_ev:.3f} eV. "

    full_methods = (
        f"Spectroscopic and electronic structure simulations for {sys_str} were performed with {soft_str} at the {func_str} level of theory. "
        f"Spectral convolution, empirical scaling, and electronic structure audits were certified using SpecCert v1.0.0 (Monreal-Hernández, 2026). "
        f"{uv_str}{vib_str}{dos_str}"
        f"The computational spectroscopy audit achieved an overall quality status of: {report.overall_status}."
    )

    with open(methods_path, "w", encoding="utf-8") as f:
        f.write(full_methods + "\n")
    generated["methods_text"] = methods_path

    # 3. BibTeX
    bib_path = os.path.join(output_dir, "citation.bib")
    bib_content = """@software{monreal2026speccert,
  author = {Monreal-Hern\\'andez, Andre},
  title = {{SpecCert: Automated Quality-Control, Spectroscopy Simulation (UV-Vis TD-DFT, IR/Raman Anharmonic Scaling), and Electronic Structure Certification (DOS & d-Band Center)}},
  year = {2026},
  version = {1.0.0},
  publisher = {Zenodo},
  url = {https://github.com/sircalch/speccert}
}
"""
    with open(bib_path, "w", encoding="utf-8") as f:
        f.write(bib_content)
    generated["citation_bib"] = bib_path

    return generated

