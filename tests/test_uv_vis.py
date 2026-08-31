"""
Tests for TD-DFT UV-Vis excitation analysis and Gaussian broadening.
"""

import numpy as np
import pytest
from speccert.core.uv_vis import calculate_uv_vis_spectrum


def test_uv_vis_simulation_pass():
    energies = [2.5, 3.2, 4.0]
    osc_f = [0.1, 0.8, 0.2]

    res = calculate_uv_vis_spectrum(
        energies_ev=energies,
        oscillator_strengths=osc_f,
        fwhm_ev=0.30
    )

    assert res.status == "PASS"
    assert res.n_states == 3
    assert np.isclose(res.max_oscillator_strength, 0.8)
    assert np.isclose(res.total_oscillator_strength, 1.1)
    # Peak near 3.2 eV is ~ 387 nm
    assert 350.0 < res.lambda_max_nm < 420.0
    assert len(res.wavelength_grid_nm) == 600


def test_uv_vis_dark_transitions_warning():
    energies = [2.5, 3.2]
    osc_f = [0.0, 0.0]  # Optically dark

    res = calculate_uv_vis_spectrum(
        energies_ev=energies,
        oscillator_strengths=osc_f
    )

    assert res.status == "WARNING"
