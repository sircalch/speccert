"""
Parsers for ORCA TD-DFT / CIS and IR/Raman frequency outputs.
"""

from typing import Dict, Any, List, Optional
import os
import re


def parse_orca_tddft_output(filepath: str) -> Dict[str, Any]:
    """
    Parses ORCA TD-DFT calculation log for excitation energies and oscillator strengths.

    Parameters
    ----------
    filepath : str

    Returns
    -------
    data : dict
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    energies_ev = []
    osc_strengths = []
    wavelengths_nm = []
    transitions = []

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Pattern for ORCA TD-DFT / CIS absorption summary:
    # STATE  1:  E=   0.123456 au      3.359 eV    369.1 nm  f=  0.0854
    pattern = r"STATE\s+(\d+):\s+E=\s+([-\d\.]+)\s+au\s+([-\d\.]+)\s+eV\s+([-\d\.]+)\s+nm\s+f=\s+([-\d\.]+)"
    matches = re.findall(pattern, content)

    for m in matches:
        st_idx = int(m[0])
        e_ev = float(m[2])
        wl_nm = float(m[3])
        f_val = float(m[4])
        energies_ev.append(e_ev)
        wavelengths_nm.append(wl_nm)
        osc_strengths.append(f_val)
        transitions.append(f"State {st_idx}")

    return {
        "energies_ev": energies_ev,
        "wavelengths_nm": wavelengths_nm,
        "oscillator_strengths": osc_strengths,
        "transitions_character": transitions,
        "n_states": len(energies_ev)
    }
