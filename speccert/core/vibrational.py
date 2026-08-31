"""
Harmonic vibrational frequency scaling, IR/Raman Lorentzian broadening, and diagnostic band assignment.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

# NIST CCCBDB / Merrick et al. (2007) Recommended Vibrational Scaling Factors
STANDARD_SCALING_FACTORS = {
    "b3lyp": 0.9679,
    "b3lyp-d3": 0.9679,
    "pbe0": 0.9594,
    "pbe0-d3": 0.9594,
    "wb97x-d": 0.9570,
    "wb97x-d3": 0.9570,
    "wb97x-d4": 0.9570,
    "m06-2x": 0.9520,
    "pbe": 0.9850,
    "bp86": 0.9914,
    "hf": 0.8992,
    "mp2": 0.9427
}


@dataclass
class VibrationalMode:
    mode_index: int
    harmonic_freq_cm1: float
    scaled_freq_cm1: float
    ir_intensity_km_mol: float
    raman_activity_ang4_amu: Optional[float]
    band_assignment: str


@dataclass
class VibrationalSpectrumResult:
    n_modes: int
    functional_name: str
    scaling_factor_applied: float
    frequency_grid_cm1: List[float]
    ir_absorbance_convoluted: List[float]
    top_diagnostic_bands: List[VibrationalMode]
    status: str  # 'PASS', 'WARNING', 'FAIL'
    diagnostic_message: str


def get_recommended_scaling_factor(functional: Optional[str] = None) -> float:
    """
    Returns empirical harmonic vibrational scaling factor for specified functional.
    """
    if not functional:
        return 0.9650
    f_low = functional.lower().replace("_", "-").replace(" ", "")
    for k, v in STANDARD_SCALING_FACTORS.items():
        if k in f_low:
            return v
    return 0.9650


def assign_vibrational_band_region(freq_cm1: float) -> str:
    """
    Categorizes infrared frequency into chemical functional group regions.
    """
    f = abs(freq_cm1)
    if f >= 3200.0:
        return "O-H / N-H / Alkyne C-H Stretch Region"
    elif f >= 2800.0:
        return "Aliphatic / Aromatic C-H Stretch Region"
    elif f >= 2000.0:
        return "Triple Bond / Cumulated Double Bond Region (C#C, C#N, N=C=O)"
    elif f >= 1600.0:
        return "Carbonyl (C=O) / Alkene (C=C) / Amide Region"
    elif f >= 1400.0:
        return "C-H Bending / Aromatic Skeletal Region"
    elif f >= 1000.0:
        return "C-O / C-N Stretch / Fingerprint Region"
    elif f >= 600.0:
        return "Low-Frequency Out-of-Plane Bending / Halogen Stretch"
    else:
        return "Far-IR / Soft Skeletal Torsional Region"


def calculate_scaled_vibrational_spectrum(
    frequencies_cm1: List[float],
    ir_intensities: Optional[List[float]] = None,
    raman_activities: Optional[List[float]] = None,
    functional: Optional[str] = "B3LYP",
    custom_scaling_factor: Optional[float] = None,
    fwhm_cm1: float = 12.0,
    freq_range_cm1: Tuple[float, float] = (400.0, 4000.0),
    n_grid_points: int = 720
) -> VibrationalSpectrumResult:
    """
    Applies empirical harmonic scaling factors and convolutes IR/Raman vibrational spectra
    with Lorentzian lineshapes.

    Parameters
    ----------
    frequencies_cm1 : list of float
        Harmonic vibrational frequencies in cm^-1.
    ir_intensities : list of float, optional
        IR intensities in km/mol.
    raman_activities : list of float, optional
    functional : str, optional
    custom_scaling_factor : float, optional
    fwhm_cm1 : float, default 12.0 cm^-1
    freq_range_cm1 : tuple of (float, float)
    n_grid_points : int

    Returns
    -------
    result : VibrationalSpectrumResult
    """
    freqs = np.asarray(frequencies_cm1, dtype=float)
    n_m = len(freqs)
    if n_m == 0:
        raise ValueError("At least one vibrational frequency is required.")

    # Determine scaling factor
    scale_fac = custom_scaling_factor if custom_scaling_factor is not None else get_recommended_scaling_factor(functional)
    scaled_freqs = freqs * scale_fac

    # Default IR intensities if none provided (e.g. uniform)
    if ir_intensities is not None and len(ir_intensities) == n_m:
        ir_int = np.asarray(ir_intensities, dtype=float)
    else:
        ir_int = np.ones(n_m, dtype=float) * 50.0

    # Frequency grid
    grid = np.linspace(freq_range_cm1[0], freq_range_cm1[1], n_grid_points)
    gamma = fwhm_cm1

    # Lorentzian convolution: A(nu) = sum_i I_i * (gamma / (2*pi)) / ((nu - nu_i_scaled)^2 + (gamma/2)^2)
    absorbance = np.zeros_like(grid)
    for nu_i, i_val in zip(scaled_freqs, ir_int):
        if nu_i > 0 and i_val > 0:
            lorentz = (gamma / (2.0 * np.pi)) / ((grid - nu_i)**2 + (gamma / 2.0)**2)
            absorbance += i_val * lorentz

    # Create top diagnostic modes
    modes = []
    for i in range(n_m):
        r_act = raman_activities[i] if raman_activities and i < len(raman_activities) else None
        modes.append(VibrationalMode(
            mode_index=i + 1,
            harmonic_freq_cm1=float(freqs[i]),
            scaled_freq_cm1=float(scaled_freqs[i]),
            ir_intensity_km_mol=float(ir_int[i]),
            raman_activity_ang4_amu=float(r_act) if r_act is not None else None,
            band_assignment=assign_vibrational_band_region(scaled_freqs[i])
        ))

    # Sort top bands by IR intensity
    top_bands = sorted(modes, key=lambda m: m.ir_intensity_km_mol, reverse=True)[:10]

    status = "PASS"
    diag = f"Harmonic vibrational frequencies scaled by factor {scale_fac:.4f} ({functional or 'DFT'}). Convoluted IR absorption spectrum generated ({n_m} modes across {freq_range_cm1[0]:.0f}-{freq_range_cm1[1]:.0f} cm^-1)."

    return VibrationalSpectrumResult(
        n_modes=n_m,
        functional_name=functional or "DFT",
        scaling_factor_applied=scale_fac,
        frequency_grid_cm1=grid.tolist(),
        ir_absorbance_convoluted=absorbance.tolist(),
        top_diagnostic_bands=top_bands,
        status=status,
        diagnostic_message=diag
    )
