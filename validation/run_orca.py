"""
Runs the ORCA jobs of validation/spec_runs/<molecule>/: opt_freq.inp first, then tddft.inp (which reads the
optimised geometry). Molecules run in parallel, jobs within a molecule in sequence.

    python validation/run_orca.py [n_parallel]

Jobs whose output already ends in "ORCA TERMINATED NORMALLY" are skipped. Set ORCA to the orca executable if
it is not at C:\\ORCA_6.1.1\\orca.exe. On this machine more than three parallel jobs occasionally failed with
"CANNOT OPEN FILE" (file locks); a failed job is retried once.
"""
import ctypes
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ORCA = os.environ.get("ORCA", r"C:\ORCA_6.1.1\orca.exe")


def done(out):
    if not os.path.exists(out):
        return False
    with open(out, encoding="utf-8", errors="ignore") as fh:
        return "ORCA TERMINATED NORMALLY" in fh.read()[-3000:]


def run_job(d, name):
    out = os.path.join(d, name + ".out")
    for attempt in (1, 2):
        if done(out):
            return f"{name} ok"
        with open(out, "w") as fh:
            subprocess.run([ORCA, name + ".inp"], cwd=d, stdout=fh, stderr=subprocess.STDOUT)
    return f"{name} {'ok' if done(out) else 'FAILED'}"


def run_molecule(d):
    t = time.time()
    msgs = [run_job(d, "opt_freq")]
    if "ok" in msgs[0]:
        msgs.append(run_job(d, "tddft"))
    return f"{os.path.basename(d)}: {', '.join(msgs)} ({time.time() - t:.0f} s)"


def main():
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # keep the machine awake
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    root = os.path.join(HERE, "spec_runs")
    dirs = sorted(os.path.join(root, x) for x in os.listdir(root) if os.path.isdir(os.path.join(root, x)))
    with ThreadPoolExecutor(n) as ex:
        for msg in ex.map(run_molecule, dirs):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
