"""
Multi-technique spectroscopy certification scoring and report aggregation for SpecCert.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import numpy as np

from speccert.core.uv_vis import UVVisResult
from speccert.core.vibrational import VibrationalSpectrumResult
from speccert.core.dos_dband import DOSAnalysisResult


@dataclass
class SpectroscopyReport:
    overall_status: str  # 'PASS', 'WARNING', 'FAIL'
    validation_score: str
    metadata: Dict[str, Any]
    uv_vis: Optional[UVVisResult]
    vibrational: Optional[VibrationalSpectrumResult]
    dos_analysis: Optional[DOSAnalysisResult]
    recommendations: List[str]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def assess_spectroscopy_quality(
    metadata: Dict[str, Any],
    uv_vis_res: Optional[UVVisResult] = None,
    vib_res: Optional[VibrationalSpectrumResult] = None,
    dos_res: Optional[DOSAnalysisResult] = None
) -> SpectroscopyReport:
    """
    Consolidates simulated optical UV-Vis spectra, scaled IR/Raman vibrational profiles,
    and electronic density of states / d-band metrics.

    Parameters
    ----------
    metadata : dict
    uv_vis_res : UVVisResult, optional
    vib_res : VibrationalSpectrumResult, optional
    dos_res : DOSAnalysisResult, optional

    Returns
    -------
    report : SpectroscopyReport
    """
    statuses = []
    recommendations = []

    if uv_vis_res is not None:
        statuses.append(uv_vis_res.status)
        if uv_vis_res.status != "PASS":
            recommendations.append(uv_vis_res.diagnostic_message)

    if vib_res is not None:
        statuses.append(vib_res.status)
        if vib_res.status != "PASS":
            recommendations.append(vib_res.diagnostic_message)

    if dos_res is not None:
        statuses.append(dos_res.status)
        if dos_res.status != "PASS":
            recommendations.append(dos_res.diagnostic_message)

    if not statuses:
        overall_status = "PASS"
        validation_score = "SPECTROSCOPY & ELECTRONIC STRUCTURE = UNVERIFIED"
    elif "FAIL" in statuses:
        overall_status = "FAIL"
        validation_score = "SPECTROSCOPY & ELECTRONIC STRUCTURE = FAILED / METHODOLOGICAL INCONSISTENCIES"
    elif "WARNING" in statuses:
        overall_status = "WARNING"
        validation_score = "SPECTROSCOPY & ELECTRONIC STRUCTURE = ACCEPTABLE WITH WARNINGS"
    else:
        overall_status = "PASS"
        validation_score = "SPECTROSCOPY & ELECTRONIC STRUCTURE = FULLY CERTIFIED (PUBLICATION GRADE)"

    return SpectroscopyReport(
        overall_status=overall_status,
        validation_score=validation_score,
        metadata=metadata,
        uv_vis=uv_vis_res,
        vibrational=vib_res,
        dos_analysis=dos_res,
        recommendations=recommendations,
        provenance={
            "tool": "SpecCert",
            "version": "1.0.0",
            "citation": "Monreal-Hernández, A. (2026). SpecCert: Automated Quality-Control, Spectroscopy Simulation (UV-Vis TD-DFT, IR/Raman Anharmonic Scaling), and Electronic Structure Certification (DOS & d-Band Center)."
        }
    )
