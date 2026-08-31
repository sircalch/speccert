"""
Tests for electronic density of states (DOS) and Hammer-Norskov d-band center.
"""

import numpy as np
import pytest
from speccert.core.dos_dband import calculate_dos_and_dband_center


def test_dos_and_dband_center_calculation():
    e_grid = np.linspace(-10.0, 5.0, 300)
    # Gaussian d-band centered at -2.0 eV
    pdos_d = 5.0 * np.exp(-0.5 * ((e_grid + 2.0) / 1.0)**2)
    tdos = pdos_d + 1.0

    res = calculate_dos_and_dband_center(
        energies_ev=e_grid.tolist(),
        total_dos=tdos.tolist(),
        projected_d_dos=pdos_d.tolist(),
        fermi_energy_ev=0.0
    )

    assert res.status == "PASS"
    assert res.d_band_center_filled_ev is not None
    # d-band center should be approximately -2.0 eV
    assert np.isclose(res.d_band_center_filled_ev, -2.0, atol=0.15)
    assert res.d_band_width_ev is not None
    assert res.d_band_filling_fraction is not None
