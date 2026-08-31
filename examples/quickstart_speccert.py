"""
Quickstart tutorial for SpecCert Python API.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from speccert import (
    calculate_uv_vis_spectrum,
    calculate_scaled_vibrational_spectrum,
    calculate_dos_and_dband_center,
    assess_spectroscopy_quality
)
from speccert.parsers import parse_spectral_csv
from speccert.reporters import (
    generate_speccert_figures,
    generate_speccert_manuscript_assets,
    generate_speccert_html_report
)
from generate_sample_spectra_data import generate_sample_spectra_data


def main():
    print("Running SpecCert Python API quickstart tutorial...")
    raw_dir = "sample_spectra_dataset"
    generate_sample_spectra_data(raw_dir)

    out_dir = "quickstart_speccert_output"
    os.makedirs(out_dir, exist_ok=True)

    # 1. Parse & calculate UV-Vis
    uv_data = parse_spectral_csv(os.path.join(raw_dir, "porphyrin_uvvis.csv"))
    uv_res = calculate_uv_vis_spectrum(
        energies_ev=uv_data["energies_ev"],
        oscillator_strengths=uv_data["oscillator_strengths"]
    )

    # 2. Parse & calculate scaled IR
    ir_data = parse_spectral_csv(os.path.join(raw_dir, "porphyrin_ir.csv"))
    vib_res = calculate_scaled_vibrational_spectrum(
        frequencies_cm1=ir_data["frequencies_cm1"],
        ir_intensities=ir_data["intensities"],
        functional="wB97X-D"
    )

    # 3. Parse & calculate DOS / d-band center
    dos_data = parse_spectral_csv(os.path.join(raw_dir, "pt111_dos.csv"))
    dos_res = calculate_dos_and_dband_center(
        energies_ev=dos_data["energies_ev"],
        total_dos=dos_data["total_dos"],
        projected_d_dos=dos_data["projected_d_dos"],
        fermi_energy_ev=0.0
    )

    # 4. Consolidate report
    report = assess_spectroscopy_quality(
        metadata={"system": "Pt-Porphyrin Dye on Pt(111)", "functional": "wB97X-D", "software": "ORCA / VASP"},
        uv_vis_res=uv_res,
        vib_res=vib_res,
        dos_res=dos_res
    )

    print(f"\nOverall Spectroscopy Certification: {report.overall_status}")
    print(f"UV-Vis Absorption Max: lambda_max = {report.uv_vis.lambda_max_nm:.1f} nm")
    print(f"IR Vibrational Scaling: factor = {report.vibrational.scaling_factor_applied:.4f}")
    print(f"Hammer-Norskov d-Band Center: eps_d = {report.dos_analysis.d_band_center_filled_ev:.3f} eV rel to E_F")

    # 5. Export deliverables
    generate_speccert_figures(report, out_dir)
    assets = generate_speccert_manuscript_assets(report, out_dir)
    with open(assets["methods_text"], "r", encoding="utf-8") as f:
        methods_txt = f.read()
    with open(assets["citation_bib"], "r", encoding="utf-8") as f:
        bib_txt = f.read()

    html_p = os.path.join(out_dir, "report.html")
    generate_speccert_html_report(report, html_p, methods_text=methods_txt, citation_bib=bib_txt)

    print(f"\nCompleted! HTML report available at: {os.path.abspath(html_p)}")


if __name__ == "__main__":
    main()
