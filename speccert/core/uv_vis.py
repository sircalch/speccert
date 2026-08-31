"""
TD-DFT UV-Vis excitation analysis, Gaussian line broadening, and absorption spectrum convolution.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

HC_EV_NM = 1239.841984  # Planck constant * c in eV * nm


@dataclass
class ExcitedStateTransition:
    state_index: int
    energy_ev: float
    wavelength_nm: float
    oscillator_strength: float
    dominant_character: Optional[str]  # e.g., "HOMO -> LUMO (92%)"
    spin_multiplicity: int             # 1 for Singlet, 3 for Triplet


@dataclass
class UVVisResult:
    n_states: int
    lambda_max_nm: float
    max_oscillator_strength: float
    total_oscillator_strength: float
    transitions: List[ExcitedStateTransition]
    wavelength_grid_nm: List[float]
    extinction_coefficient_m_minus_1_cm_minus_1: List[float]
    status: str  # 'PASS', 'WARNING', 'FAIL'
    diagnostic_message: str


def calculate_uv_vis_spectrum(
    energies_ev: List[float],
    oscillator_strengths: List[float],
    transitions_character: Optional[List[str]] = None,
    spin_multiplicities: Optional[List[int]] = None,
    fwhm_ev: float = 0.30,
    wavelength_range_nm: Tuple[float, float] = (200.0, 800.0),
    n_grid_points: int = 600
) -> UVVisResult:
    """
    Simulates optical absorption spectrum from TD-DFT vertical excitation energies
    and oscillator strengths using Gaussian line-shape convolution.

    Parameters
    ----------
    energies_ev : list of float
        Excited state vertical transition energies (eV).
    oscillator_strengths : list of float
        Electric dipole oscillator strengths (dimensionless).
    transitions_character : list of str, optional
    spin_multiplicities : list of int, optional
    fwhm_ev : float, default 0.30 eV
        Full Width at Half Maximum for Gaussian broadening.
    wavelength_range_nm : tuple of (float, float)
    n_grid_points : int

    Returns
    -------
    result : UVVisResult
    """
    e_arr = np.asarray(energies_ev, dtype=float)
    f_arr = np.asarray(oscillator_strengths, dtype=float)
    n_states = len(e_arr)

    if n_states == 0:
        raise ValueError("At least one excited state transition is required for UV-Vis simulation.")

    # Convert FWHM to Gaussian standard deviation sigma = FWHM / (2 * sqrt(2 * ln 2))
    sigma_ev = fwhm_ev / (2.0 * np.sqrt(2.0 * np.log(2.0)))

    # Wavelength grid (nm) and corresponding energy grid (eV)
    wl_grid = np.linspace(wavelength_range_nm[0], wavelength_range_nm[1], n_grid_points)
    e_grid = HC_EV_NM / wl_grid

    # Gaussian convolution: epsilon(E) = (1.3062974e8 / FWHM_cm) * sum f_i * exp(-4 ln2 * ((E - E_i)/FWHM)^2)
    # in standard standard units:
    eps_grid = np.zeros_like(e_grid)
    for e_i, f_i in zip(e_arr, f_arr):
        if f_i > 0:
            gauss = np.exp(-0.5 * ((e_grid - e_i) / sigma_ev)**2) / (sigma_ev * np.sqrt(2.0 * np.pi))
            eps_grid += f_i * gauss * 2.174e4  # Scale to typical molar absorption units L/(mol*cm)

    # Find lambda_max
    max_idx = int(np.argmax(eps_grid))
    lambda_max = float(wl_grid[max_idx])
    max_f = float(np.max(f_arr))
    tot_f = float(np.sum(f_arr))

    # Transitions list
    trans_list = []
    for i in range(n_states):
        w_nm = float(HC_EV_NM / max(1e-4, e_arr[i]))
        ch_str = transitions_character[i] if transitions_character and i < len(transitions_character) else None
        s_mult = spin_multiplicities[i] if spin_multiplicities and i < len(spin_multiplicities) else 1
        trans_list.append(ExcitedStateTransition(
            state_index=i + 1,
            energy_ev=float(e_arr[i]),
            wavelength_nm=w_nm,
            oscillator_strength=float(f_arr[i]),
            dominant_character=ch_str,
            spin_multiplicity=s_mult
        ))

    # Diagnostic & status
    if max_f < 1e-4:
        status = "WARNING"
        diag = "All calculated transitions are optically dark / forbidden (max oscillator strength f < 0.0001)."
    else:
        status = "PASS"
        diag = f"UV-Vis absorption spectrum successfully simulated ({n_states} states, lambda_max = {lambda_max:.1f} nm, max f = {max_f:.4f}, sum(f) = {tot_f:.3f})."

    return UVVisResult(
        n_states=n_states,
        lambda_max_nm=lambda_max,
        max_oscillator_strength=max_f,
        total_oscillator_strength=tot_f,
        transitions=trans_list,
        wavelength_grid_nm=wl_grid.tolist(),
        extinction_coefficient_m_minus_1_cm_minus_1=eps_grid.tolist(),
        status=status,
        diagnostic_message=diag
    )
