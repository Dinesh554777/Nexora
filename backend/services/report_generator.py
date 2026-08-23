"""Report Generation Service.

Builds a structured, frontend-ready patient report dict from the individual
pipeline stage results (patient info, OA assessment, segmentation metrics,
implant match).

Every generated report carries a mandatory disclaimer and a demo flag so
the UI can surface them prominently.

This module does NOT touch the database, does NOT call ML models, and has
no FastAPI dependency — it is a pure data-assembly service that can be unit
tested without any server infrastructure.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from services.oa_classifier import OAClassificationResult


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DISCLAIMER_TEXT = (
    "DEMO DATA — NOT FOR CLINICAL USE. "
    "This system is a research/demo decision-support prototype and does "
    "not provide a medical diagnosis."
)

REPORT_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Input data-classes (plain dicts accepted too; typed for clarity)
# ---------------------------------------------------------------------------

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Core report builder
# ---------------------------------------------------------------------------

def build_patient_report(
    *,
    # Patient info
    patient_id: str,
    patient_name: str,
    age: int | str,
    sex: str,
    affected_knee: str,
    scan_type: str = "Knee MRI",
    scan_date: str | None = None,
    # OA assessment result from oa_classifier_service
    oa_result: OAClassificationResult,
    # Segmentation metrics (from postprocessor or demo data)
    segmentation_metrics: dict[str, Any] | None = None,
    segmentation_source: str = "pipeline",
    # Measurements (mm)
    measurements: dict[str, float] | None = None,
    # Findings list
    findings: list[str] | None = None,
    # Implant match result (from /implant-match or demo data)
    implant_match: dict[str, Any] | None = None,
    # Whether this is a demo report
    is_demo: bool = True,
) -> dict[str, Any]:
    """Assemble and return a complete patient report dictionary.

    Parameters
    ----------
    patient_id      : Unique patient identifier (e.g. "DEMO-OA-001").
    patient_name    : Display name (use "Demo Patient OA" for demo cases).
    age             : Patient age in years.
    sex             : "Male" | "Female" | "Other".
    affected_knee   : "Left" | "Right" | "Bilateral".
    scan_type       : Modality label, default "Knee MRI".
    scan_date       : ISO date string, defaults to today.
    oa_result       : OAClassificationResult from oa_classifier_service.
    segmentation_metrics : Dict from postprocessor (mask_area_pixels, etc.).
    segmentation_source  : "pipeline" | "DEMO".
    measurements    : Dict of named measurements in mm.
    findings        : List of imaging observation strings.
    implant_match   : Dict with "recommendation" and "alternatives" keys.
    is_demo         : Must be True for all synthetic cases.

    Returns
    -------
    dict  Fully structured report ready to be serialised as JSON.
    """
    report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"
    generated_at = datetime.now(timezone.utc).isoformat()
    scan_date_str = scan_date or datetime.now(timezone.utc).date().isoformat()

    # ---- OA assessment section ----
    assessment_section: dict[str, Any] = {
        "case_id": oa_result.case_id,
        "classification": oa_result.classification,
        "oa_status": (
            "OA_SUSPECTED" if oa_result.classification == "OA"
            else "NO_OA_FEATURES_DETECTED" if oa_result.classification == "NON_OA"
            else "UNKNOWN"
        ),
        "confidence": oa_result.confidence,
        "severity": oa_result.severity,
        "source": oa_result.source,
        "model_version": oa_result.model_version,
        "is_demo": oa_result.is_demo,
        "clinical_warning": oa_result.clinical_warning,
    }

    # ---- Segmentation section ----
    seg = segmentation_metrics or {}
    segmentation_section: dict[str, Any] = {
        "mask_area_pixels": seg.get("mask_area_pixels"),
        "mask_fraction": seg.get("mask_fraction"),
        "probability_mean": seg.get("probability_mean"),
        "threshold": seg.get("threshold", 0.5),
        "model_name": seg.get("model_name", "unet2d"),
        "source": segmentation_source,
    }

    # ---- Measurements section ----
    meas = measurements or {}
    measurements_section: dict[str, Any] = {
        "medial_meniscus_thickness_mm": meas.get("medial_meniscus_thickness_mm"),
        "lateral_meniscus_thickness_mm": meas.get("lateral_meniscus_thickness_mm"),
        "medial_joint_space_mm": meas.get("medial_joint_space_mm"),
        "lateral_joint_space_mm": meas.get("lateral_joint_space_mm"),
        "femur_width_mm": meas.get("femur_width_mm"),
        "femur_ap_mm": meas.get("femur_ap_mm"),
        "tibia_width_mm": meas.get("tibia_width_mm"),
        "tibia_ap_mm": meas.get("tibia_ap_mm"),
    }
    # Remove None entries to keep the payload clean
    measurements_section = {k: v for k, v in measurements_section.items() if v is not None}

    # ---- Implant assessment section ----
    oa_requires_implant = oa_result.classification == "OA"
    if oa_requires_implant and implant_match:
        implant_section: dict[str, Any] = {
            "required": True,
            "status": "Candidate for further implant assessment",
            "recommendation": implant_match.get("recommendation"),
            "alternatives": implant_match.get("alternatives", []),
            "note": (
                "Implant matching based on extracted measurements. "
                "Verify with a qualified orthopaedic surgeon."
                + (" DEMO DATA — NOT FOR CLINICAL USE." if is_demo else "")
            ),
        }
    elif oa_requires_implant:
        implant_section = {
            "required": True,
            "status": "Implant assessment pending — measurements required",
            "recommendation": None,
            "alternatives": [],
            "note": "Provide femur/tibia measurements to generate implant recommendations.",
        }
    else:
        implant_section = {
            "required": False,
            "status": "No implant recommendation required",
            "recommendation": None,
            "alternatives": [],
            "note": (
                "Non-OA case. Implant matching is not applicable."
                + (" DEMO DATA — NOT FOR CLINICAL USE." if is_demo else "")
            ),
        }

    # ---- Full report ----
    report: dict[str, Any] = {
        "report_id": report_id,
        "report_version": REPORT_VERSION,
        "generated_at": generated_at,
        "demo": is_demo,
        "clinical_use": False,
        "report_status": "DEMO_ONLY" if is_demo else "ACTIVE",
        "disclaimer": DISCLAIMER_TEXT if is_demo else (
            "AI-generated result for clinical decision support only. "
            "Must be reviewed by a qualified healthcare professional."
        ),
        # --- Patient information ---
        "patient": {
            "patient_id": patient_id,
            "name": patient_name,
            "age": int(age) if str(age).isdigit() else age,
            "sex": sex,
            "affected_knee": affected_knee,
        },
        # --- Scan metadata ---
        "scan": {
            "scan_type": scan_type,
            "scan_date": scan_date_str,
        },
        # --- AI OA assessment ---
        "assessment": assessment_section,
        # --- Segmentation output ---
        "segmentation": segmentation_section,
        # --- Quantitative measurements ---
        "measurements": measurements_section,
        # --- Imaging findings ---
        "findings": findings or [],
        # --- Implant planning ---
        "implant_assessment": implant_section,
        # --- Pipeline provenance ---
        "pipeline_stages": [
            "image_validation",
            "oa_classification",
            "segmentation",
            "measurements",
            "report_generation",
            *(["implant_matching"] if oa_requires_implant and implant_match else []),
        ],
    }

    return report


def build_demo_report_from_file(case_data: dict[str, Any]) -> dict[str, Any]:
    """Build a report from a pre-loaded demo JSON file (demo_oa_patient.json, etc.).

    This is a convenience wrapper used by the /demo-cases endpoints to convert
    the raw JSON file content into the canonical report format without running
    any ML pipeline.

    Parameters
    ----------
    case_data : Parsed content of demo_oa_patient.json or demo_non_oa_patient.json.

    Returns
    -------
    dict  Canonical report dict.
    """
    from services.oa_classifier import OAClassificationResult
    import uuid

    patient = case_data.get("patient", {})
    scan = case_data.get("scan", {})
    assessment = case_data.get("assessment", {})
    measurements = case_data.get("measurements", {})
    findings = case_data.get("findings", [])
    segmentation = case_data.get("segmentation", {})
    implant_raw = case_data.get("implant_assessment", {})

    # Reconstruct OAClassificationResult from stored demo data
    oa_result = OAClassificationResult(
        case_id=str(uuid.uuid4()),
        classification=assessment.get("classification", "UNKNOWN"),
        confidence=float(assessment.get("confidence", 0.0)),
        severity=assessment.get("severity", "Unknown"),
        source="DEMO",
        model_version=assessment.get("model_version", "demo-stub-v1.0"),
        is_demo=True,
        clinical_warning=OAClassificationResult.CLINICAL_WARNING_DEMO,
        metadata={"source_file": case_data.get("case_type", "unknown")},
    )

    # Re-shape implant data
    implant_match: dict[str, Any] | None = None
    recommended = implant_raw.get("recommended_implant")
    if recommended:
        implant_match = {
            "recommendation": {
                "implantId": recommended.get("implant_id"),
                "implantName": recommended.get("implant_name"),
                "size": recommended.get("size"),
                "matchScore": recommended.get("match_score"),
                "confidence": recommended.get("confidence"),
                "measurementDifference": recommended.get("measurement_difference"),
                "rank": 1,
            },
            "alternatives": [
                {
                    "implantId": a.get("implant_id"),
                    "implantName": a.get("implant_name"),
                    "size": a.get("size"),
                    "matchScore": a.get("match_score"),
                    "confidence": a.get("confidence"),
                    "measurementDifference": a.get("measurement_difference"),
                    "rank": i + 2,
                }
                for i, a in enumerate(implant_raw.get("alternatives", []))
            ],
        }

    return build_patient_report(
        patient_id=patient.get("patient_id", "DEMO-UNKNOWN"),
        patient_name=patient.get("name", "Demo Patient"),
        age=patient.get("age", 0),
        sex=patient.get("sex", "Unknown"),
        affected_knee=patient.get("affected_knee", "Unknown"),
        scan_type=scan.get("scan_type", "Knee MRI"),
        scan_date=scan.get("scan_date"),
        oa_result=oa_result,
        segmentation_metrics=segmentation,
        segmentation_source="DEMO",
        measurements=measurements,
        findings=findings,
        implant_match=implant_match,
        is_demo=True,
    )
