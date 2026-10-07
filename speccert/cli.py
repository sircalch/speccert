"""
Command Line Interface (CLI) for SpecCert.
"""

import sys
import os
import argparse
import numpy as np

from speccert import __version__
from speccert import __version__
from speccert.citation import APA, BIBTEX
from speccert.parsers.orca_tddft import parse_orca_tddft_output
from speccert.parsers.orca_freq import parse_orca_freq_output
from speccert.parsers.gaussian_tddft import parse_gaussian_tddft_output
from speccert.parsers.vasp_doscar import parse_vasp_doscar
from speccert.parsers.generic_spectra_csv import parse_spectral_csv

from speccert.core.uv_vis import calculate_uv_vis_spectrum
from speccert.core.vibrational import calculate_scaled_vibrational_spectrum
from speccert.core.dos_dband import calculate_dos_and_dband_center
from speccert.core.scoring import assess_spectroscopy_quality

from speccert.reporters.plot_generator import generate_speccert_figures
from speccert.reporters.manuscript_prep import generate_speccert_manuscript_assets
from speccert.reporters.html_report import generate_speccert_html_report


def print_banner():
    banner = rf"""
   _____                     _____          _   
  / ____|                   / ____|        | |  
 | (___  _ __   ___  ___   | |     ___ _ __| |_ 
  \___ \| '_ \ / _ \/ __|  | |    / _ \ '__| __|
  ____) | |_) |  __/ (__   | |___|  __/ |  | |_ 
 |_____/| .__/ \___|\___|___\_____\___|_|   \__| v{__version__}
        | |            |___/                    
        |_|                                     

 Spectroscopy Simulation, TD-DFT UV-Vis, IR Scaling & d-Band Center Toolkit
 Monreal-Hernández et al., 2026
"""
    print(banner)


