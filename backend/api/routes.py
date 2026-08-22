import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from config import settings
from database.connection import check_database_connection
from services.analytics import analytics_service
from services.model_adapter import (
    ModelNotAvailableError,
    PendingModelAdapter,
    UNetModelAdapter,
    model_adapter_service,
)
from services.postprocessor import (
    PostprocessingInput,
    PostprocessingNotConfiguredError,
    PendingPostprocessor,
    UNetPostprocessor,
    postprocessor_service,
)
from services.preprocessor import preprocessor_service
from services.persistence import (
    persist_prediction_failure,
    persist_prediction_success,
)
from services.validator import validate_image_upload

logger = logging.getLogger(__name__)
router = APIRouter()
analytics = analytics_service

DEFAULT_MODEL_ADAPTER = model_adapter_service
DEFAULT_POSTPROCESSOR = postprocessor_service
_live_model_adapter = None
_live_postprocessor = None


class PatientMeasurementsRequest(BaseModel):
    femurWidth: float = Field(..., gt=0)
    femurAP: float = Field(..., gt=0)
    tibiaWidth: float = Field(..., gt=0)
    tibiaAP: float = Field(..., gt=0)


class ImplantRecommendationResponse(BaseModel):
    implantId: str
    implantName: str
    size: str
    matchScore: float
    confidence: float
    measurementDifference: float
    rank: int | None = None


class ImplantMatchResponse(BaseModel):
    recommendation: ImplantRecommendationResponse
    alternatives: list[ImplantRecommendationResponse]


DEMO_PATIENTS: list[dict[str, Any]] = [
    {"id": "P001", "age": 65, "sex": "M", "meniscusThickness": 3.2, "oaStatus": "OA", "analysisStatus": "Completed"},
    {"id": "P002", "age": 45, "sex": "F", "meniscusThickness": 5.8, "oaStatus": "Non-OA", "analysisStatus": "Completed"},
    {"id": "P003", "age": 72, "sex": "M", "meniscusThickness": 2.8, "oaStatus": "OA", "analysisStatus": "Completed"},
    {"id": "P004", "age": 38, "sex": "F", "meniscusThickness": 6.1, "oaStatus": "Non-OA", "analysisStatus": "Completed"},
    {"id": "P005", "age": 68, "sex": "F", "meniscusThickness": 3.5, "oaStatus": "OA", "analysisStatus": "Completed"},
    {"id": "P006", "age": 52, "sex": "M", "meniscusThickness": 5.2, "oaStatus": "Non-OA", "analysisStatus": "Completed"},
    {"id": "P007", "age": 70, "sex": "M", "meniscusThickness": 3.0, "oaStatus": "OA", "analysisStatus": "Completed"},
    {"id": "P008", "age": 42, "sex": "F", "meniscusThickness": 5.5, "oaStatus": "Non-OA", "analysisStatus": "Completed"},
    {"id": "P009", "age": 75, "sex": "M", "meniscusThickness": 2.5, "oaStatus": "OA", "analysisStatus": "Completed"},
    {"id": "P010", "age": 35, "sex": "F", "meniscusThickness": 6.3, "oaStatus": "Non-OA", "analysisStatus": "Completed"},
    {"id": "P011", "age": 66, "sex": "F", "meniscusThickness": 3.4, "oaStatus": "OA", "analysisStatus": "Pending"},
    {"id": "P012", "age": 48, "sex": "M", "meniscusThickness": 5.7, "oaStatus": "Non-OA", "analysisStatus": "Completed"},
    {"id": "P013", "age": 71, "sex": "M", "meniscusThickness": 2.9, "oaStatus": "OA", "analysisStatus": "Completed"},
    {"id": "P014", "age": 40, "sex": "F", "meniscusThickness": 5.9, "oaStatus": "Non-OA", "analysisStatus": "Completed"},
    {"id": "P015", "age": 69, "sex": "M", "meniscusThickness": 3.3, "oaStatus": "OA", "analysisStatus": "Completed"},
]

