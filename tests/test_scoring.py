"""
Tests for scoring, manuscript assets, and CLI demo execution in SpecCert.
"""

import os
import tempfile
import numpy as np
import pytest
from speccert.core.uv_vis import calculate_uv_vis_spectrum
from speccert.core.vibrational import calculate_scaled_vibrational_spectrum
from speccert.core.dos_dband import calculate_dos_and_dband_center
from speccert.core.scoring import assess_spectroscopy_quality
from speccert.reporters.plot_generator import generate_speccert_figures
from speccert.reporters.manuscript_prep import generate_speccert_manuscript_assets
from speccert.reporters.html_report import generate_speccert_html_report
from speccert.cli import run_demo


def test_full_speccert_pipeline():
    meta = {
        "system": "Benzophenone",
        "functional": "B3LYP",
        "software": "ORCA"
    }

    uv_res = calculate_uv_vis_spectrum(
        energies_ev=[3.2, 4.1],
        oscillator_strengths=[0.15, 0.65]
    )

    vib_res = calculate_scaled_vibrational_spectrum(
        frequencies_cm1=[800.0, 1600.0, 1720.0, 3050.0],
        ir_intensities=[30.0, 80.0, 350.0, 45.0],
        functional="B3LYP"
    )

    e_grid = np.linspace(-6.0, 3.0, 200)
    dos_res = calculate_dos_and_dband_center(
        energies_ev=e_grid.tolist(),
        total_dos=(np.exp(-0.5*(e_grid+1.5)**2) + 0.5).tolist(),
        projected_d_dos=np.exp(-0.5*(e_grid+1.5)**2).tolist(),
        fermi_energy_ev=0.0
    )

    report = assess_spectroscopy_quality(
        metadata=meta,
        uv_vis_res=uv_res,
        vib_res=vib_res,
        dos_res=dos_res
    )

    assert report.overall_status == "PASS"

    with tempfile.TemporaryDirectory() as tmpdir:
        plots = generate_speccert_figures(report, tmpdir, formats=["png", "svg"])
        assert len(plots) > 0
        for p in plots:
            assert os.path.exists(p)

        assets = generate_speccert_manuscript_assets(report, tmpdir)
        assert os.path.exists(assets["summary_csv"])
        assert os.path.exists(assets["summary_tex"])
        assert os.path.exists(assets["methods_text"])
        assert os.path.exists(assets["citation_bib"])

        html_p = os.path.join(tmpdir, "report.html")
        generate_speccert_html_report(report, html_p, methods_text="Sample methods", citation_bib="@software{}")
        assert os.path.exists(html_p)
        assert os.path.getsize(html_p) > 500


def test_cli_demo_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_demo(output_dir=tmpdir)
        assert os.path.exists(os.path.join(tmpdir, "report.html"))
        assert os.path.exists(os.path.join(tmpdir, "speccert_summary_table.csv"))
        assert os.path.exists(os.path.join(tmpdir, "citation.bib"))
