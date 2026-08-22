import io
from fastapi import HTTPException, UploadFile, status
from PIL import Image
from config import settings


async def validate_image_upload(file: UploadFile) -> tuple[bytes, tuple[int, int]]:
    """Validates the uploaded file for type, size, and image integrity.

    Returns:
        tuple[bytes, tuple[int, int]]: (raw_file_contents, (width, height))

    Raises:
        HTTPException: 400 Bad Request if file type is invalid or image is corrupted.
        HTTPException: 413 Payload Too Large if file size exceeds configured limit.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing or empty.",
        )

    # 1. Validate MIME content type or extension
    content_type = file.content_type.lower() if file.content_type else ""
    if content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{content_type}'. Allowed types: {', '.join(sorted(settings.ALLOWED_IMAGE_TYPES))}.",
        )

    # 2. Read contents
    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # 3. Validate file size
    if len(contents) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    # 4. Verify image integrity and extract dimensions safely
    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()
        # Re-open after verify() as Pillow recommends
        image = Image.open(io.BytesIO(contents))
        dimensions = image.size  # (width, height)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted image file.",
        )

    max_dim = settings.MAX_IMAGE_DIMENSION_PX
    if max_dim > 0 and (dimensions[0] > max_dim or dimensions[1] > max_dim):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image dimensions exceed the maximum allowed limit of {max_dim}x{max_dim} pixels.",
        )

    return contents, dimensions
