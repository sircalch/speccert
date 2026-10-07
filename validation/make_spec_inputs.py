"""
Writes the ORCA 6.1 inputs of the SpecCert v2 benchmark (validation/spec_runs/<molecule>/).

    python validation/make_spec_inputs.py

For each molecule: opt_freq.inp (B3LYP-D3(BJ)/def2-SVP, TightSCF, TightOpt, analytic frequencies with IR
intensities) and tddft.inp (TD-DFT, 15 singlet roots, at the optimised geometry opt_freq.xyz, written by
the first job). Starting geometries: RDKit ETKDG + MMFF (random seed 7).
"""
import os

from rdkit import Chem
from rdkit.Chem import AllChem

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "spec_runs")

MOLECULES = {
    "formaldehyde": "C=O",
    "acetone": "CC(C)=O",
    "acrolein": "C=CC=O",
    "butadiene": "C=CC=C",
    "hexatriene": "C=CC=CC=C",
    "benzene": "c1ccccc1",
    "pyridine": "c1ccncc1",
    "naphthalene": "c1ccc2ccccc2c1",
}


def xyz_block(smiles):
    m = Chem.AddHs(Chem.MolFromSmiles(smiles))
    AllChem.EmbedMolecule(m, randomSeed=7)
    AllChem.MMFFOptimizeMolecule(m)
    conf = m.GetConformer()
    return "\n".join(f"{a.GetSymbol():2s} {p.x:12.6f} {p.y:12.6f} {p.z:12.6f}"
                     for a, p in zip(m.GetAtoms(), (conf.GetAtomPosition(i) for i in range(m.GetNumAtoms()))))


def main():
    for name, smi in MOLECULES.items():
        d = os.path.join(OUT, name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "opt_freq.inp"), "w") as fh:
            fh.write(f"# {name} ({smi})\n! B3LYP D3BJ def2-SVP TightSCF TightOpt Freq\n* xyz 0 1\n{xyz_block(smi)}\n*\n")
        with open(os.path.join(d, "tddft.inp"), "w") as fh:
            fh.write(f"# {name}: TD-DFT at the optimised geometry\n! B3LYP D3BJ def2-SVP TightSCF\n"
                     "%tddft\n  nroots 15\nend\n* xyzfile 0 1 opt_freq.xyz\n")
    print(len(MOLECULES), "molecules")


if __name__ == "__main__":
    main()
