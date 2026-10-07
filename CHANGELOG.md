# Changelog

## 1.2.0 (2026-10-06)

Version 1.1.0 was committed but never released; 1.2.0 contains its changes (listed under 1.1.0 below) and the
following. Version 1.0.0 is the only earlier release.

### Fixed
- **Molar absorption coefficient.** ε was computed with a prefactor of 2.174e4 instead of
  1/(4.319e-9 × 8065.54) = 2.8706e4 L mol⁻¹ cm⁻¹ eV, so every spectrum was 0.757 times too low. It now matches
  ORCA's `orca_mapspc` to 1.2e-4 and integrates back to Σf.
- **λmax from a truncated set of states.** A maximum within 2 FWHM of the highest computed state now gives a
  WARNING: there, states that were not computed would also absorb.
- **Fabricated IR intensities.** Without intensities every mode was given 50 km/mol and a spectrum was drawn; the
  command line accepted only frequencies, so every IR spectrum it produced was of this kind. Without intensities
  no spectrum is made now (WARNING). New ORCA frequency parser (`parse_orca_freq_output`: frequencies, IR
  intensities and the level of theory from the input echo) and `--input-ir`.
- **Scaling factors.** One factor per functional was applied for any basis set, the values were of mixed origin
  (B3LYP 0.9679 is the 6-311+G(d,p) value of Andersson and Uvdal; BP86 and MP2 the 6-31G(d) values of Scott and
  Radom), names were matched by substring (wB97X-D3 got the wB97X-D factor) and unknown methods got 0.965. The
  factor is now looked up by method and basis set in the NIST CCCBDB table (299 factors, `speccert/data/`); if
  none is tabulated the frequencies are left unscaled with a WARNING (`--basis`, `--scaling-factor`).
- **Imaginary modes** give FAIL.
- **DOSCAR.** Only the first ion's projections were used, the total DOS of spin-polarised runs was spin-up only,
  and the d columns were wrong for ISPIN = 2 (and for lm-decomposed spin-polarised files). The parser now
  recognises ISPIN 1/2 and LORBIT 10/11 layouts (with or without f), sums both spins and all ions (`ions=`,
  `--ions`), and reads gzipped files. On three spin-polarised clusters the occupied d-band centre of 1.0.0/1.1.0
  was off by −0.22 to −0.77 eV.
- **d-band check.** WARNING without d projections or when the grid stops less than 2 eV above E_F; both the
  occupied-part and the whole-band centres are reported with their definitions.
- **Wording.** "FULLY CERTIFIED (PUBLICATION GRADE)" and "certified" are gone; labels are ALL CHECKS PASSED,
  PASSED WITH WARNINGS, AT LEAST ONE CHECK FAILED or NO CHECKS RUN. The methods paragraph states what was
  computed and found. Version and citation come from `speccert.__version__` (`speccert/citation.py`).

### Validation (`validation/`)
- `make_spec_inputs.py`, `run_orca.py`, `benchmark_uv_ir.py`: eight molecules, ORCA 6.1.1 B3LYP-D3(BJ)/def2-SVP
  optimisation + frequencies + TD-DFT, against `orca_mapspc` and the `.hess` files.
- `extract_cccbdb.py`: CCCBDB scaling-factor table (page saved 2026-10-06).
- `fetch_nomad_doscar.py`, `benchmark_dos.py`: nine VASP calculations from NOMAD against pymatgen.
- `make_figures.py`: figures and tables.

## 1.1.0 (committed, not released)

### Fixed (validated on real ORCA 6.1.1 TD-DFT outputs, `validation/orca_runs/`)
- **ORCA TD-DFT parser.** It found no transitions in real ORCA outputs, because it looked for `f=` on the
  `STATE n:` line, where ORCA does not print it. Energies, wavelengths and oscillator strengths are now read
  from the `ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS` table, in both the ORCA 6 (eV) and
  ORCA 5 (cm⁻¹) layouts. The dominant orbital excitation of each state is also reported.
- **λmax clipped at 200 nm.** The spectral window was fixed at 200–800 nm, so any absorption maximum below
  200 nm was reported as 200.0 nm. The window now spans all computed transitions by default, and a warning
  is raised if the maximum still falls on the window edge.
- The demo output is labelled as synthetic data.

### Validation
- **trans-Butadiene.** π→π* (HOMO→LUMO) transition at 6.44 eV with f = 1.31; λmax = 192.8 nm (previously
  reported as 200.0 nm).
- **Formaldehyde.** The n→π* transition at 4.07 eV is dark (f = 0); the first bright state is at 8.20 eV.

### Not yet validated
- Gaussian TD-DFT parser (no Gaussian installation available) and VASP DOSCAR parser.

## 1.0.0 (2026-08-31)

Initial release.
