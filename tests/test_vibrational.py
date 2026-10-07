"""
Tests for vibrational scaling (CCCBDB lookup), IR Lorentzian broadening and the ORCA frequency parser.
"""
import os

import numpy as np
import pytest
from speccert.core.vibrational import calculate_scaled_vibrational_spectrum, get_recommended_scaling_factor
from speccert.parsers.orca_freq import parse_orca_freq_output

DATA = os.path.join(os.path.dirname(__file__), "data")


def test_scaling_factor_depends_on_method_and_basis():
    assert get_recommended_scaling_factor("B3LYP", "6-31G(d)")[0] == pytest.approx(0.960)
    assert get_recommended_scaling_factor("B3LYP", "cc-pVTZ")[0] == pytest.approx(0.967)
    assert get_recommended_scaling_factor("B3LYP-D3BJ", "def2-TZVPP")[0] == pytest.approx(0.963)
    assert get_recommended_scaling_factor("PBE0", "aug-cc-pVTZ")[0] == pytest.approx(0.962)
    # not tabulated, basis missing, or a different functional: no factor
    assert get_recommended_scaling_factor("B3LYP", "def2-SVP")[0] is None
    assert get_recommended_scaling_factor("B3LYP")[0] is None
    assert get_recommended_scaling_factor("wB97X-D3", "cc-pVTZ")[0] is None


def test_vibrational_scaling_and_convolution():
    raw = [800.0, 1500.0, 1750.0, 3100.0]
    intens = [20.0, 50.0, 250.0, 40.0]
    res = calculate_scaled_vibrational_spectrum(raw, intens, functional="B3LYP", basis="6-31G(d)", fwhm_cm1=12.0,
                                                freq_range_cm1=(0.0, 5000.0), n_grid_points=200001)
    assert res.status == "PASS"
    assert res.scaling_factor_applied == pytest.approx(0.960)
    assert res.top_diagnostic_bands[0].harmonic_freq_cm1 == 1750.0
    assert "Carbonyl" in res.top_diagnostic_bands[0].band_assignment
    # area-normalised Lorentzians: the integral equals the summed intensity (minus the far tails)
    area = np.trapezoid(res.ir_absorbance_convoluted, res.frequency_grid_cm1)
    assert area == pytest.approx(sum(intens), rel=0.01)


def test_no_intensities_means_no_spectrum_and_no_scaling_guess():
    res = calculate_scaled_vibrational_spectrum([800.0, 1700.0], functional="r2SCAN", basis="def2-TZVP")
    assert res.ir_absorbance_convoluted is None
    assert res.scaling_factor_applied == 1.0
    assert res.status == "WARNING"
    assert all(m.ir_intensity_km_mol is None for m in res.top_diagnostic_bands)


def test_imaginary_mode_fails():
    res = calculate_scaled_vibrational_spectrum([-150.0, 800.0], [1.0, 2.0], custom_scaling_factor=0.97)
    assert res.status == "FAIL"
    assert res.n_imaginary == 1


def test_orca_freq_parser_real_output():
    d = parse_orca_freq_output(os.path.join(DATA, "acrolein_opt_freq.out"))
    assert d["n_modes"] == 18                       # 3N - 6 for acrolein
    assert d["frequencies_cm1"][0] == pytest.approx(198.70)
    assert d["ir_intensities_km_mol"][0] == pytest.approx(6.42)
    assert d["method"] == "B3LYP-D3BJ" and d["basis"] == "def2-SVP"
