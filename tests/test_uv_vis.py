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


def test_oscillator_strength_sum_rule():
    from speccert.core.uv_vis import F_EPS_COEFF, HC_EV_NM
    e, f = [3.0, 4.0, 5.2], [0.2, 0.7, 0.1]
    res = calculate_uv_vis_spectrum(e, f, fwhm_ev=0.3, wavelength_range_nm=(HC_EV_NM / 7.5, HC_EV_NM / 1.0),
                                     n_grid_points=200001)
    en = HC_EV_NM / np.array(res.wavelength_grid_nm)
    eps = np.array(res.extinction_coefficient_m_minus_1_cm_minus_1)
    f_back = F_EPS_COEFF * abs(np.trapezoid(eps, en * 8065.543937))
    assert f_back == pytest.approx(1.0, rel=1e-4)


def test_maximum_at_highest_computed_state_is_flagged():
    res = calculate_uv_vis_spectrum([3.0, 4.0, 5.0], [0.05, 0.1, 0.9], fwhm_ev=0.3)
    assert res.status == "WARNING"
    assert "highest computed state" in res.diagnostic_message
