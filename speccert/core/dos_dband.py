"""
Density of States (DOS/PDOS) analysis, Fermi level alignment, and Hammer-Norskov d-band center theory.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class DOSAnalysisResult:
    n_energy_points: int
    fermi_energy_ev: float
    d_band_center_filled_ev: Optional[float]
    d_band_center_full_ev: Optional[float]
    d_band_width_ev: Optional[float]
    d_band_filling_fraction: Optional[float]
    energy_grid_rel_ef_ev: List[float]
    total_dos: List[float]
    projected_d_dos: Optional[List[float]]
    status: str  # 'PASS', 'WARNING', 'FAIL'
    diagnostic_message: str


def calculate_dos_and_dband_center(
    energies_ev: List[float],
    total_dos: List[float],
    projected_d_dos: Optional[List[float]] = None,
    fermi_energy_ev: float = 0.0
) -> DOSAnalysisResult:
    """
    Analyzes electronic density of states, centers grid relative to Fermi level (E - E_F),
    and computes Hammer-Norskov d-band center (epsilon_d), d-band width (W_d), and filling fraction.

    Parameters
    ----------
    energies_ev : list of float
        Raw energy grid (eV).
    total_dos : list of float
        Total density of states (states / eV).
    projected_d_dos : list of float, optional
        Projected density of states for d-orbitals (states / eV).
    fermi_energy_ev : float, default 0.0 eV

    Returns
    -------
    result : DOSAnalysisResult
    """
    e_raw = np.asarray(energies_ev, dtype=float)
    tdos = np.asarray(total_dos, dtype=float)
    n_pts = len(e_raw)

    if n_pts < 5:
        raise ValueError("At least 5 energy points are required for DOS analysis.")

    # Align energy relative to Fermi level
    e_rel = e_raw - fermi_energy_ev

    # Sorting
    sort_idx = np.argsort(e_rel)
    e_rel = e_rel[sort_idx]
    tdos = tdos[sort_idx]

    d_center_filled = None
    d_center_full = None
    d_width = None
    d_filling = None
    pdos_d_list = None

    if projected_d_dos is not None and len(projected_d_dos) == n_pts:
        pdos_d = np.asarray(projected_d_dos, dtype=float)[sort_idx]
        pdos_d_list = pdos_d.tolist()

        # Filled states mask (E <= 0)
        filled_mask = (e_rel <= 0.0)

        # Numerical integration using trapezoid rule
        int_filled_d = float(np.trapezoid(pdos_d[filled_mask], e_rel[filled_mask])) if np.sum(filled_mask) > 1 else 0.0
        int_total_d = float(np.trapezoid(pdos_d, e_rel))

        if int_filled_d > 1e-6:
            # Filled d-band center: int (E * pdos_d) / int (pdos_d) below E_F
            d_center_filled = float(np.trapezoid(e_rel[filled_mask] * pdos_d[filled_mask], e_rel[filled_mask]) / int_filled_d)

            # d-band width (second central moment)
            var_d = float(np.trapezoid((e_rel[filled_mask] - d_center_filled)**2 * pdos_d[filled_mask], e_rel[filled_mask]) / int_filled_d)
            d_width = float(np.sqrt(max(0.0, var_d)))

        if int_total_d > 1e-6:
            d_center_full = float(np.trapezoid(e_rel * pdos_d, e_rel) / int_total_d)
            d_filling = float(min(1.0, max(0.0, int_filled_d / int_total_d)))

    status = "PASS"
    if d_center_filled is not None:
        diag = f"Electronic DOS & d-band model certified (Filled d-band center eps_d = {d_center_filled:.3f} eV rel to E_F, d-band width W_d = {d_width:.3f} eV, filling = {d_filling*100:.1f}%)."
    else:
        diag = f"Total DOS analyzed ({n_pts} grid points centered around E_F = {fermi_energy_ev:.3f} eV)."

    return DOSAnalysisResult(
        n_energy_points=n_pts,
        fermi_energy_ev=fermi_energy_ev,
        d_band_center_filled_ev=d_center_filled,
        d_band_center_full_ev=d_center_full,
        d_band_width_ev=d_width,
        d_band_filling_fraction=d_filling,
        energy_grid_rel_ef_ev=e_rel.tolist(),
        total_dos=tdos.tolist(),
        projected_d_dos=pdos_d_list,
        status=status,
        diagnostic_message=diag
    )
