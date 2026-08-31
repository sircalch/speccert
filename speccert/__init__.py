"""
SpecCert: Automated Quality-Control, Spectroscopy Simulation (UV-Vis TD-DFT, IR/Raman Anharmonic Scaling),
and Electronic Structure Certification (DOS & d-Band Center).
"""

__version__ = "1.0.0"
__author__ = "Andre Monreal-Hernández"
__license__ = "MIT"

from speccert.core.uv_vis import calculate_uv_vis_spectrum, UVVisResult
from speccert.core.vibrational import calculate_scaled_vibrational_spectrum, VibrationalSpectrumResult
from speccert.core.dos_dband import calculate_dos_and_dband_center, DOSAnalysisResult
from speccert.core.scoring import assess_spectroscopy_quality, SpectroscopyReport

__all__ = [
    "__version__",
    "calculate_uv_vis_spectrum",
    "UVVisResult",
    "calculate_scaled_vibrational_spectrum",
    "VibrationalSpectrumResult",
    "calculate_dos_and_dband_center",
    "DOSAnalysisResult",
    "assess_spectroscopy_quality",
    "SpectroscopyReport"
]
