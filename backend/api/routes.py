from fastapi import APIRouter, File, HTTPException, UploadFile, status
from config import settings
from services.model_adapter import (
    ModelNotAvailableError,
    model_adapter_service,
)
from services.postprocessor import (
    PostprocessingInput,
    PostprocessingNotConfiguredError,
    postprocessor_service,
)
from services.preprocessor import preprocessor_service
from services.validator import validate_image_upload

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint to verify backend status."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.post("/api/v1/segment", status_code=status.HTTP_200_OK)
async def segment_image(file: UploadFile = File(...)):
    """Main image segmentation endpoint.

    Executes pipeline: validate -> preprocess -> model adapter -> postprocess -> JSON response.
    """
    # 1. Image Upload Validation
    contents, (orig_w, orig_h) = await validate_image_upload(file)

    # 2. Image Preprocessing
    container = preprocessor_service.preprocess(contents)

    # 3. Model Adapter Inference Layer
    try:
        prediction = model_adapter_service.predict(container)
    except ModelNotAvailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model inference processing failed.",
        ) from e

    # 4. Postprocessing & Result Generation Layer
    try:
        post_input = PostprocessingInput(
            prediction=prediction, container=container
        )
        result = postprocessor_service.process(post_input)
    except PostprocessingNotConfiguredError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Postprocessing result generation failed.",
        ) from e

    # 5. Structured JSON API Response
    return {
        "success": True,
        "filename": file.filename,
        "mask_image_base64": result.mask_image_base64,
        "overlay_image_base64": result.overlay_image_base64,
        "metrics": result.metrics,
        "metadata": result.metadata,
    }
