"""
Parsers for VASP DOSCAR density of states files.
"""

from typing import Dict, Any, List, Optional
import os
import numpy as np


def parse_vasp_doscar(filepath: str) -> Dict[str, Any]:
    """
    Parses VASP DOSCAR file to extract energy grid, Fermi level, Total DOS, and Projected d-DOS.

    Parameters
    ----------
    filepath : str

    Returns
    -------
    data : dict
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    energies = []
    total_dos = []
    pdos_d = []
    fermi_energy = 0.0

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    if len(lines) < 6:
        raise ValueError("Invalid or truncated VASP DOSCAR file.")

    # Header line 6: EMAX, EMIN, NEDOS, E_FERMI, 1.0
    header_6 = lines[5].split()
    if len(header_6) >= 4:
        fermi_energy = float(header_6[3])
        nedos = int(header_6[2])
    else:
        nedos = len(lines) - 6

    # Total DOS block
    for i in range(6, min(6 + nedos, len(lines))):
        parts = lines[i].split()
        if len(parts) >= 3:
            e = float(parts[0])
            dos_val = float(parts[1])
            energies.append(e)
            total_dos.append(dos_val)

    # Check for site-projected DOS block (if present)
    # Start after total dos header
    pdos_start = 6 + nedos + 1
    if len(lines) > pdos_start + nedos:
        # First ion projected DOS
        # Format typical: energy s p_y p_z p_x d_xy d_yz d_z2 d_xz d_x2-y2
        pdos_d_vals = []
        for i in range(pdos_start, min(pdos_start + nedos, len(lines))):
            parts = lines[i].split()
            if len(parts) >= 10:
                # Sum 5 d-orbitals: indices 5, 6, 7, 8, 9
                d_sum = sum(float(parts[k]) for k in range(5, 10))
                pdos_d_vals.append(d_sum)
            elif len(parts) >= 4:
                # s, p, d format (index 3 is d)
                pdos_d_vals.append(float(parts[3]))
        if len(pdos_d_vals) == len(energies):
            pdos_d = pdos_d_vals

    return {
        "energies_ev": energies,
        "total_dos": total_dos,
        "projected_d_dos": pdos_d if pdos_d else None,
        "fermi_energy_ev": fermi_energy,
        "n_points": len(energies)
    }
