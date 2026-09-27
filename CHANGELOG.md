# Changelog

## 1.1.0 (unreleased)

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
