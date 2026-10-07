"""
Citation strings for SpecCert (concept DOI: resolves to the latest version on Zenodo).
"""

from speccert import __version__

CONCEPT_DOI = "10.5281/zenodo.22217588"
TITLE = "SpecCert: checked UV-Vis and IR spectra from ORCA outputs and d-band moments from VASP DOSCAR files"

BIBTEX = (
    "@software{monreal2026speccert,\n"
    "  author = {Monreal-Hern{\\'a}ndez, Andr{\\'e}s},\n"
    f"  title = {{{{{TITLE}}}}},\n"
    "  year = {2026},\n"
    f"  version = {{{__version__}}},\n"
    "  publisher = {Zenodo},\n"
    f"  doi = {{{CONCEPT_DOI}}},\n"
    "  url = {https://github.com/sircalch/speccert}\n"
    "}\n"
)

APA = f"Monreal-Hernández, A. (2026). {TITLE} (v{__version__}). Zenodo. https://doi.org/{CONCEPT_DOI}"
