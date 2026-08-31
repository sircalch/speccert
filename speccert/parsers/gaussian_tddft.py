"""
Parsers for Gaussian 16 TD-DFT excitation outputs.
"""

from typing import Dict, Any, List, Optional
import os
import re


def parse_gaussian_tddft_output(filepath: str) -> Dict[str, Any]:
    """
    Parses Gaussian 16 TD-DFT log for excited state energies and oscillator strengths.

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

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            # Excited State   1:      Singlet-A      3.2541 eV  380.99 nm  f=0.1234  <S**2>=0.000
            if "Excited State" in line:
                m = re.search(r"Excited State\s+\d+:\s+[\w\-]+\s+([-\d\.]+)\s+eV\s+([-\d\.]+)\s+nm\s+f=([-\d\.]+)", line)
                if m:
                    energies_ev.append(float(m.group(1)))
                    wavelengths_nm.append(float(m.group(2)))
                    osc_strengths.append(float(m.group(3)))

    return {
        "energies_ev": energies_ev,
        "wavelengths_nm": wavelengths_nm,
        "oscillator_strengths": osc_strengths,
        "n_states": len(energies_ev)
    }