DEMO_IMPLANTS: list[dict[str, Any]] = [
    {"id": "IMP-2024-A7", "name": "Genesis II Total Knee System", "femurWidth": 65.0, "femurAP": 58.0, "tibiaWidth": 72.0, "tibiaAP": 48.0, "sizes": ["Small", "Medium", "Large", "XL"]},
    {"id": "IMP-2024-B3", "name": "Attune Knee System", "femurWidth": 64.5, "femurAP": 57.5, "tibiaWidth": 71.0, "tibiaAP": 47.5, "sizes": ["Small", "Medium", "Large", "XL"]},
    {"id": "IMP-2024-C5", "name": "NexGen LPS-Flex", "femurWidth": 66.0, "femurAP": 59.0, "tibiaWidth": 73.0, "tibiaAP": 49.0, "sizes": ["Small", "Medium", "Large", "XL"]},
    {"id": "IMP-2024-D2", "name": "Persona Knee System", "femurWidth": 63.0, "femurAP": 56.0, "tibiaWidth": 70.0, "tibiaAP": 46.5, "sizes": ["Small", "Medium", "Large", "XL"]},
    {"id": "IMP-2024-E8", "name": "Triathlon Total Knee", "femurWidth": 67.0, "femurAP": 60.0, "tibiaWidth": 74.0, "tibiaAP": 50.0, "sizes": ["Small", "Medium", "Large", "XL"]},
]


def _euclidean_distance(measurements: PatientMeasurementsRequest, implant: dict[str, Any]) -> float:
    return (
        (measurements.femurWidth - implant["femurWidth"]) ** 2
        + (measurements.femurAP - implant["femurAP"]) ** 2
        + (measurements.tibiaWidth - implant["tibiaWidth"]) ** 2
        + (measurements.tibiaAP - implant["tibiaAP"]) ** 2
    ) ** 0.5


def _match_score(distance: float, max_distance: float) -> float:
    if max_distance == 0:
        return 100.0
    score = max(0.0, 100.0 - (distance / max_distance * 100.0))
    return round(score, 1)


def _confidence(match_score: float, distance: float) -> float:
    base_confidence = match_score * 0.8
    distance_penalty = min(distance * 2, 20)
    confidence = max(0.0, min(100.0, base_confidence - distance_penalty))
    return round(confidence, 1)


def _determine_size(avg_measurement: float) -> str:
    if avg_measurement < 50:
        return "Small"
    if avg_measurement < 60:
        return "Medium"
    if avg_measurement < 70:
        return "Large"
    return "XL"


def _resolve_live_model_adapter():
    global _live_model_adapter
    current = model_adapter_service
    if isinstance(current, PendingModelAdapter):
        if current is DEFAULT_MODEL_ADAPTER:
            if _live_model_adapter is None or not _live_model_adapter.is_loaded():
                _live_model_adapter = UNetModelAdapter()
            return _live_model_adapter
        return current
    return current


def _resolve_live_postprocessor():
    global _live_postprocessor
    current = postprocessor_service
    if isinstance(current, PendingPostprocessor):
        if current is DEFAULT_POSTPROCESSOR:
            if _live_postprocessor is None or not _live_postprocessor.is_configured():
                _live_postprocessor = UNetPostprocessor()
            return _live_postprocessor
        return current
    return current


@router.get(
    "/health",
    tags=["system"],
    summary="Health check",
    response_description="Backend status, application name, version, and model readiness.",
)
async def health_check():
    """Returns service health and whether the live model adapter is ready."""
    try:
        live_model = _resolve_live_model_adapter()
        model_ready = bool(live_model.is_loaded())
    except Exception:
        model_ready = False

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "model": {
            "ready": model_ready,
            "adapter": type(_resolve_live_model_adapter()).__name__ if model_ready else type(model_adapter_service).__name__,
        },
    }


@router.get(
    "/health/db",
    tags=["system"],
    summary="Database connectivity check",
    response_description="Truthful PostgreSQL connectivity status.",
)
async def database_health_check():
    """Reports real database connectivity without exposing credentials.

    Never returns DATABASE_URL, passwords, or internal error details.
    """
    configured = bool(settings.DATABASE_URL and settings.DATABASE_URL.strip())
    ok, detail = check_database_connection()
    return {
        "status": "ok" if ok else "unavailable",
        "database": {
            "configured": configured,
            "connected": ok,
            "detail": detail,
        },
    }


