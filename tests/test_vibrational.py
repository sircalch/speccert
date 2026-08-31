"""
Tests for empirical vibrational scaling and IR Lorentzian convolution.
"""

import numpy as np
import pytest
from speccert.core.vibrational import calculate_scaled_vibrational_spectrum, get_recommended_scaling_factor


def test_vibrational_scaling_and_convolution():
    raw_freqs = [800.0, 1500.0, 1750.0, 3100.0]
    intens = [20.0, 50.0, 250.0, 40.0]

    scale_fac = get_recommended_scaling_factor("B3LYP")
    assert np.isclose(scale_fac, 0.9679)

    res = calculate_scaled_vibrational_spectrum(
        frequencies_cm1=raw_freqs,
        ir_intensities=intens,
        functional="B3LYP",
        fwhm_cm1=12.0
    )

    assert res.status == "PASS"
    assert res.n_modes == 4
    assert np.isclose(res.scaling_factor_applied, 0.9679)
    assert len(res.top_diagnostic_bands) == 4
    assert res.top_diagnostic_bands[0].harmonic_freq_cm1 == 1750.0
    assert "Carbonyl" in res.top_diagnostic_bands[0].band_assignment
