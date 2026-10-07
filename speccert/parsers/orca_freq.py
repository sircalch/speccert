"""
Parser for ORCA (5/6) frequency outputs: harmonic frequencies, IR intensities and the level of theory.
"""

from typing import Dict, Any, List, Optional
import os
import re

_BASIS = re.compile(r"^(def2-[a-z0-9+]+|ma-def2-[a-z0-9+]+|(aug-|jun-|may-)?cc-p[cw]?v[dtq56]z|"
                    r"6-31[1]?\+{0,2}g[*(),dfp]*|3-21g\*?|sto-3g|pc(seg)?-[0-4])$", re.I)
_NOT_METHOD = {"rks", "uks", "rhf", "uhf", "rohf", "tightscf", "verytightscf", "normalscf", "loosescf",
               "opt", "tightopt", "verytightopt", "looseopt", "freq", "numfreq", "anfreq", "d3bj", "d3", "d4",
               "d3zero", "rijcosx", "ri", "def2/j", "nopop", "miniprint", "largeprint", "printbasis", "cpcm",
               "smd", "sp", "engrad", "defgrid1", "defgrid2", "defgrid3", "grid4", "grid5", "grid6"}


def _level_of_theory(content: str):
    kws = []
    for m in re.finditer(r"^\|\s*\d+>\s*!(.*)$", content, re.M):
        kws += m.group(1).split()
    basis = next((k for k in kws if _BASIS.match(k)), None)
    method = next((k for k in kws if k.lower() not in _NOT_METHOD and not _BASIS.match(k)
                   and not k.lower().startswith(("def2/", "aux", "cpcm(", "smd("))), None)
    if method and any(k.lower() in ("d3bj", "d3", "d4", "d3zero") for k in kws):
        method_disp = method + "-" + next(k for k in kws if k.lower() in ("d3bj", "d3", "d4", "d3zero")).upper()
    else:
        method_disp = method
    return method_disp, basis


def parse_orca_freq_output(filepath: str) -> Dict[str, Any]:
    """
    Parses an ORCA frequency output.

    Returns
    -------
    data : dict
        frequencies_cm1 (vibrations only: the leading translation/rotation modes printed as 0.00 are dropped;
        imaginary modes are negative), ir_intensities_km_mol (aligned with frequencies_cm1; 0 for modes absent
        from the IR table), scaling_factor_in_output (the factor ORCA reports as already applied), method,
        basis (from the input echo, None if not recognised).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
        content = fh.read()

    blocks = re.split(r"VIBRATIONAL FREQUENCIES\s*\n-+\s*\n", content)
    if len(blocks) < 2:
        raise ValueError("No 'VIBRATIONAL FREQUENCIES' block found in the ORCA output.")
    body = re.split(r"NORMAL MODES|IR SPECTRUM", blocks[-1])[0]
    m = re.search(r"Scaling factor for frequencies\s*=\s*([\d.]+)", body)
    scaling = float(m.group(1)) if m else 1.0
    modes = [(int(i), float(f)) for i, f in re.findall(r"^\s*(\d+):\s+(-?\d+\.\d+)\s+cm\*\*-1", body, re.M)]
    # translations and rotations are printed first as exactly 0.00
    first = next((k for k, (_, f) in enumerate(modes) if f != 0.0), len(modes))
    vib = modes[first:]

    intens = {}
    ir = content.split("IR SPECTRUM")
    if len(ir) > 1:
        for i, _f, _eps, inten in re.findall(r"^\s*(\d+):\s+(-?\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s", ir[-1], re.M):
            intens[int(i)] = float(inten)

    method, basis = _level_of_theory(content)
    return {
        "frequencies_cm1": [f for _, f in vib],
        "ir_intensities_km_mol": [intens.get(i, 0.0) for i, _ in vib] if intens else None,
        "mode_indices": [i for i, _ in vib],
        "scaling_factor_in_output": scaling,
        "method": method,
        "basis": basis,
        "n_modes": len(vib),
    }
