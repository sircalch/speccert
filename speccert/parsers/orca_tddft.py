"""
Parsers for ORCA TD-DFT / CIS and IR/Raman frequency outputs.
"""

from typing import Dict, Any, List, Optional
import os
import re

EV_PER_CM1 = 1.0 / 8065.543937
NM_EV = 1239.841984

_ABS_HEADER = "ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS"


def _dominant_excitations(content: str) -> Dict[int, str]:
    """Largest-weight orbital excitation of each state from the last 'STATE n:' listing."""
    out: Dict[int, str] = {}
    blocks = re.split(r"\n(?=STATE\s+\d+:\s+E=)", content)
    for blk in blocks:
        m = re.match(r"STATE\s+(\d+):\s+E=", blk)
        if not m:
            continue
        best = None
        for occ, vir, w in re.findall(r"^\s*(\d+[ab]?)\s*->\s*(\d+[ab]?)\s*:\s*([\d.]+)", blk, re.M):
            if best is None or float(w) > best[2]:
                best = (occ, vir, float(w))
        if best is not None:
            out[int(m.group(1))] = f"{best[0]} -> {best[1]} ({best[2]:.2f})"
    return out


def parse_orca_tddft_output(filepath: str) -> Dict[str, Any]:
    """
    Parses an ORCA TD-DFT / CIS output for excitation energies and oscillator strengths.

    The oscillator strengths are read from the last
    'ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS' table, which ORCA 6 writes as
    "0-1A -> 1-1A  E(eV)  E(cm-1)  lambda(nm)  fosc ..." and ORCA 5 as "n  E(cm-1)  lambda(nm)  fosc ...".
    The dominant orbital excitation of each state is taken from the 'STATE n:' listing.
    Returns energies in eV, wavelengths in nm, oscillator strengths, a character label per state
    and n_states.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    energies_ev: List[float] = []
    osc_strengths: List[float] = []
    wavelengths_nm: List[float] = []
    states: List[int] = []

    if _ABS_HEADER in content:
        table = content.rsplit(_ABS_HEADER, 1)[1]
        lines = table.splitlines()
        started = False
        for ln in lines[1:]:
            s = ln.strip()
            if not s:
                if started:
                    break
                continue
            if set(s) <= {"-"}:
                if started:
                    break
                continue
            # ORCA 6: "0-1A  ->  2-1A    8.198821   66128.0   151.2   0.170287143 ..."
            m6 = re.match(r"\d+-\S+\s*->\s*(\d+)-\S+\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)", s)
            # ORCA 5: "   2   66128.0    151.2   0.170287143 ..."
            m5 = re.match(r"(\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)", s)
            if m6:
                started = True
                states.append(int(m6.group(1)))
                energies_ev.append(float(m6.group(2)))
                wavelengths_nm.append(float(m6.group(4)))
                osc_strengths.append(float(m6.group(5)))
            elif m5 and not re.match(r"\d+-", s):
                started = True
                states.append(int(m5.group(1)))
                energies_ev.append(float(m5.group(2)) * EV_PER_CM1)
                wavelengths_nm.append(float(m5.group(3)))
                osc_strengths.append(float(m5.group(4)))
            elif started:
                break

    if not energies_ev:
        # Legacy one-line format: "STATE  1:  E=  0.123 au  3.359 eV  369.1 nm  f=  0.0854"
        pattern = r"STATE\s+(\d+):\s+E=\s+([-\d\.]+)\s+au\s+([-\d\.]+)\s+eV\s+([-\d\.]+)\s+nm\s+f=\s+([-\d\.]+)"
        for m in re.findall(pattern, content):
            states.append(int(m[0]))
            energies_ev.append(float(m[2]))
            wavelengths_nm.append(float(m[3]))
            osc_strengths.append(float(m[4]))

    dom = _dominant_excitations(content)
    transitions = [f"State {st}: {dom[st]}" if st in dom else f"State {st}" for st in states]

    return {
        "energies_ev": energies_ev,
        "wavelengths_nm": wavelengths_nm,
        "oscillator_strengths": osc_strengths,
        "transitions_character": transitions,
        "n_states": len(energies_ev),
    }
