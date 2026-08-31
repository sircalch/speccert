"""
Generates sample UV-Vis, IR, and DOS datasets for SpecCert.
"""

import os
import pandas as pd
import numpy as np


def generate_sample_spectra_data(output_dir: str = "sample_spectra_dataset"):
    os.makedirs(output_dir, exist_ok=True)

    # 1. TD-DFT UV-Vis excitation states CSV
    e_states = [2.14, 2.30, 2.96, 3.45, 3.80, 4.10]
    f_states = [0.08, 0.15, 1.25, 0.45, 0.20, 0.10]
    df_uv = pd.DataFrame({
        "state": list(range(1, len(e_states) + 1)),
        "energy_ev": e_states,
        "wavelength_nm": [1239.84 / e for e in e_states],
        "oscillator_strength": f_states
    })
    df_uv.to_csv(os.path.join(output_dir, "porphyrin_uvvis.csv"), index=False)

    # 2. Vibrational IR table CSV
    raw_freqs = [650.0, 820.0, 1050.0, 1220.0, 1380.0, 1490.0, 1610.0, 1680.0, 3120.0, 3180.0]
    raw_intens = [30.0, 45.0, 80.0, 120.0, 95.0, 160.0, 320.0, 480.0, 15.0, 25.0]
    df_ir = pd.DataFrame({
        "mode": list(range(1, len(raw_freqs) + 1)),
        "frequency_cm1": raw_freqs,
        "intensity_km_mol": raw_intens
    })
    df_ir.to_csv(os.path.join(output_dir, "porphyrin_ir.csv"), index=False)

    # 3. DOS table CSV
    e_dos = np.linspace(-10.0, 5.0, 300)
    tdos = 1.0 / (1.0 + np.exp(-e_dos)) + 4.0 * np.exp(-0.5 * ((e_dos + 2.25) / 1.5)**2)
    pdos_d = 4.0 * np.exp(-0.5 * ((e_dos + 2.25) / 1.5)**2)
    df_dos = pd.DataFrame({
        "energy_ev": e_dos,
        "total_dos": tdos,
        "pdos_d": pdos_d
    })
    df_dos.to_csv(os.path.join(output_dir, "pt111_dos.csv"), index=False)

    print(f"Generated sample spectroscopy datasets at: {os.path.abspath(output_dir)}/")


if __name__ == "__main__":
    generate_sample_spectra_data()