@router.get("/analytics")
async def get_analytics():
    """Return dashboard-ready patient and OA analytics data."""
    df = DEMO_PATIENTS
    total_patients = len(df)
    oa_patients = sum(1 for patient in df if patient["oaStatus"] == "OA")
    non_oa_patients = total_patients - oa_patients
    oa_percentage = round((oa_patients / total_patients * 100), 1) if total_patients else 0.0
    thickness_values = [float(patient["meniscusThickness"]) for patient in df]
    avg_meniscus = round(sum(thickness_values) / len(thickness_values), 1) if thickness_values else 0.0
    min_meniscus = round(min(thickness_values), 1) if thickness_values else 0.0
    max_meniscus = round(max(thickness_values), 1) if thickness_values else 0.0

    age_distribution = []
    for min_age, max_age in [(30, 40), (41, 50), (51, 60), (61, 70), (71, 80)]:
        age_group = [patient for patient in df if min_age <= patient["age"] <= max_age]
        oa_count = sum(1 for patient in age_group if patient["oaStatus"] == "OA")
        non_oa_count = len(age_group) - oa_count
        age_distribution.append({"age": f"{min_age}-{max_age}", "OA": oa_count, "NonOA": non_oa_count})

    sex_distribution = []
    for sex, label in {"M": "Male", "F": "Female"}.items():
        sex_group = [patient for patient in df if patient["sex"] == sex]
        oa_count = sum(1 for patient in sex_group if patient["oaStatus"] == "OA")
        non_oa_count = len(sex_group) - oa_count
        sex_distribution.append({"sex": label, "OA": oa_count, "NonOA": non_oa_count})

    return {
        "totalPatients": total_patients,
        "oaPatients": oa_patients,
        "nonOaPatients": non_oa_patients,
        "oaPercentage": oa_percentage,
        "avgMeniscusThickness": avg_meniscus,
        "minMeniscusThickness": min_meniscus,
        "maxMeniscusThickness": max_meniscus,
        "patients": df,
        "ageDistribution": age_distribution,
        "sexDistribution": sex_distribution,
    }


@router.post("/implant-match")
async def match_implant(measurements: PatientMeasurementsRequest):
    """Return a best implant recommendation and alternatives for a patient."""
    results = []
    for implant in DEMO_IMPLANTS:
        distance = _euclidean_distance(measurements, implant)
        results.append({"implant": implant, "distance": distance})

    results.sort(key=lambda item: item["distance"])
    max_distance = max((item["distance"] for item in results), default=1.0)
    average_measurement = (
        measurements.femurWidth + measurements.femurAP + measurements.tibiaWidth + measurements.tibiaAP
    ) / 4

    recommendations = []
    for rank, result in enumerate(results, start=1):
        implant = result["implant"]
        distance = result["distance"]
        score = _match_score(distance, max_distance)
        conf = _confidence(score, distance)
        recommendations.append(
            {
                "implantId": implant["id"],
                "implantName": implant["name"],
                "size": _determine_size(average_measurement),
                "matchScore": score,
                "confidence": conf,
                "measurementDifference": round(distance, 2),
                "rank": rank,
            }
        )

    return {
        "recommendation": recommendations[0],
        "alternatives": recommendations[1:4],
    }


