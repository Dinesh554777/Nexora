"""OA Classification Service — pluggable interface.

Architecture
------------
BaseOAClassifier   Abstract contract every classifier must implement.
StubOAClassifier   Returns demo/synthetic results. Used when no trained model
                   is available. Always marks results with source="DEMO".
RealOAClassifier   Placeholder concrete class — wire in a trained model here
                   when one becomes available (see integrate_real_model()).

The active classifier is exposed as ``oa_classifier_service``. Swap it at
startup or in tests via dependency injection / monkeypatching, exactly the
same pattern used by model_adapter_service and postprocessor_service.

IMPORTANT
---------
The StubOAClassifier does NOT inspect the image content to decide OA/Non-OA.
It always returns a clearly labelled DEMO result whose classification is driven
only by the explicit ``demo_case_id`` parameter, never by the image filename
or any heuristic on the uploaded bytes.

When a real trained OA model is integrated, replace StubOAClassifier with
RealOAClassifier and plug the actual model weights path into config.py.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Output contract
# ---------------------------------------------------------------------------

@dataclass
class OAClassificationResult:
    """Structured output from any OA classifier.

    Fields
    ------
    case_id         Unique identifier for this assessment request.
    classification  "OA" | "NON_OA"
    confidence      Float in [0.0, 1.0].
    severity        "None" | "Mild" | "Moderate" | "Severe" | "Unknown"
    source          "DEMO" | "MODEL" — callers must surface this to the user.
    model_version   Human-readable model identifier, None when source="DEMO".
    is_demo         True when this result is synthetic / not from a real model.
    clinical_warning Always set; must be displayed in every UI that shows this result.
    metadata        Arbitrary extra data (feature importances, heatmap refs, etc.)
    """

    case_id: str
    classification: str          # "OA" | "NON_OA"
    confidence: float            # [0.0, 1.0]
    severity: str                # "None" | "Mild" | "Moderate" | "Severe" | "Unknown"
    source: str                  # "DEMO" | "MODEL"
    model_version: str | None
    is_demo: bool
    clinical_warning: str
    metadata: dict[str, Any] = field(default_factory=dict)

    CLINICAL_WARNING_DEMO = (
        "For demonstration only. Not a medical diagnosis. "
        "DEMO DATA — NOT FOR CLINICAL USE."
    )
    CLINICAL_WARNING_MODEL = (
        "AI-generated result for clinical decision support only. "
        "Must be reviewed by a qualified healthcare professional. "
        "This system does not provide medical diagnoses."
    )


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class BaseOAClassifier(ABC):
    """Abstract contract for all OA classifiers."""

    @abstractmethod
    def classify(
        self,
        image_bytes: bytes,
        *,
        demo_case_id: str | None = None,
    ) -> OAClassificationResult:
        """Classify knee image bytes and return an OAClassificationResult.

        Parameters
        ----------
        image_bytes:
            Raw bytes of the uploaded/demo image (already validated).
        demo_case_id:
            When provided ("DEMO-OA-001" or "DEMO-NONOA-001"), the stub
            returns the pre-configured demo result for that case.
            A real model implementation MUST ignore this parameter and
            always run inference.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when the classifier is ready to run inference."""


# ---------------------------------------------------------------------------
# Stub — demo-only, no model
# ---------------------------------------------------------------------------

_DEMO_CASES: dict[str, dict[str, Any]] = {
    "DEMO-OA-001": {
        "classification": "OA",
        "confidence": 0.92,
        "severity": "Moderate",
    },
    "DEMO-NONOA-001": {
        "classification": "NON_OA",
        "confidence": 0.95,
        "severity": "None",
    },
}


class StubOAClassifier(BaseOAClassifier):
    """Synthetic demo classifier — returns pre-configured results.

    This classifier NEVER analyses image content. It is used exclusively
    for jury/hackathon demonstrations when no real trained OA model exists.

    Decision logic
    --------------
    - If ``demo_case_id`` matches a known demo case → return that case's result.
    - For any real image upload (no demo_case_id) → return a clearly labelled
      DEMO result stating that no model is available.

    This means the system cannot be mistaken for running real OA inference.
    """

    def is_available(self) -> bool:
        # Stub is always "available" in the sense it will return a response,
        # but callers should check result.source == "DEMO".
        return True

    def classify(
        self,
        image_bytes: bytes,
        *,
        demo_case_id: str | None = None,
    ) -> OAClassificationResult:
        case_id = str(uuid.uuid4())

        if demo_case_id and demo_case_id in _DEMO_CASES:
            cfg = _DEMO_CASES[demo_case_id]
            return OAClassificationResult(
                case_id=case_id,
                classification=cfg["classification"],
                confidence=cfg["confidence"],
                severity=cfg["severity"],
                source="DEMO",
                model_version="demo-stub-v1.0",
                is_demo=True,
                clinical_warning=OAClassificationResult.CLINICAL_WARNING_DEMO,
                metadata={
                    "demo_case_id": demo_case_id,
                    "note": (
                        "Result is pre-configured demo data. "
                        "Image content was NOT analysed."
                    ),
                },
            )

        # Real image uploaded — no model available
        return OAClassificationResult(
            case_id=case_id,
            classification="UNKNOWN",
            confidence=0.0,
            severity="Unknown",
            source="DEMO",
            model_version=None,
            is_demo=True,
            clinical_warning=OAClassificationResult.CLINICAL_WARNING_DEMO,
            metadata={
                "note": (
                    "No trained OA classification model is integrated. "
                    "Upload was validated but OA assessment cannot be performed. "
                    "Connect a real model via RealOAClassifier."
                ),
                "image_size_bytes": len(image_bytes),
            },
        )


# ---------------------------------------------------------------------------
# Real classifier placeholder — wire your model here
# ---------------------------------------------------------------------------

class RealOAClassifier(BaseOAClassifier):
    """Placeholder for a future trained OA classification model.

    How to integrate
    ----------------
    1. Add your model weights path to config.py as OA_CLASSIFIER_WEIGHTS_PATH.
    2. Load the model in __init__ (see UNetModelAdapter for the pattern).
    3. Implement classify() to run real inference and return an
       OAClassificationResult with source="MODEL" and is_demo=False.
    4. Replace oa_classifier_service below with RealOAClassifier().
    5. Update the OA_CLASSIFIER_AVAILABLE flag in config if needed.

    This class intentionally raises NotImplementedError until integrated so
    the stub is used and results are never silently fabricated.
    """

    def __init__(self, weights_path: str | None = None) -> None:
        self.weights_path = weights_path
        self._model = None  # load model here

    def is_available(self) -> bool:
        return self._model is not None

    def classify(
        self,
        image_bytes: bytes,
        *,
        demo_case_id: str | None = None,
    ) -> OAClassificationResult:
        raise NotImplementedError(
            "RealOAClassifier has not been implemented yet. "
            "A trained OA classification model must be loaded first. "
            "See the docstring for integration instructions."
        )


# ---------------------------------------------------------------------------
# Active service instance — swap this for RealOAClassifier when ready
# ---------------------------------------------------------------------------

oa_classifier_service: BaseOAClassifier = StubOAClassifier()
