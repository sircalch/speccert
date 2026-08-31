# SpecCert

[![CI](https://github.com/amonreal/speccert/actions/workflows/test.yml/badge.svg)](https://github.com/amonreal/speccert/actions)
[![PyPI version](https://img.shields.io/pypi/v/speccert.svg?color=blue)](https://pypi.org/project/speccert/)
[![Python versions](https://img.shields.io/pypi/pyversions/speccert.svg)](https://pypi.org/project/speccert/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1234610.svg)](https://doi.org/10.5281/zenodo.1234610)

> **Automated Quality-Control, Spectroscopy Simulation (UV-Vis TD-DFT, IR/Raman Anharmonic Scaling), and Electronic Structure Certification (DOS & d-Band Center).**

---

## Overview

**SpecCert** is an open-source scientific software package designed to standardize, audit, and certify simulated optical and vibrational spectra, TD-DFT electronic excitations, empirical harmonic vibrational scaling (accounting for anharmonicity), and electronic density of states (DOS) / Hammer-Nørskov $d$-band center calculations ($\varepsilon_d$).

In computational spectroscopy, materials science, and physical chemistry:

- 🌈 **TD-DFT & Optical UV-Vis Spectroscopy**:
  - Convolutes discrete vertical excitation energies and oscillator strengths $f$ using Gaussian line broadening (FWHM $= 0.25-0.35\text{ eV}$).
  - Automatically identifies $\lambda_{\text{max}}$ (strongest absorption peak wavelength and molar extinction $\varepsilon$).
  - Tracks singlet/triplet character and audits total oscillator strength sum $\sum f_i$.
- 🎶 **Vibrational Spectroscopy (IR & Raman Scaling)**:
  - Applies standardized NIST CCCBDB / Merrick et al. empirical harmonic-to-anharmonic frequency scaling factors (B3LYP $= 0.9679$, PBE0 $= 0.9594$, wB97X-D $= 0.9570$, M06-2X $= 0.9520$, etc.).
  - Convolutes infrared and Raman spectra using Lorentzian lineshapes (FWHM $= 10-15\text{ cm}^{-1}$).
  - Automatically classifies diagnostic functional group regions (Carbonyl $\text{C=O}$, Hydroxyl $\text{O-H}$, $\text{C-H}$ stretch, Fingerprint).
- ⚡ **Electronic Density of States (DOS) & d-Band Center Theory**:
  - Automatically aligns energy grids to Fermi level ($E - E_F$).
  - Computes Hammer-Nørskov $d$-band center $\varepsilon_d = \frac{\int_{-\infty}^{E_F} E \cdot \rho_d(E) dE}{\int_{-\infty}^{E_F} \rho_d(E) dE}$, $d$-band width $W_d$, and filling fraction $f_d$.
- 📑 **Publication Deliverables**:
  - Interactive self-contained `report.html` dashboard.
  - Publication vector figures (UV-Vis Spectrum, Scaled IR Profile, DOS / $d$-Band Center) in SVG, PDF, PNG (300 DPI).
  - Ready-to-compile LaTeX summary tables (`.tex`).
  - Draft **Methods** text snippet and BibTeX citation (`citation.bib`).

```
       Spectroscopy Outputs (ORCA TD-DFT, Gaussian, VASP DOSCAR, CSV)
                               │
                               ▼
  ┌───────────────────────────────────────────────────────────┐
  │                         SpecCert                          │
  │  ├── TD-DFT UV-Vis Convoluted Optical Absorption Spectrum │
  │  ├── Scaled IR/Raman Vibrational Spectroscopy (CCCBDB)    │
  │  └── Electronic Density of States & d-Band Center (eps_d) │
  └───────────────────────────────────────────────────────────┘
                               │
                               ▼
  ┌───────────────────────────────────────────────────────────┐
  │                   Publication Deliverables                │
  │  ├── report.html (Interactive Dashboard & Badges)         │
  │  ├── speccert_uv_vis_spectrum.pdf/svg/png                 │
  │  ├── speccert_ir_vibrational_spectrum.pdf/svg/png         │
  │  ├── speccert_electronic_dos.pdf/svg/png                  │
  │  ├── speccert_summary_table.tex / .csv                    │
  │  ├── methods_snippet.txt (Ready for Manuscript)           │
  │  └── citation.bib (BibTeX Reference)                      │
  └───────────────────────────────────────────────────────────┘
```

---

## Installation

### From PyPI
```bash
pip install speccert
```

### From Source
```bash
git clone https://github.com/amonreal/speccert.git
cd speccert
pip install -e .[dev]
```

---

## Quickstart (CLI)

### 1. Run Benchmark Demo (Porphyrin Dye UV-Vis + Scaled IR + Pt(111) d-band)
```bash
speccert demo -o my_spectra_audit/
```
Open `my_spectra_audit/report.html` in any browser!

### 2. Assess ORCA TD-DFT Calculation
```bash
speccert assess --input-uv tddft.out --frequencies "800,1650,1720,3100" --functional "wB97X-D" -o uv_report/
```

---

## Python API Usage

```python
from speccert import (
    calculate_uv_vis_spectrum,
    calculate_scaled_vibrational_spectrum,
    calculate_dos_and_dband_center,
    assess_spectroscopy_quality
)
from speccert.reporters import (
    generate_speccert_figures,
    generate_speccert_manuscript_assets,
    generate_speccert_html_report
)

# 1. UV-Vis Spectrum
uv_res = calculate_uv_vis_spectrum(
    energies_ev=[2.14, 2.96, 3.45],
    oscillator_strengths=[0.15, 1.25, 0.45]
)

# 2. Scaled IR Vibrational Spectrum
vib_res = calculate_scaled_vibrational_spectrum(
    frequencies_cm1=[820.0, 1490.0, 1680.0, 3120.0],
    ir_intensities=[45.0, 160.0, 480.0, 25.0],
    functional="wB97X-D"
)

# 3. Density of States & d-Band Model
dos_res = calculate_dos_and_dband_center(
    energies_ev=[-6.0, -4.0, -2.25, 0.0, 2.0],
    total_dos=[0.2, 1.5, 4.0, 1.0, 0.5],
    projected_d_dos=[0.1, 1.2, 3.8, 0.2, 0.0],
    fermi_energy_ev=0.0
)

# 4. Consolidate report
report = assess_spectroscopy_quality(
    metadata={"system": "Pt-Porphyrin", "functional": "wB97X-D", "software": "ORCA"},
    uv_vis_res=uv_res,
    vib_res=vib_res,
    dos_res=dos_res
)

print(f"Overall Certification: {report.overall_status}")
print(f"Absorption Max: lambda_max = {report.uv_vis.lambda_max_nm:.1f} nm")
print(f"IR Scaling: factor = {report.vibrational.scaling_factor_applied:.4f}")
print(f"d-Band Center: eps_d = {report.dos_analysis.d_band_center_filled_ev:.3f} eV")

# 5. Export deliverables
generate_speccert_figures(report, "output_dir/")
generate_speccert_manuscript_assets(report, "output_dir/")
generate_speccert_html_report(report, "output_dir/report.html")
```

---

## Citation

If you use SpecCert in your publications, please cite:

```bibtex
@software{monreal2026speccert,
  author = {Monreal-Hern{\'a}ndez, Andre},
  title = {{SpecCert: Automated Quality-Control, Spectroscopy Simulation (UV-Vis TD-DFT, IR/Raman Anharmonic Scaling), and Electronic Structure Certification (DOS & d-Band Center)}},
  year = {2026},
  version = {1.0.0},
  publisher = {Zenodo},
  url = {https://github.com/amonreal/speccert}
}
```

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