def run_demo(output_dir: str = "speccert_demo_output"):
    """
    Executes a benchmark demonstration evaluating a complete spectroscopic profile:
    1. TD-DFT UV-Vis Absorption (Porphyrin Soret & Q-bands, lambda_max = 418.5 nm)
    2. Scaled IR Vibrational Spectrum (wB97X-D / def2-TZVP scaled by 0.9570)
    3. Electronic Density of States (Pt surface with filled d-band center eps_d = -2.25 eV).
    """
    print(f"\n[SpecCert] Running demonstration benchmark on Multi-Technique Spectroscopy (Porphyrin Dye & Pt Surface)...")
    os.makedirs(output_dir, exist_ok=True)

    metadata = {
        "system": "Platinum(II) Tetraphenylporphyrin / Pt(111) Surface",
        "functional": "wB97X-D / def2-TZVP",
        "software": "SYNTHETIC DEMO DATA (ORCA/VASP-like outputs; not real calculations)"
    }

    # 1. TD-DFT UV-Vis excitation states
    # Soret band (State 1: ~418 nm, strong f=1.25), Q-bands (~540 nm, f=0.15, ~580 nm, f=0.08)
    e_states = [2.14, 2.30, 2.96, 3.45, 3.80, 4.10]
    f_states = [0.08, 0.15, 1.25, 0.45, 0.20, 0.10]
    ch_states = [
        "HOMO -> LUMO (Q-band)",
        "HOMO-1 -> LUMO (Q-band)",
        "HOMO -> LUMO+1 (Soret B-band)",
        "HOMO-2 -> LUMO+1",
        "HOMO-3 -> LUMO",
        "HOMO-1 -> LUMO+2"
    ]

    print("  -> Convoluting TD-DFT vertical excitations into UV-Vis optical absorption spectrum...")
    uv_res = calculate_uv_vis_spectrum(
        energies_ev=e_states,
        oscillator_strengths=f_states,
        transitions_character=ch_states,
        fwhm_ev=0.28
    )

    # 2. Scaled IR vibrational spectrum
    # Frequencies for aromatic ring C-H, C=C, C=N, C-C
    raw_freqs = [650.0, 820.0, 1050.0, 1220.0, 1380.0, 1490.0, 1610.0, 1680.0, 3120.0, 3180.0]
    raw_intens = [30.0, 45.0, 80.0, 120.0, 95.0, 160.0, 320.0, 480.0, 15.0, 25.0]

    print("  -> Applying empirical harmonic scaling (0.9570 for wB97X-D) and convoluting IR spectrum...")
    vib_res = calculate_scaled_vibrational_spectrum(
        frequencies_cm1=raw_freqs,
        ir_intensities=raw_intens,
        functional="wB97X-D",
        fwhm_cm1=12.0
    )

    # 3. Density of States & Hammer-Norskov d-Band Center
    print("  -> Computing electronic density of states and Hammer-Norskov d-band center (eps_d)...")
    e_dos = np.linspace(-10.0, 5.0, 500)
    # Model d-band centered at -2.25 eV below E_F
    tdos = 1.0 / (1.0 + np.exp(-e_dos)) + 4.0 * np.exp(-0.5 * ((e_dos + 2.25) / 1.5)**2)
    pdos_d = 4.0 * np.exp(-0.5 * ((e_dos + 2.25) / 1.5)**2)

    dos_res = calculate_dos_and_dband_center(
        energies_ev=e_dos.tolist(),
        total_dos=tdos.tolist(),
        projected_d_dos=pdos_d.tolist(),
        fermi_energy_ev=0.0
    )

    report = assess_spectroscopy_quality(
        metadata=metadata,
        uv_vis_res=uv_res,
        vib_res=vib_res,
        dos_res=dos_res
    )

    print("  -> Generating publication-ready vector figures (UV-Vis Spectrum, Scaled IR Profile, DOS & d-Band)...")
    generate_speccert_figures(report, output_dir)

    print("  -> Drafting manuscript Methods text snippet, summary LaTeX tables, and BibTeX citations...")
    assets = generate_speccert_manuscript_assets(report, output_dir)

    with open(assets["methods_text"], "r", encoding="utf-8") as f:
        methods_txt = f.read()
    with open(assets["citation_bib"], "r", encoding="utf-8") as f:
        bib_txt = f.read()

    html_p = os.path.join(output_dir, "report.html")
    print(f"  -> Writing interactive report to {html_p}...")
    generate_speccert_html_report(report, html_p, methods_text=methods_txt, citation_bib=bib_txt)

    print("\n" + "="*70)
    print(f" [RESULT] Overall status: {report.overall_status}")
    print(f" [SCORE]  {report.validation_score}")
    print("="*70)
    print(f" * Target System    : {report.metadata['system']}")
    print(f" * UV-Vis Absorption: lambda_max = {report.uv_vis.lambda_max_nm:.1f} nm (f_max = {report.uv_vis.max_oscillator_strength:.4f}, sum(f) = {report.uv_vis.total_oscillator_strength:.3f})")
    print(f" * IR Vibrational   : Scaling = {report.vibrational.scaling_factor_applied:.4f} ({report.vibrational.n_modes} modes convoluted)")
    print(f" * d-Band Center    : eps_d = {report.dos_analysis.d_band_center_filled_ev:.3f} eV rel to E_F (Width W_d = {report.dos_analysis.d_band_width_ev:.3f} eV, Filling = {report.dos_analysis.d_band_filling_fraction*100:.1f}%)")
    print("="*70)
    print(f"\nAll outputs successfully saved to: {os.path.abspath(output_dir)}/")
    print(f"Open {os.path.abspath(html_p)} in your browser to inspect the full report.\n")


