"""Regression tests on real ORCA 6.1.1 TD-DFT outputs (B3LYP-D3BJ/def2-SVP, 6 roots)."""
import os

import pytest

from speccert.core.uv_vis import calculate_uv_vis_spectrum
from speccert.parsers.orca_tddft import parse_orca_tddft_output

DATA = os.path.join(os.path.dirname(__file__), "data")


def test_butadiene_bright_pi_pi_star():
    d = parse_orca_tddft_output(os.path.join(DATA, "butadiene.out"))
    assert d["n_states"] == 6
    assert d["energies_ev"][1] == pytest.approx(6.441255)
    assert d["oscillator_strengths"][1] == pytest.approx(1.310295303)
    assert "14a -> 15a" in d["transitions_character"][1]     # HOMO -> LUMO
    uv = calculate_uv_vis_spectrum(d["energies_ev"], d["oscillator_strengths"])
    # lambda_max must not be clipped at a fixed 200 nm window edge
    assert uv.lambda_max_nm == pytest.approx(192.5, abs=1.5)


def test_formaldehyde_dark_n_pi_star():
    d = parse_orca_tddft_output(os.path.join(DATA, "h2co_tddft.out"))
    assert d["energies_ev"][0] == pytest.approx(4.074539)
    assert d["oscillator_strengths"][0] == pytest.approx(0.0)       # symmetry-forbidden n -> pi*
    assert d["oscillator_strengths"][1] == pytest.approx(0.170287143)
