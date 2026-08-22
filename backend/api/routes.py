import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from config import settings
from database.connection import check_database_connection
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

DEFAULT_MODEL_ADAPTER = model_adapter_service
DEFAULT_POSTPROCESSOR = postprocessor_service
_live_model_adapter = None
_live_postprocessor = None


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
    # 1. Image Upload Validation
    contents, (orig_w, orig_h) = await validate_image_upload(file)

    # 2. Image Preprocessing
    try:
        container = preprocessor_service.preprocess(contents)
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
        prediction = active_model_adapter.predict(container)
    except ModelNotAvailableError as e:
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
    except PostprocessingNotConfiguredError as e:
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

    # 6. Structured JSON API Response
    return {
        "success": True,
        "filename": file.filename,
        "mask_image_base64": result.mask_image_base64,
        "overlay_image_base64": result.overlay_image_base64,
        "metrics": result.metrics,
        "metadata": result.metadata,
    }