def run_assess(args):
    """
    Evaluates user-provided spectroscopy or electronic structure files.
    """
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    uv_res = None
    vib_res = None
    dos_res = None

    # 1. UV-Vis input
    if args.input_uv:
        print(f"\n[SpecCert] Parsing UV-Vis data from: {args.input_uv}...")
        if args.input_uv.endswith(".out") or args.input_uv.endswith(".log"):
            try:
                data = parse_orca_tddft_output(args.input_uv)
            except Exception:
                data = parse_gaussian_tddft_output(args.input_uv)
        else:
            data = parse_spectral_csv(args.input_uv)

        if "energies_ev" in data and "oscillator_strengths" in data:
            uv_res = calculate_uv_vis_spectrum(
                energies_ev=data["energies_ev"],
                oscillator_strengths=data["oscillator_strengths"],
                fwhm_ev=args.uv_fwhm
            )

    # 2. Vibrational input: an ORCA frequency output (frequencies + IR intensities + level of theory), or a list
    # of frequencies (no intensities, so no IR spectrum)
    method, basis = args.functional, args.basis
    if args.input_ir:
        print(f"\n[SpecCert] Parsing frequencies and IR intensities from: {args.input_ir}...")
        if args.input_ir.lower().endswith((".out", ".log")):
            fq = parse_orca_freq_output(args.input_ir)
            freqs, intens = fq["frequencies_cm1"], fq["ir_intensities_km_mol"]
            method, basis = method or fq["method"], basis or fq["basis"]
            print(f"  -> {fq['n_modes']} modes, level of theory read from the input: {fq['method']} / {fq['basis']}")
        else:
            c = parse_spectral_csv(args.input_ir)
            freqs, intens = c.get("frequencies_cm1"), c.get("intensities")
        vib_res = calculate_scaled_vibrational_spectrum(
            frequencies_cm1=freqs, ir_intensities=intens, functional=method, basis=basis,
            custom_scaling_factor=args.scaling_factor)
    elif args.frequencies:
        freq_list = [float(x) for x in args.frequencies.split(",")]
        vib_res = calculate_scaled_vibrational_spectrum(
            frequencies_cm1=freq_list, functional=method, basis=basis, custom_scaling_factor=args.scaling_factor)

    # 3. DOS input
    if args.input_dos:
        print(f"\n[SpecCert] Parsing DOS data from: {args.input_dos}...")
        if "doscar" in args.input_dos.lower():
            ions = [int(x) for x in args.ions.split(",")] if args.ions else None
            dos_data = parse_vasp_doscar(args.input_dos, ions=ions)
            print(f"  -> ISPIN = {dos_data['ispin']}, {dos_data['n_ions']} ions, d-DOS summed over ions "
                  f"{dos_data['ions_used'] if args.ions else 'all'}")
        else:
            dos_data = parse_spectral_csv(args.input_dos)

        if "energies_ev" in dos_data and "total_dos" in dos_data:
            dos_res = calculate_dos_and_dband_center(
                energies_ev=dos_data["energies_ev"],
                total_dos=dos_data["total_dos"],
                projected_d_dos=dos_data.get("projected_d_dos"),
                fermi_energy_ev=dos_data.get("fermi_energy_ev", 0.0)
            )

    meta = {
        "system": args.system or "the system",
        "functional": " / ".join(x for x in (method, basis) if x) or "an unstated level of theory",
        "software": args.software or " and ".join(
            x for x, used in (("ORCA", (args.input_uv or "").lower().endswith((".out", ".log"))
                                         or (args.input_ir or "").lower().endswith((".out", ".log"))),
                              ("VASP", "doscar" in (args.input_dos or "").lower())) if used) or "an unstated program"
    }

    report = assess_spectroscopy_quality(
        metadata=meta,
        uv_vis_res=uv_res,
        vib_res=vib_res,
        dos_res=dos_res
    )

    print("  -> Generating publication figures...")
    generate_speccert_figures(report, output_dir)

    print("  -> Generating manuscript text, LaTeX summary table, and BibTeX citations...")
    assets = generate_speccert_manuscript_assets(report, output_dir)

    with open(assets["methods_text"], "r", encoding="utf-8") as f:
        methods_txt = f.read()
    with open(assets["citation_bib"], "r", encoding="utf-8") as f:
        bib_txt = f.read()

    html_p = os.path.join(output_dir, "report.html")
    print(f"  -> Writing HTML quality report to {html_p}...")
    generate_speccert_html_report(report, html_p, methods_text=methods_txt, citation_bib=bib_txt)

    print("\n" + "="*70)
    print(f" [RESULT] Overall status: {report.overall_status}")
    print(f" [SCORE]  {report.validation_score}")
    print("="*70)
    if report.uv_vis:
        print(f" * UV-Vis Absorption: lambda_max = {report.uv_vis.lambda_max_nm:.1f} nm (f_max = {report.uv_vis.max_oscillator_strength:.4f})")
    if report.dos_analysis and report.dos_analysis.d_band_center_filled_ev is not None:
        print(f" * d-Band Center    : eps_d = {report.dos_analysis.d_band_center_filled_ev:.3f} eV rel to E_F")
    print("="*70)
    print(f"\nReport ready at: {os.path.abspath(html_p)}\n")


