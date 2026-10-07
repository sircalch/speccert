"""
Parser for VASP DOSCAR files (total and site-projected density of states).

Layouts handled (columns after the energy):
  total DOS:  ISPIN=1: dos, integrated;  ISPIN=2: dos_up, dos_down, int_up, int_down
  projected:  LORBIT=10 (s p d [f]) or LORBIT=11 (lm-decomposed: s py pz px dxy dyz dz2 dxz dx2-y2 [7 f]),
              with up/down columns interleaved when ISPIN=2.
Non-collinear DOSCARs (4 spin components) are rejected.
"""

from typing import Dict, Any, List, Optional, Sequence
import gzip
import os
import numpy as np

# number of projected columns -> (ISPIN, column indices (1-based, after energy at 0) of the d channels)
_PDOS_LAYOUTS = {
    (1, 3): [3], (1, 4): [3],                            # s p d [f]
    (1, 9): [5, 6, 7, 8, 9], (1, 16): [5, 6, 7, 8, 9],   # lm-decomposed s, p(3), d(5) [f(7)]
    (2, 6): [5, 6], (2, 8): [5, 6],                      # s_up s_dn p_up p_dn d_up d_dn [f]
    (2, 18): list(range(9, 19)), (2, 32): list(range(9, 19)),
}


def _open(path):
    return gzip.open(path, "rt", errors="ignore") if path.endswith(".gz") else open(path, "r", errors="ignore")


def parse_vasp_doscar(filepath: str, ions: Optional[Sequence[int]] = None) -> Dict[str, Any]:
    """
    Parses a VASP DOSCAR (plain or .gz).

    Parameters
    ----------
    filepath : str
    ions : sequence of int, optional
        1-based ion numbers whose d-projected DOS are summed (default: all ions).

    Returns
    -------
    data : dict
        energies_ev, total_dos (spin-summed), fermi_energy_ev, ispin, n_ions, projected_d_dos (summed over the
        selected ions and both spins; None without projections), projected_d_dos_by_ion (n_ions x NEDOS),
        ions_used, n_points.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with _open(filepath) as fh:
        lines = fh.read().splitlines()
    if len(lines) < 7:
        raise ValueError("Invalid or truncated VASP DOSCAR file.")

    n_ions = int(lines[0].split()[0])
    head = lines[5].split()
    nedos, fermi = int(head[2]), float(head[3])
    tot = np.array([[float(x) for x in ln.split()] for ln in lines[6:6 + nedos]])
    if tot.shape[1] == 3:
        ispin = 1
        total = tot[:, 1]
    elif tot.shape[1] == 5:
        ispin = 2
        total = tot[:, 1] + tot[:, 2]
    else:
        raise ValueError(f"Unrecognised total-DOS layout ({tot.shape[1]} columns); non-collinear DOSCARs are not supported.")
    energies = tot[:, 0]

    d_by_ion = []
    pos = 6 + nedos
    for _ in range(n_ions):
        if pos + 1 + nedos > len(lines):
            break
        block = np.array([[float(x) for x in ln.split()] for ln in lines[pos + 1:pos + 1 + nedos]])
        cols = _PDOS_LAYOUTS.get((ispin, block.shape[1] - 1))
        if cols is None:
            raise ValueError(f"Unrecognised projected-DOS layout: ISPIN={ispin}, {block.shape[1] - 1} columns.")
        d_by_ion.append(block[:, cols].sum(axis=1))
        pos += 1 + nedos

    pdos_d = None
    used = []
    if d_by_ion:
        used = list(ions) if ions is not None else list(range(1, len(d_by_ion) + 1))
        pdos_d = np.sum([d_by_ion[i - 1] for i in used], axis=0)

    return {
        "energies_ev": energies.tolist(),
        "total_dos": total.tolist(),
        "projected_d_dos": pdos_d.tolist() if pdos_d is not None else None,
        "projected_d_dos_by_ion": [x.tolist() for x in d_by_ion] or None,
        "fermi_energy_ev": fermi,
        "ispin": ispin,
        "n_ions": n_ions,
        "ions_used": used,
        "n_points": len(energies),
    }
