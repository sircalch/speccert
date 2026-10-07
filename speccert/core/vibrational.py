"""
Harmonic vibrational frequency scaling, IR Lorentzian broadening, and diagnostic band assignment.

Scaling factors are looked up by method and basis set in the precomputed table of NIST CCCBDB
(Computational Chemistry Comparison and Benchmark Database, SRD 101; speccert/data/cccbdb_scaling.csv). They
depend on the basis set as well as on the method: for B3LYP alone they range from 0.960 to 0.972. When no
factor is tabulated for the method and basis, the frequencies are left unscaled and the check warns.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import csv
import os
import re
import numpy as np

_TABLE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cccbdb_scaling.csv")

# user spelling (lower case, no spaces) -> CCCBDB method name. Dispersion corrections (-D3, -D3BJ, -D4) are
# dropped for B3LYP, PBE0 and PBE, whose CCCBDB factors are without dispersion; wB97X-D3 is a different
# functional from wB97X-D and is not mapped.
METHOD_ALIASES = {
    "hf": "HF", "rhf": "HF", "uhf": "HF", "lsda": "LSDA", "blyp": "BLYP", "b3lyp": "B3LYP", "b3pw91": "B3PW91",
    "mpw1pw91": "mPW1PW91", "m06-2x": "M06-2X", "m062x": "M06-2X", "pbe": "PBEPBE", "pbepbe": "PBEPBE",
    "pbe0": "PBE1PBE", "pbe1pbe": "PBE1PBE", "hse06": "HSEh1PBE", "hseh1pbe": "HSEh1PBE", "tpssh": "TPSSh",
    "wb97x-d": "wB97X-D", "wb97xd": "wB97X-D", "b97-d3": "B97D3", "b97d3": "B97D3", "mp2": "MP2", "ri-mp2": "MP2",
    "b2plyp": "B2PLYP", "ccsd(t)": "CCSD(T)",
}
_DISPERSION = re.compile(r"-?d3\(?bj\)?$|-?d3bj$|-?d3$|-?d4$")


def _norm_basis(b: str) -> str:
    b = b.lower().replace(" ", "").replace("(d,p)", "**").replace("(d)", "*")
    return b.replace("def2-", "def2").replace("_", "")


def _load_table() -> Dict[Tuple[str, str], float]:
    out = {}
    with open(_TABLE, newline="") as fh:
        for r in csv.DictReader(fh):
            out[(r["method"], _norm_basis(r["basis"]))] = float(r["factor"])
    return out


CCCBDB_FACTORS = _load_table()


def normalise_method(method: Optional[str]) -> Optional[str]:
    if not method:
        return None
    m = method.lower().replace(" ", "").replace("_", "-")
    if m in METHOD_ALIASES:
        return METHOD_ALIASES[m]
    stripped = _DISPERSION.sub("", m)
    if stripped in ("b3lyp", "pbe0", "pbe", "pbe1pbe", "blyp", "tpssh") and stripped in METHOD_ALIASES:
        return METHOD_ALIASES[stripped]
    return None


def get_recommended_scaling_factor(method: Optional[str] = None, basis: Optional[str] = None
                                   ) -> Tuple[Optional[float], str]:
    """
    CCCBDB scaling factor for a method and basis set.

    Returns (factor, source); factor is None when the combination is not tabulated.
    """
    m = normalise_method(method)
    if m is None:
        return None, f"no CCCBDB entry for method '{method}'"
    if not basis:
        return None, f"basis set not given (CCCBDB factors for {m} depend on it)"
    key = (m, _norm_basis(basis))
    if key in CCCBDB_FACTORS:
        return CCCBDB_FACTORS[key], f"CCCBDB {m}/{basis}"
    return None, f"no CCCBDB entry for {m}/{basis}"


@dataclass
class VibrationalMode:
    mode_index: int
    harmonic_freq_cm1: float
    scaled_freq_cm1: float
    ir_intensity_km_mol: Optional[float]
    raman_activity_ang4_amu: Optional[float]
    band_assignment: str


@dataclass
class VibrationalSpectrumResult:
    n_modes: int
    functional_name: str
    scaling_factor_applied: float
    frequency_grid_cm1: List[float]
    ir_absorbance_convoluted: Optional[List[float]]
    top_diagnostic_bands: List[VibrationalMode]
    status: str  # 'PASS', 'WARNING', 'FAIL'
    diagnostic_message: str
    scaling_source: str = ""
    basis_set: Optional[str] = None
    n_imaginary: int = 0


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
    n_grid_points: int = 720,
    basis: Optional[str] = None
) -> VibrationalSpectrumResult:
    """
    Scales harmonic frequencies and broadens the IR stick spectrum with area-normalised Lorentzians.

    Parameters
    ----------
    frequencies_cm1 : list of float
        Harmonic vibrational frequencies in cm^-1 (imaginary modes as negative numbers).
    ir_intensities : list of float, optional
        IR intensities in km/mol. Without them no IR spectrum is computed (only scaled frequencies).
    raman_activities : list of float, optional
        Stored with the modes; not broadened.
    functional, basis : str, optional
        Method and basis set for the CCCBDB scaling factor.
    custom_scaling_factor : float, optional
        Overrides the table.
    fwhm_cm1 : float, default 12.0 cm^-1
    freq_range_cm1 : tuple of (float, float)
    n_grid_points : int

    Returns
    -------
    result : VibrationalSpectrumResult
        ir_absorbance_convoluted is in km mol^-1 per cm^-1: its integral over a band equals the intensity.
    """
    freqs = np.asarray(frequencies_cm1, dtype=float)
    n_m = len(freqs)
    if n_m == 0:
        raise ValueError("At least one vibrational frequency is required.")

    notes = []
    if custom_scaling_factor is not None:
        scale_fac, source = float(custom_scaling_factor), "user-supplied"
    else:
        scale_fac, source = get_recommended_scaling_factor(functional, basis)
        if scale_fac is None:
            notes.append(f"Frequencies not scaled: {source}; supply custom_scaling_factor.")
            scale_fac = 1.0
    scaled_freqs = freqs * scale_fac

    n_imag = int(np.sum(freqs < 0))
    if n_imag:
        notes.append(f"{n_imag} imaginary mode(s): the structure is not a minimum.")

    grid = np.linspace(freq_range_cm1[0], freq_range_cm1[1], n_grid_points)
    absorbance = None
    ir_int = None
    if ir_intensities is not None and len(ir_intensities) == n_m:
        ir_int = np.asarray(ir_intensities, dtype=float)
        gamma = fwhm_cm1
        absorbance = np.zeros_like(grid)
        for nu_i, i_val in zip(scaled_freqs, ir_int):
            if nu_i > 0 and i_val > 0:
                absorbance += i_val * (gamma / (2.0 * np.pi)) / ((grid - nu_i) ** 2 + (gamma / 2.0) ** 2)
    else:
        notes.append("No IR intensities: no IR spectrum computed (scaled frequencies only).")

    modes = []
    for i in range(n_m):
        r_act = raman_activities[i] if raman_activities and i < len(raman_activities) else None
        modes.append(VibrationalMode(
            mode_index=i + 1,
            harmonic_freq_cm1=float(freqs[i]),
            scaled_freq_cm1=float(scaled_freqs[i]),
            ir_intensity_km_mol=float(ir_int[i]) if ir_int is not None else None,
            raman_activity_ang4_amu=float(r_act) if r_act is not None else None,
            band_assignment=assign_vibrational_band_region(scaled_freqs[i])
        ))
    key = (lambda m: m.ir_intensity_km_mol) if ir_int is not None else (lambda m: m.scaled_freq_cm1)
    top_bands = sorted(modes, key=key, reverse=True)[:10]

    if n_imag:
        status = "FAIL"
    elif notes:
        status = "WARNING"
    else:
        status = "PASS"
    diag = f"{n_m} modes, scaling factor {scale_fac:.3f} ({source if scale_fac != 1.0 or custom_scaling_factor else 'none'})."
    if absorbance is not None:
        diag += f" IR spectrum broadened with Lorentzians of FWHM {fwhm_cm1:.0f} cm^-1."
    if notes:
        diag += " " + " ".join(notes)

    return VibrationalSpectrumResult(
        n_modes=n_m,
        functional_name=functional or "not given",
        scaling_factor_applied=scale_fac,
        frequency_grid_cm1=grid.tolist(),
        ir_absorbance_convoluted=absorbance.tolist() if absorbance is not None else None,
        top_diagnostic_bands=top_bands,
        status=status,
        diagnostic_message=diag,
        scaling_source=source,
        basis_set=basis,
        n_imaginary=n_imag
    )
