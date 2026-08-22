from fastapi import APIRouter, File, UploadFile, status
from config import settings
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
    """Validates uploaded image and runs generic preprocessing preparation pipeline.

    Does not execute model inference or generate segmentation masks.
    """
    contents, (orig_w, orig_h) = await validate_image_upload(file)

    # Execute preprocessing preparation
    preprocessed_container = preprocessor_service.preprocess(contents)

    return {
        "success": True,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(contents),
        "original_dimensions": {"width": orig_w, "height": orig_h},
        "preprocessing": {
            "status": preprocessed_container.metadata["status"],
            "processed_shape": list(preprocessed_container.processed_shape),
            "color_mode": preprocessed_container.metadata["color_mode"],
            "target_size": list(preprocessed_container.metadata["target_size"]),
            "normalized": preprocessed_container.metadata["normalized"],
            "specification_status": preprocessed_container.metadata[
                "specification_status"
            ],
        },
        "message": (
            "Image validated and preprocessed successfully using temporary configuration. "
            "Ready for future model adapter."
        ),
    }
