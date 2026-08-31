"""
Parser for generic tabular CSV / TSV spectroscopy and DOS data.
"""

from typing import Dict, Any, List, Optional
import os
import pandas as pd


def parse_spectral_csv(filepath: str) -> Dict[str, Any]:
    """
    Parses generic CSV/TSV table for UV-Vis (wavelength, oscillator strength),
    IR (frequency, intensity), or DOS (energy, tdos, pdos_d).

    Parameters
    ----------
    filepath : str

    Returns
    -------
    data : dict
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    sep = r"\s+" if filepath.endswith(".dat") else ("," if filepath.endswith(".csv") else None)
    df = pd.read_csv(filepath, sep=sep, engine="python" if sep is None else None)

    col_map = {}
    for c in df.columns:
        c_low = str(c).lower().strip()
        if c_low in ["energy", "e", "energy_ev", "e_ev"]:
            col_map[c] = "energy"
        elif c_low in ["wavelength", "wl", "wavelength_nm", "lambda"]:
            col_map[c] = "wavelength"
        elif c_low in ["f", "osc", "oscillator_strength", "f_osc"]:
            col_map[c] = "oscillator_strength"
        elif c_low in ["frequency", "freq", "frequency_cm1", "freq_cm1", "wavenumber", "nu", "cm-1"]:
            col_map[c] = "frequency"
        elif c_low in ["intensity", "ir_intensity", "intensity_km_mol", "absorbance", "eps"]:
            col_map[c] = "intensity"
        elif c_low in ["tdos", "total_dos", "dos"]:
            col_map[c] = "tdos"
        elif c_low in ["pdos_d", "d_dos", "d_band", "pdos"]:
            col_map[c] = "pdos_d"

    df = df.rename(columns=col_map)

    res = {}
    if "energy" in df.columns:
        res["energies_ev"] = df["energy"].astype(float).tolist()
    if "wavelength" in df.columns:
        res["wavelengths_nm"] = df["wavelength"].astype(float).tolist()
    if "oscillator_strength" in df.columns:
        res["oscillator_strengths"] = df["oscillator_strength"].astype(float).tolist()
    if "frequency" in df.columns:
        res["frequencies_cm1"] = df["frequency"].astype(float).tolist()
    if "intensity" in df.columns:
        res["intensities"] = df["intensity"].astype(float).tolist()
    if "tdos" in df.columns:
        res["total_dos"] = df["tdos"].astype(float).tolist()
    if "pdos_d" in df.columns:
        res["projected_d_dos"] = df["pdos_d"].astype(float).tolist()

    res["n_rows"] = len(df)
    return res
