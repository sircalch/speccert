"""
TD-DFT UV-Vis excitation analysis, Gaussian line broadening, and absorption spectrum convolution.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

HC_EV_NM = 1239.841984  # Planck constant * c in eV * nm
EV_TO_CM1 = 8065.543937
# Oscillator strength and molar absorption coefficient: f = 4.319e-9 * integral(eps d nu~), nu~ in cm^-1
# (eps in L mol^-1 cm^-1). For a band normalised in eV this gives integral(eps dE) = f * EPS_PER_F_EV.
F_EPS_COEFF = 4.319e-9
EPS_PER_F_EV = 1.0 / (F_EPS_COEFF * EV_TO_CM1)  # 2.8706e4 L mol^-1 cm^-1 eV


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
    wavelength_range_nm: Optional[Tuple[float, float]] = None,
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
    wavelength_range_nm : tuple of (float, float), optional
        Plot/search window. By default it spans all transitions: from min(200 nm, shortest
        transition - 40 nm) to max(800 nm, longest transition + 100 nm), so that absorption
        maxima below 200 nm are not clipped at the edge of the grid.
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
    if wavelength_range_nm is None:
        wl_states = HC_EV_NM / np.clip(e_arr, 1e-4, None)
        wavelength_range_nm = (max(50.0, min(200.0, float(wl_states.min()) - 40.0)),
                               max(800.0, float(wl_states.max()) + 100.0))
    wl_grid = np.linspace(wavelength_range_nm[0], wavelength_range_nm[1], n_grid_points)
    e_grid = HC_EV_NM / wl_grid

    # Gaussian convolution in energy: eps(E) = EPS_PER_F_EV * sum_i f_i g(E - E_i), with g a unit-area Gaussian (eV^-1)
    eps_grid = np.zeros_like(e_grid)
    for e_i, f_i in zip(e_arr, f_arr):
        if f_i > 0:
            gauss = np.exp(-0.5 * ((e_grid - e_i) / sigma_ev)**2) / (sigma_ev * np.sqrt(2.0 * np.pi))
            eps_grid += f_i * gauss * EPS_PER_F_EV  # L mol^-1 cm^-1

    # Find lambda_max
    max_idx = int(np.argmax(eps_grid))
    lambda_max = float(wl_grid[max_idx])
    at_grid_edge = max_idx in (0, len(wl_grid) - 1)
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

    # Above the highest computed state the spectrum is incomplete: states that were not computed would add
    # intensity there. A maximum within 2 FWHM of the highest computed excitation depends on how many states
    # were requested.
    e_at_max = float(HC_EV_NM / lambda_max)
    truncated = n_states > 1 and e_at_max > float(e_arr.max()) - 2.0 * fwhm_ev
    if max_f < 1e-4:
        status = "WARNING"
        diag = "All calculated transitions are dark (largest oscillator strength < 1e-4)."
    else:
        status = "PASS"
        diag = (f"Spectrum from {n_states} states (Gaussian FWHM {fwhm_ev:.2f} eV): lambda_max = {lambda_max:.1f} nm, "
                f"eps_max = {float(eps_grid[max_idx]):.3g} L mol^-1 cm^-1, largest f = {max_f:.4f}, sum f = {tot_f:.3f}.")
        if at_grid_edge:
            status = "WARNING"
            diag += " The maximum lies at the edge of the wavelength window; widen wavelength_range_nm."
        elif truncated:
            status = "WARNING"
            diag += (f" The maximum ({e_at_max:.2f} eV) lies within 2 FWHM of the highest computed state "
                     f"({float(e_arr.max()):.2f} eV), where uncomputed states would also absorb; it depends on the "
                     f"number of states requested. Compute more states or restrict wavelength_range_nm.")

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
