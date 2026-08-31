"""
Tests for parsers (ORCA TD-DFT, Gaussian TD-DFT, VASP DOSCAR, CSV) in SpecCert.
"""

import os
import tempfile
import numpy as np
import pytest
from speccert.parsers.orca_tddft import parse_orca_tddft_output
from speccert.parsers.generic_spectra_csv import parse_spectral_csv


def test_orca_tddft_parser():
    content = """
-----------------------------------------------------------------------------
         ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS
-----------------------------------------------------------------------------
  STATE  1:  E=   0.119420 au      3.250 eV    381.5 nm  f=  0.1542
  STATE  2:  E=   0.145600 au      3.962 eV    313.0 nm  f=  0.0210
  STATE  3:  E=   0.165000 au      4.490 eV    276.1 nm  f=  0.8900
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".out", delete=False) as f:
        f.write(content)
        f_path = f.name

    try:
        data = parse_orca_tddft_output(f_path)
        assert data["n_states"] == 3
        assert np.isclose(data["energies_ev"][0], 3.250)
        assert np.isclose(data["oscillator_strengths"][2], 0.8900)
    finally:
        if os.path.exists(f_path):
            os.remove(f_path)


def test_generic_spectral_csv_parser():
    content = """energy,f,frequency,intensity
2.5,0.12,1750.0,200.0
3.0,0.85,3050.0,50.0
3.5,0.05,650.0,30.0
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(content)
        f_path = f.name

    try:
        data = parse_spectral_csv(f_path)
        assert data["n_rows"] == 3
        assert data["energies_ev"] == [2.5, 3.0, 3.5]
        assert data["oscillator_strengths"] == [0.12, 0.85, 0.05]
        assert data["frequencies_cm1"] == [1750.0, 3050.0, 650.0]
    finally:
        if os.path.exists(f_path):
            os.remove(f_path)
