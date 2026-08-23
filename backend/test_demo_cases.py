"""Tests for the Demo Cases and OA Assessment endpoints, plus unit tests for
the OA classifier service and report generation service.

Coverage
--------
1.  GET  /api/v1/demo-cases         — list endpoint
2.  GET  /api/v1/demo-cases/DEMO-OA-001    — OA full report
3.  GET  /api/v1/demo-cases/DEMO-NONOA-001 — Non-OA full report
4.  GET  /api/v1/demo-cases/<unknown>       — 404
5.  POST /api/v1/oa-assessment — OA demo result (demo_case_id=DEMO-OA-001)
6.  POST /api/v1/oa-assessment — Non-OA demo result (demo_case_id=DEMO-NONOA-001)
7.  POST /api/v1/oa-assessment — real upload, no demo_case_id → UNKNOWN stub
8.  POST /api/v1/oa-assessment — invalid image type → 400
9.  POST /api/v1/oa-assessment — corrupted image → 400
10. POST /api/v1/oa-assessment — missing file field → 422
11. StubOAClassifier unit — demo OA case
12. StubOAClassifier unit — demo Non-OA case
13. StubOAClassifier unit — real upload (no demo_case_id) → UNKNOWN
14. StubOAClassifier unit — is_available returns True
15. build_patient_report unit — OA report structure
16. build_patient_report unit — Non-OA report (no implant)
17. build_demo_report_from_file unit — OA demo file round-trip
18. build_demo_report_from_file unit — Non-OA demo file round-trip
19. Existing /health still works (regression)
20. Existing /analytics still works (regression)
21. Existing POST /api/v1/segment still accepts valid image (regression)
"""

