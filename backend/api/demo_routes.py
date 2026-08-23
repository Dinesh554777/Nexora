"""Demo and OA Assessment endpoints.

New endpoints added here — existing routes.py is unchanged.

Endpoints
---------
POST /api/v1/oa-assessment
    Accept a valid knee image and return an OA assessment.
    Uses oa_classifier_service (StubOAClassifier while no real model exists).
    Accepts an optional ``demo_case_id`` form field so jury demos work.

GET  /api/v1/demo-cases
    List the two pre-configured synthetic demo cases (OA + Non-OA).

GET  /api/v1/demo-cases/{case_id}
    Return the full demo report for a specific case (DEMO-OA-001 or DEMO-NONOA-001).

All endpoints surface the demo/clinical-use flags and disclaimers in every response.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from services.oa_classifier import oa_classifier_service
from services.report_generator import build_demo_report_from_file
from services.validator import validate_image_upload

logger = logging.getLogger(__name__)

demo_router = APIRouter(tags=["demo"])

# ---------------------------------------------------------------------------
# Locate demo data files relative to this file
# ---------------------------------------------------------------------------

_DEMO_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # backend/
    "demo_data",
)

_DEMO_CASE_FILES: dict[str, str] = {
    "DEMO-OA-001": os.path.join(_DEMO_DATA_DIR, "demo_oa_patient.json"),
    "DEMO-NONOA-001": os.path.join(_DEMO_DATA_DIR, "demo_non_oa_patient.json"),
}

# Lightweight card info returned by GET /api/v1/demo-cases
_DEMO_CASE_CARDS: list[dict[str, Any]] = [
    {
        "case_id": "DEMO-OA-001",
        "case_type": "OA",
        "label": "OA Demo Patient",
        "patient_id": "DEMO-OA-001",
        "age": 58,
        "sex": "Female",
        "affected_knee": "Right",
        "classification": "OA",
        "severity": "Moderate",
        "confidence": 0.92,
        "scan_type": "Knee MRI",
        "scan_date": "2026-08-23",
        "report_status": "DEMO_ONLY",
        "demo": True,
        "clinical_use": False,
        "disclaimer": "DEMO DATA — NOT FOR CLINICAL USE.",
    },
    {
        "case_id": "DEMO-NONOA-001",
        "case_type": "NON_OA",
        "label": "Non-OA Demo Patient",
        "patient_id": "DEMO-NONOA-001",
        "age": 32,
        "sex": "Male",
        "affected_knee": "Right",
        "classification": "NON_OA",
        "severity": "None",
        "confidence": 0.95,
        "scan_type": "Knee MRI",
        "scan_date": "2026-08-23",
        "report_status": "DEMO_ONLY",
        "demo": True,
        "clinical_use": False,
        "disclaimer": "DEMO DATA — NOT FOR CLINICAL USE.",
    },
]


def _load_demo_case(case_id: str) -> dict[str, Any]:
    """Load and parse a demo JSON file; raise 404 if unknown or unreadable."""
    file_path = _DEMO_CASE_FILES.get(case_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo case '{case_id}' not found. Valid IDs: {list(_DEMO_CASE_FILES)}",
        )
    if not os.path.exists(file_path):
        logger.error("Demo data file missing: %s", file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo data file is missing from the server. Contact the demo administrator.",
        )
    try:
        with open(file_path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        logger.exception("Corrupt demo data file: %s", file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo data file is corrupt.",
        ) from exc


# ---------------------------------------------------------------------------
# POST /api/v1/oa-assessment
# ---------------------------------------------------------------------------

@demo_router.post(
    "/api/v1/oa-assessment",
    status_code=status.HTTP_200_OK,
    summary="OA Assessment — classify a knee image for osteoarthritis",
    description=(
        "Accept a valid knee medical image and return an OA/Non-OA assessment.\n\n"
        "**Architecture note:** The current implementation uses a `StubOAClassifier` "
        "because no trained OA classification model has been integrated yet. "
        "Results with `source='DEMO'` are pre-configured synthetic values — "
        "they are NOT derived from image content analysis.\n\n"
        "When a real model is available, replace `oa_classifier_service` with "
        "`RealOAClassifier` in `services/oa_classifier.py`.\n\n"
        "Pass `demo_case_id=DEMO-OA-001` or `demo_case_id=DEMO-NONOA-001` in the "
        "form body to retrieve the pre-configured jury-demo result for that case."
    ),
    responses={
        200: {"description": "OA assessment returned (may be DEMO source)."},
        400: {"description": "Invalid image upload."},
        413: {"description": "Image exceeds size limit."},
        422: {"description": "Missing 'file' field."},
    },
)
async def oa_assessment(
    file: Annotated[UploadFile, File(description="Knee medical image (JPEG/PNG/WebP/BMP/TIFF).")],
    demo_case_id: Annotated[
        str | None,
        Form(description="Optional: 'DEMO-OA-001' or 'DEMO-NONOA-001' for jury demo."),
    ] = None,
) -> dict[str, Any]:
    """Classify the uploaded knee image for OA.

    Pipeline
    --------
    1. Validate image (type, size, integrity, dimensions).
    2. Pass bytes + optional demo_case_id to oa_classifier_service.
    3. Return structured assessment with mandatory clinical warning.
    """
    # Step 1 — validate upload (reuses existing validator; raises HTTPException on failure)
    try:
        contents, (orig_w, orig_h) = await validate_image_upload(file)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected validation error in oa-assessment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image validation failed unexpectedly.",
        ) from exc

    # Step 2 — OA classification
    try:
        result = oa_classifier_service.classify(
            contents,
            demo_case_id=demo_case_id,
        )
    except Exception as exc:
        logger.exception("OA classification failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OA classification failed unexpectedly.",
        ) from exc

    # Step 3 — structured response
    return {
        "case_id": result.case_id,
        "assessment": {
            "classification": result.classification,
            "oa_status": (
                "OA_SUSPECTED" if result.classification == "OA"
                else "NO_OA_FEATURES_DETECTED" if result.classification == "NON_OA"
                else "UNKNOWN"
            ),
            "confidence": result.confidence,
            "severity": result.severity,
        },
        "source": result.source,
        "model_version": result.model_version,
        "is_demo": result.is_demo,
        "status": "demo" if result.is_demo else "model",
        "clinical_warning": result.clinical_warning,
        "image_info": {
            "filename": file.filename,
            "width": orig_w,
            "height": orig_h,
        },
        "metadata": result.metadata,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/demo-cases
# ---------------------------------------------------------------------------

@demo_router.get(
    "/api/v1/demo-cases",
    status_code=status.HTTP_200_OK,
    summary="List available synthetic demo patient cases",
    description=(
        "Returns the two pre-configured synthetic demo cases available for "
        "jury demonstration: one OA case and one Non-OA case.\n\n"
        "**All cases are DEMO DATA — NOT FOR CLINICAL USE.**"
    ),
)
async def list_demo_cases() -> dict[str, Any]:
    """Return summary cards for all available demo cases."""
    return {
        "demo": True,
        "clinical_use": False,
        "disclaimer": "DEMO DATA — NOT FOR CLINICAL USE.",
        "total": len(_DEMO_CASE_CARDS),
        "cases": _DEMO_CASE_CARDS,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/demo-cases/{case_id}
# ---------------------------------------------------------------------------

@demo_router.get(
    "/api/v1/demo-cases/{case_id}",
    status_code=status.HTTP_200_OK,
    summary="Get full demo report for a specific synthetic patient case",
    description=(
        "Returns the complete synthetic patient report for the given demo case ID.\n\n"
        "Valid IDs: `DEMO-OA-001`, `DEMO-NONOA-001`\n\n"
        "**DEMO DATA — NOT FOR CLINICAL USE.**"
    ),
    responses={
        200: {"description": "Full demo report returned."},
        404: {"description": "Unknown demo case ID."},
    },
)
async def get_demo_case(case_id: str) -> dict[str, Any]:
    """Return the full report for a single demo case.

    Loads the corresponding JSON file and assembles a canonical report
    via ``build_demo_report_from_file``.
    """
    case_data = _load_demo_case(case_id)
    report = build_demo_report_from_file(case_data)
    return report