def print_citation():
    print()
    print("If you use SpecCert in your publications, please cite:")
    print()
    print("APA Style:")
    print(APA)
    print()
    print("BibTeX:")
    print(BIBTEX)


def main():
    parser = argparse.ArgumentParser(
        prog="speccert",
        description="SpecCert: Spectroscopy Simulation, TD-DFT UV-Vis, IR Scaling & d-Band Center Certification."
    )
    parser.add_argument("-v", "--version", action="version", version=f"speccert {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Assess command
    assess_parser = subparsers.add_parser("assess", help="Assess UV-Vis, IR vibrational spectra, or DOS / d-band")
    assess_parser.add_argument("--input-uv", default=None, help="Path to TD-DFT output or UV-Vis CSV table")
    assess_parser.add_argument("--input-dos", default=None, help="Path to VASP DOSCAR or DOS CSV table")
    assess_parser.add_argument("--input-ir", default=None, help="ORCA frequency output (.out) or CSV with frequency and intensity columns")
    assess_parser.add_argument("--frequencies", default=None, help="Comma-separated harmonic frequencies in cm^-1 (no intensities: no IR spectrum)")
    assess_parser.add_argument("--basis", default=None, help="Basis set for the CCCBDB scaling factor (read from ORCA outputs if not given)")
    assess_parser.add_argument("--scaling-factor", type=float, default=None, help="Frequency scaling factor overriding the CCCBDB table")
    assess_parser.add_argument("--uv-fwhm", type=float, default=0.30, help="Gaussian FWHM (eV) of the UV-Vis broadening (default 0.30)")
    assess_parser.add_argument("--ions", default=None, help="Comma-separated 1-based ion numbers whose d-DOS is used (default: all ions)")
    assess_parser.add_argument("-o", "--output", default="speccert_output", help="Directory for output report (default: speccert_output)")
    assess_parser.add_argument("--system", default=None, help="Molecule / Surface name")
    assess_parser.add_argument("--functional", default=None, help="DFT functional / level of theory")
    assess_parser.add_argument("--software", default=None, help="Software code (e.g. 'ORCA', 'Gaussian', 'VASP')")

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run benchmark demonstration (Porphyrin UV-Vis + IR + Pt(111) d-band)")
    demo_parser.add_argument("-o", "--output", default="speccert_demo_output", help="Output directory (default: speccert_demo_output)")

    # Cite command
    subparsers.add_parser("cite", help="Display BibTeX and APA citation details")

    if len(sys.argv) == 1:
        print_banner()
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.command == "assess":
        print_banner()
        run_assess(args)
    elif args.command == "demo":
        print_banner()
        run_demo(args.output)
    elif args.command == "cite":
        print_banner()
        print_citation()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

