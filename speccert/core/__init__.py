"""
Core spectral convolution, anharmonic scaling, and electronic structure engines for SpecCert.
"""

from speccert.core.uv_vis import calculate_uv_vis_spectrum, UVVisResult
from speccert.core.vibrational import calculate_scaled_vibrational_spectrum, VibrationalSpectrumResult
from speccert.core.dos_dband import calculate_dos_and_dband_center, DOSAnalysisResult
from speccert.core.scoring import assess_spectroscopy_quality, SpectroscopyReport

__all__ = [
    "calculate_uv_vis_spectrum",
    "UVVisResult",
    "calculate_scaled_vibrational_spectrum",
    "VibrationalSpectrumResult",
    "calculate_dos_and_dband_center",
    "DOSAnalysisResult",
    "assess_spectroscopy_quality",
    "SpectroscopyReport"
]