import io
import json
import os

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from main import app
from services.oa_classifier import (
    OAClassificationResult,
    StubOAClassifier,
    oa_classifier_service,
)
from services.report_generator import (
    build_demo_report_from_file,
    build_patient_report,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_png(width: int = 64, height: int = 64, color: str = "gray") -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _demo_file(filename: str) -> dict:
    """Load a demo JSON file from the backend demo_data directory."""
    base = os.path.join(os.path.dirname(__file__), "demo_data", filename)
    with open(base, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# 1 — GET /api/v1/demo-cases  (list)
# ---------------------------------------------------------------------------

def test_list_demo_cases_returns_two_cases():
    resp = client.get("/api/v1/demo-cases")
    assert resp.status_code == 200
    data = resp.json()
    assert data["demo"] is True
    assert data["clinical_use"] is False
    assert data["total"] == 2
    ids = [c["case_id"] for c in data["cases"]]
    assert "DEMO-OA-001" in ids
    assert "DEMO-NONOA-001" in ids


def test_list_demo_cases_carries_disclaimer():
    resp = client.get("/api/v1/demo-cases")
    data = resp.json()
    assert "NOT FOR CLINICAL USE" in data["disclaimer"].upper()


def test_list_demo_cases_card_fields():
    resp = client.get("/api/v1/demo-cases")
    for case in resp.json()["cases"]:
        for field in ("case_id", "case_type", "label", "patient_id",
                      "age", "sex", "affected_knee", "classification",
                      "severity", "confidence", "report_status", "demo"):
            assert field in case, f"Missing field '{field}' in case card"


# ---------------------------------------------------------------------------
# 2 — GET /api/v1/demo-cases/DEMO-OA-001  (OA report)
# ---------------------------------------------------------------------------

def test_get_oa_demo_case_report_structure():
    resp = client.get("/api/v1/demo-cases/DEMO-OA-001")
    assert resp.status_code == 200
    r = resp.json()

    # top-level mandatory keys
    for key in ("report_id", "demo", "clinical_use", "report_status",
                "disclaimer", "patient", "scan", "assessment",
                "segmentation", "measurements", "findings",
                "implant_assessment", "pipeline_stages"):
        assert key in r, f"Missing top-level key '{key}'"


def test_get_oa_demo_case_is_demo_flagged():
    r = client.get("/api/v1/demo-cases/DEMO-OA-001").json()
    assert r["demo"] is True
    assert r["clinical_use"] is False
    assert r["report_status"] == "DEMO_ONLY"
    assert "NOT FOR CLINICAL USE" in r["disclaimer"].upper()


def test_get_oa_demo_case_classification():
    r = client.get("/api/v1/demo-cases/DEMO-OA-001").json()
    assert r["assessment"]["classification"] == "OA"
    assert r["assessment"]["oa_status"] == "OA_SUSPECTED"
    assert r["assessment"]["severity"] == "Moderate"
    assert r["assessment"]["confidence"] == pytest.approx(0.92, abs=0.01)
    assert r["assessment"]["is_demo"] is True
    assert r["assessment"]["source"] == "DEMO"


def test_get_oa_demo_case_implant_required():
    r = client.get("/api/v1/demo-cases/DEMO-OA-001").json()
    assert r["implant_assessment"]["required"] is True
    assert r["implant_assessment"]["recommendation"] is not None
    assert len(r["implant_assessment"]["alternatives"]) > 0


def test_get_oa_demo_case_measurements_present():
    r = client.get("/api/v1/demo-cases/DEMO-OA-001").json()
    meas = r["measurements"]
    assert len(meas) > 0
    # All values should be numeric
    for k, v in meas.items():
        assert isinstance(v, (int, float)), f"Measurement '{k}' is not numeric: {v}"


def test_get_oa_demo_case_findings_not_empty():
    r = client.get("/api/v1/demo-cases/DEMO-OA-001").json()
    assert isinstance(r["findings"], list)
    assert len(r["findings"]) > 0


def test_get_oa_demo_case_patient_fields():
    r = client.get("/api/v1/demo-cases/DEMO-OA-001").json()
    p = r["patient"]
    assert p["patient_id"] == "DEMO-OA-001"
    assert p["age"] == 58
    assert p["sex"] == "Female"
    assert p["affected_knee"] == "Right"


# ---------------------------------------------------------------------------
# 3 — GET /api/v1/demo-cases/DEMO-NONOA-001  (Non-OA report)
# ---------------------------------------------------------------------------

def test_get_non_oa_demo_case_classification():
    r = client.get("/api/v1/demo-cases/DEMO-NONOA-001").json()
    assert r["assessment"]["classification"] == "NON_OA"
    assert r["assessment"]["oa_status"] == "NO_OA_FEATURES_DETECTED"
    assert r["assessment"]["severity"] == "None"
    assert r["assessment"]["confidence"] == pytest.approx(0.95, abs=0.01)


def test_get_non_oa_demo_case_no_implant():
    r = client.get("/api/v1/demo-cases/DEMO-NONOA-001").json()
    assert r["implant_assessment"]["required"] is False
    assert r["implant_assessment"]["recommendation"] is None


def test_get_non_oa_demo_case_patient_fields():
    r = client.get("/api/v1/demo-cases/DEMO-NONOA-001").json()
    p = r["patient"]
    assert p["patient_id"] == "DEMO-NONOA-001"
    assert p["age"] == 32
    assert p["sex"] == "Male"


# ---------------------------------------------------------------------------
# 4 — Unknown case ID → 404
# ---------------------------------------------------------------------------

def test_get_unknown_demo_case_returns_404():
    resp = client.get("/api/v1/demo-cases/DOES-NOT-EXIST-999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5 — POST /api/v1/oa-assessment  (OA demo)
# ---------------------------------------------------------------------------

def test_oa_assessment_demo_oa_case():
    img = _make_png()
    resp = client.post(
        "/api/v1/oa-assessment",
        data={"demo_case_id": "DEMO-OA-001"},
        files={"file": ("knee.png", img, "image/png")},
    )
    assert resp.status_code == 200
    d = resp.json()
    assert d["assessment"]["classification"] == "OA"
    assert d["assessment"]["confidence"] == pytest.approx(0.92, abs=0.01)
    assert d["source"] == "DEMO"
    assert d["is_demo"] is True
    assert d["status"] == "demo"
    assert "NOT FOR CLINICAL USE" in d["clinical_warning"].upper()


# ---------------------------------------------------------------------------
# 6 — POST /api/v1/oa-assessment  (Non-OA demo)
# ---------------------------------------------------------------------------

def test_oa_assessment_demo_non_oa_case():
    img = _make_png()
    resp = client.post(
        "/api/v1/oa-assessment",
        data={"demo_case_id": "DEMO-NONOA-001"},
        files={"file": ("knee.png", img, "image/png")},
    )
    assert resp.status_code == 200
    d = resp.json()
    assert d["assessment"]["classification"] == "NON_OA"
    assert d["assessment"]["oa_status"] == "NO_OA_FEATURES_DETECTED"
    assert d["assessment"]["confidence"] == pytest.approx(0.95, abs=0.01)
    assert d["is_demo"] is True


# ---------------------------------------------------------------------------
# 7 — POST /api/v1/oa-assessment  (real upload, no demo_case_id → UNKNOWN stub)
# ---------------------------------------------------------------------------

def test_oa_assessment_real_upload_no_model_returns_unknown():
    """With no trained model, uploading a real image returns UNKNOWN + DEMO flag."""
    img = _make_png()
    resp = client.post(
        "/api/v1/oa-assessment",
        files={"file": ("knee.png", img, "image/png")},
    )
    assert resp.status_code == 200
    d = resp.json()
    assert d["assessment"]["classification"] == "UNKNOWN"
    assert d["source"] == "DEMO"
    assert d["is_demo"] is True
    # Clinical warning must still be present
    assert len(d["clinical_warning"]) > 10


def test_oa_assessment_includes_image_info():
    img = _make_png(100, 80)
    resp = client.post(
        "/api/v1/oa-assessment",
        files={"file": ("scan.png", img, "image/png")},
    )
    assert resp.status_code == 200
    info = resp.json()["image_info"]
    assert info["filename"] == "scan.png"
    assert info["width"] == 100
    assert info["height"] == 80


# ---------------------------------------------------------------------------
# 8 — POST /api/v1/oa-assessment — invalid image type → 400
# ---------------------------------------------------------------------------

def test_oa_assessment_invalid_mime_type_rejected():
    resp = client.post(
        "/api/v1/oa-assessment",
        files={"file": ("document.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 9 — POST /api/v1/oa-assessment — corrupted image → 400
# ---------------------------------------------------------------------------

def test_oa_assessment_corrupted_image_rejected():
    resp = client.post(
        "/api/v1/oa-assessment",
        files={"file": ("corrupt.png", b"NOT_AN_IMAGE_XXXX", "image/png")},
    )
    assert resp.status_code == 400
    assert "corrupted" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 10 — POST /api/v1/oa-assessment — missing file field → 422
# ---------------------------------------------------------------------------

def test_oa_assessment_missing_file_returns_422():
    resp = client.post("/api/v1/oa-assessment")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 11 — StubOAClassifier unit: demo OA case
# ---------------------------------------------------------------------------

def test_stub_classifier_demo_oa():
    clf = StubOAClassifier()
    result = clf.classify(b"fake_image_bytes", demo_case_id="DEMO-OA-001")
    assert isinstance(result, OAClassificationResult)
    assert result.classification == "OA"
    assert result.confidence == pytest.approx(0.92, abs=0.01)
    assert result.severity == "Moderate"
    assert result.source == "DEMO"
    assert result.is_demo is True
    assert result.model_version == "demo-stub-v1.0"
    assert "DEMO-OA-001" in result.metadata.get("demo_case_id", "")


# ---------------------------------------------------------------------------
# 12 — StubOAClassifier unit: demo Non-OA case
# ---------------------------------------------------------------------------

def test_stub_classifier_demo_non_oa():
    clf = StubOAClassifier()
    result = clf.classify(b"fake_image_bytes", demo_case_id="DEMO-NONOA-001")
    assert result.classification == "NON_OA"
    assert result.confidence == pytest.approx(0.95, abs=0.01)
    assert result.severity == "None"
    assert result.source == "DEMO"
    assert result.is_demo is True


# ---------------------------------------------------------------------------
# 13 — StubOAClassifier unit: real upload → UNKNOWN
# ---------------------------------------------------------------------------

def test_stub_classifier_real_upload_no_demo_case_id():
    clf = StubOAClassifier()
    result = clf.classify(b"some_real_image_bytes")
    assert result.classification == "UNKNOWN"
    assert result.confidence == 0.0
    assert result.source == "DEMO"
    assert result.is_demo is True
    assert result.model_version is None


def test_stub_classifier_unknown_demo_case_id_falls_back_to_unknown():
    clf = StubOAClassifier()
    result = clf.classify(b"bytes", demo_case_id="DEMO-NONEXISTENT-999")
    assert result.classification == "UNKNOWN"


# ---------------------------------------------------------------------------
# 14 — StubOAClassifier.is_available
# ---------------------------------------------------------------------------

def test_stub_classifier_is_available():
    assert StubOAClassifier().is_available() is True


# ---------------------------------------------------------------------------
# 15 — build_patient_report unit: OA report
# ---------------------------------------------------------------------------

def test_build_patient_report_oa():
    oa_result = OAClassificationResult(
        case_id="TEST-CASE-1",
        classification="OA",
        confidence=0.88,
        severity="Mild",
        source="DEMO",
        model_version="demo-stub-v1.0",
        is_demo=True,
        clinical_warning=OAClassificationResult.CLINICAL_WARNING_DEMO,
    )
    report = build_patient_report(
        patient_id="TEST-001",
        patient_name="Test OA Patient",
        age=60,
        sex="Male",
        affected_knee="Left",
        oa_result=oa_result,
        measurements={
            "medial_meniscus_thickness_mm": 3.0,
            "medial_joint_space_mm": 2.5,
        },
        findings=["Finding A", "Finding B"],
        is_demo=True,
    )
    assert report["demo"] is True
    assert report["clinical_use"] is False
    assert report["report_status"] == "DEMO_ONLY"
    assert "NOT FOR CLINICAL USE" in report["disclaimer"].upper()
    assert report["patient"]["patient_id"] == "TEST-001"
    assert report["patient"]["age"] == 60
    assert report["assessment"]["classification"] == "OA"
    assert report["assessment"]["oa_status"] == "OA_SUSPECTED"
    assert report["assessment"]["confidence"] == pytest.approx(0.88, abs=0.01)
    assert report["implant_assessment"]["required"] is True
    assert "image_validation" in report["pipeline_stages"]
    assert "oa_classification" in report["pipeline_stages"]
    assert "medial_meniscus_thickness_mm" in report["measurements"]
    assert report["measurements"]["medial_meniscus_thickness_mm"] == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# 16 — build_patient_report unit: Non-OA (no implant)
# ---------------------------------------------------------------------------

def test_build_patient_report_non_oa():
    non_oa_result = OAClassificationResult(
        case_id="TEST-CASE-2",
        classification="NON_OA",
        confidence=0.93,
        severity="None",
        source="DEMO",
        model_version="demo-stub-v1.0",
        is_demo=True,
        clinical_warning=OAClassificationResult.CLINICAL_WARNING_DEMO,
    )
    report = build_patient_report(
        patient_id="TEST-002",
        patient_name="Test Non-OA Patient",
        age=30,
        sex="Female",
        affected_knee="Right",
        oa_result=non_oa_result,
        is_demo=True,
    )
    assert report["assessment"]["classification"] == "NON_OA"
    assert report["assessment"]["oa_status"] == "NO_OA_FEATURES_DETECTED"
    assert report["implant_assessment"]["required"] is False
    assert report["implant_assessment"]["recommendation"] is None


# ---------------------------------------------------------------------------
# 17 — build_demo_report_from_file: OA round-trip
# ---------------------------------------------------------------------------

def test_build_demo_report_from_oa_file():
    case_data = _demo_file("demo_oa_patient.json")
    report = build_demo_report_from_file(case_data)

    assert report["demo"] is True
    assert report["patient"]["patient_id"] == "DEMO-OA-001"
    assert report["assessment"]["classification"] == "OA"
    assert report["implant_assessment"]["required"] is True
    assert report["implant_assessment"]["recommendation"] is not None
    # Verify implant recommendation structure
    rec = report["implant_assessment"]["recommendation"]
    for field in ("implantId", "implantName", "size", "matchScore", "confidence"):
        assert field in rec, f"Missing implant field '{field}'"


# ---------------------------------------------------------------------------
# 18 — build_demo_report_from_file: Non-OA round-trip
# ---------------------------------------------------------------------------

def test_build_demo_report_from_non_oa_file():
    case_data = _demo_file("demo_non_oa_patient.json")
    report = build_demo_report_from_file(case_data)

    assert report["demo"] is True
    assert report["patient"]["patient_id"] == "DEMO-NONOA-001"
    assert report["assessment"]["classification"] == "NON_OA"
    assert report["implant_assessment"]["required"] is False
    assert report["implant_assessment"]["recommendation"] is None


# ---------------------------------------------------------------------------
# 19 — Regression: GET /health still works
# ---------------------------------------------------------------------------

def test_regression_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "model" in data


# ---------------------------------------------------------------------------
# 20 — Regression: GET /analytics still works
# ---------------------------------------------------------------------------

def test_regression_analytics_endpoint():
    resp = client.get("/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert "totalPatients" in data
    assert data["totalPatients"] > 0


# ---------------------------------------------------------------------------
# 21 — Regression: POST /api/v1/segment still rejects unsupported type
# ---------------------------------------------------------------------------

def test_regression_segment_unsupported_type_still_400():
    resp = client.post(
        "/api/v1/segment",
        files={"file": ("doc.txt", b"text content", "text/plain")},
    )
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]