@router.post(
    "/api/v1/segment",
    status_code=status.HTTP_200_OK,
    tags=["segmentation"],
    summary="Segment an uploaded medical image",
    responses={
        200: {"description": "Segmentation completed successfully."},
        400: {
            "description": (
                "Unsupported file type, empty file, corrupted image, "
                "or image dimensions exceed MAX_IMAGE_DIMENSION_PX."
            )
        },
        413: {"description": "File exceeds MAX_UPLOAD_SIZE_MB."},
        422: {"description": "Multipart 'file' field missing (FastAPI validation)."},
        503: {
            "description": (
                "ML model adapter or postprocessor not configured/loaded yet "
                "(no weights registered)."
            )
        },
        500: {
            "description": "Unexpected preprocessing, inference, or postprocessing failure."
        },
    },
)
async def segment_image(file: UploadFile = File(...)):
    """Segment an uploaded image and return frontend-ready results.

    Pipeline: validate -> preprocess -> model inference -> postprocess.

    - `file`: required multipart image (JPEG/JPG/PNG/WebP/BMP/TIFF, <= MAX_UPLOAD_SIZE_MB).
    - Success: JSON with base64 mask, overlay, metrics, and metadata.
    - While the real ML model is pending, requests return 503 after
      successful validation/preprocessing.
    """
    analytics.emit(
        "segment_request_started",
        {
            "filename": file.filename,
            "content_type": file.content_type,
        },
    )

    try:
        # 1. Image Upload Validation
        contents, (orig_w, orig_h) = await validate_image_upload(file)
        analytics.emit(
            "image_validated",
            {
                "filename": file.filename,
                "original_width": orig_w,
                "original_height": orig_h,
            },
        )

        # 2. Image Preprocessing
        try:
            container = preprocessor_service.preprocess(contents)
            analytics.emit(
                "preprocessing_completed",
                {
                    "filename": file.filename,
                    "processed_shape": list(getattr(container, "processed_shape", [])),
                },
            )
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image could not be processed. The file may be corrupted or in an unsupported format.",
            ) from e
        except Exception as e:
            logger.exception("Unexpected preprocessing failure")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Image preprocessing failed.",
            ) from e

        # 3. Model Adapter Inference Layer
        try:
            active_model_adapter = _resolve_live_model_adapter()
            analytics.emit(
                "model_resolved",
                {
                    "filename": file.filename,
                    "adapter_name": type(active_model_adapter).__name__,
                },
            )
            prediction = active_model_adapter.predict(container)
            analytics.emit(
                "inference_completed",
                {
                    "filename": file.filename,
                    "adapter_name": type(active_model_adapter).__name__,
                    "execution_time_ms": getattr(prediction, "execution_time_ms", None),
                },
            )
        except ModelNotAvailableError as e:
            analytics.emit(
                "segmentation_failed",
                {
                    "filename": file.filename,
                    "stage": "inference",
                    "error": str(e),
                },
            )
            persist_prediction_failure(
                original_filename=file.filename,
                image_width=orig_w,
                image_height=orig_h,
                stage="inference",
                error=e,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            ) from e
        except HTTPException:
            raise
        except Exception as e:
            analytics.emit(
                "segmentation_failed",
                {
                    "filename": file.filename,
                    "stage": "inference",
                    "error": str(e),
                },
            )
            logger.exception("Model inference failure")
            persist_prediction_failure(
                original_filename=file.filename,
                image_width=orig_w,
                image_height=orig_h,
                stage="inference",
                error=e,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Model inference processing failed.",
            ) from e

        # 4. Postprocessing & Result Generation Layer
        try:
            active_postprocessor = _resolve_live_postprocessor()
            post_input = PostprocessingInput(
                prediction=prediction, container=container
            )
            result = active_postprocessor.process(post_input)
            analytics.emit(
                "postprocessing_completed",
                {
                    "filename": file.filename,
                    "metrics": result.metrics,
                    "adapter_name": type(active_model_adapter).__name__,
                },
            )
        except PostprocessingNotConfiguredError as e:
            analytics.emit(
                "segmentation_failed",
                {
                    "filename": file.filename,
                    "stage": "postprocessing",
                    "error": str(e),
                },
            )
            persist_prediction_failure(
                original_filename=file.filename,
                image_width=orig_w,
                image_height=orig_h,
                stage="postprocessing",
                error=e,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            ) from e
        except HTTPException:
            raise
        except Exception as e:
            analytics.emit(
                "segmentation_failed",
                {
                    "filename": file.filename,
                    "stage": "postprocessing",
                    "error": str(e),
                },
            )
            logger.exception("Postprocessing failure")
            persist_prediction_failure(
                original_filename=file.filename,
                image_width=orig_w,
                image_height=orig_h,
                stage="postprocessing",
                error=e,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Postprocessing result generation failed.",
            ) from e

        # 5. Persist prediction metadata to PostgreSQL (best-effort, never masks
        #    an already-successful result; failures are logged server-side).
        raw_execution_time = getattr(prediction, "execution_time_ms", None)
        execution_time_ms = (
            float(raw_execution_time)
            if isinstance(raw_execution_time, (int, float))
            else None
        )
        prediction_id = persist_prediction_success(
            original_filename=file.filename,
            image_width=orig_w,
            image_height=orig_h,
            metrics=result.metrics,
            metadata=result.metadata,
            execution_time_ms=execution_time_ms,
        )
        if prediction_id is None:
            logger.warning(
                "Segmentation succeeded but the prediction record was not "
                "persisted (database unavailable or not configured)."
            )

        analytics.emit(
            "segmentation_success",
            {
                "filename": file.filename,
                "metrics": result.metrics,
                "adapter_name": type(active_model_adapter).__name__,
                "response_status": 200,
            },
        )

        # 6. Structured JSON API Response
        return {
            "success": True,
            "filename": file.filename,
            "mask_image_base64": result.mask_image_base64,
            "overlay_image_base64": result.overlay_image_base64,
            "metrics": result.metrics,
            "metadata": result.metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        analytics.emit(
            "segmentation_failed",
            {
                "filename": file.filename,
                "stage": "unexpected",
                "error": str(e),
            },
        )
        logger.exception("Unexpected segmentation failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Segmenting image failed unexpectedly.",
        ) from e
