# VASP calculations from NOMAD

Raw files (DOSCAR, vasprun.xml, INCAR, POSCAR; gzipped, otherwise unchanged) of nine VASP calculations
published in the NOMAD repository (https://nomad-lab.eu) under the Creative Commons Attribution 4.0 licence
(CC BY 4.0). They were downloaded with `validation/fetch_nomad_doscar.py` on 2026-10-06 and are used only to
test SpecCert's DOSCAR reader and d-band moments against pymatgen.

Each calculation can be found at https://nomad-lab.eu/prod/v1/gui/entry/id/<entry_id>.

| folder | entry_id | upload_id | mainfile | ISPIN | licence |
|---|---|---|---|---|---|
| Cu | -x5RyeRegfRzVaUorQ9Q3yFI_O2S | e-UOMrI-QDGModmBnxIaBA | monomers_input_expanded/PBE/Accurate/8/29_Cu/POTCAR_pv/single_point/vasprun.xml | 1 | CC BY 4.0 |
| Ag | 0HnBXYyqhdlHGqSybnjuHqThEk6j | 4AKh_pFmSbyUoWphewbpqQ | monomers_input_expanded/PBE/Accurate/2/47_Ag/POTCAR_pv/single_point/vasprun.xml | 1 | CC BY 4.0 |
| Ni | -7fhBMLRckBEi2NMb4njVEOp1O4n | 4AKh_pFmSbyUoWphewbpqQ | monomers_input_expanded/PBE/Accurate/2/28_Ni/POTCAR_pv/single_point/vasprun.xml | 1 | CC BY 4.0 |
| Pt | -lEhOpoaRy4YXmOWtjZD3ZjVAmP3 | 5A1BV5LBTbGfuvTFh6F0GQ | monomers_input/PBE/Accurate/2/78_Pt/POTCAR/single_point/vasprun.xml | 1 | CC BY 4.0 |
| Fe | -EIm3uUgIh58NK0wL_rIwQBfFvSc | 4AKh_pFmSbyUoWphewbpqQ | monomers_input_expanded/PBE/Accurate/8/26_Fe/POTCAR_sv/single_point/vasprun.xml | 1 | CC BY 4.0 |
| Co | 1ciLtCsgoAcnvehiLOmmj5SYSuPk | eJexi2o0RGmZ-HvagQ0DMg | monomers_input/PBE/Accurate/2/27_Co/POTCAR_sv/single_point/vasprun.xml | 1 | CC BY 4.0 |
| Fe39 | -0RN7SIfS7oobLZfrxpq1cuxz5g7 | mFTkxQ0LS1GVlEItKRsB0g | Fe/39/8/vasprun.xml | 2 | CC BY 4.0 |
| Ni47 | -0Lr18tvi0d9AaEobeiK3O63mjdM | JVkvSYsCQEmSx18lbb8Ehw | Ni/47/20/vasprun.xml | 2 | CC BY 4.0 |
| Co18 | -02_ILI1bWoJw1Y80KItPnGGvEq2 | 0-sXwvckQuG7xE9YXnkbDA | Co/18/8/vasprun.xml | 2 | CC BY 4.0 |

Attribution: the authors of the NOMAD uploads listed above. NOMAD: Scheidgen, M. et al., NOMAD: A distributed
web-based platform for managing materials science research data, J. Open Source Softw. 8, 5388 (2023),
https://doi.org/10.21105/joss.05388.
