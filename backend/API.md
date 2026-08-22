# Nexora Backend API Reference

Version: `0.1.0` (`APP_VERSION` in `backend/config.py`)
Interactive Swagger UI: `/docs` · ReDoc: `/redoc` · OpenAPI schema: `/openapi.json`

This document describes the API **exactly as implemented** in `backend/`.

---

## 1. Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Welcome message with links to docs and health |
| GET | `/health` | Health check |
| POST | `/api/v1/segment` | Segment an uploaded image |

## 2. `GET /`

Response `200`:

```json
{
  "message": "Welcome to Nexora Backend API",
  "docs": "/docs",
  "health": "/health"
}
```

## 3. `GET /health`

Response `200`:

```json
{
  "status": "healthy",
  "app_name": "Nexora Backend API",
  "version": "0.1.0"
}
```

## 4. `POST /api/v1/segment`

### Request format

- Content type: `multipart/form-data`
- Field: `file` (required) — one image file

### Supported image formats

Exactly the MIME types in `ALLOWED_IMAGE_TYPES` (`config.py`):

`image/jpeg`, `image/jpg`, `image/png`, `image/webp`, `image/bmp`, `image/tiff`

### Limits

| Limit | Default | Source |
|-------|---------|--------|
| Max upload size | 10 MB | `MAX_UPLOAD_SIZE_MB` in `config.py` |
| Max width/height | 10000 px | `MAX_IMAGE_DIMENSION_PX` (env-overridable) |

Files must also pass PIL integrity verification.

### Pipeline

1. **Validation** — filename present, content-type allowed, non-empty, size limit, image integrity, dimension limit (`services/validator.py`)
2. **Preprocessing** — color conversion, bilinear resize to `(256, 256)` (temporary defaults), float32 `[0,1]` normalization (`services/preprocessor.py`)
3. **Model inference** — via registered adapter (`services/model_adapter.py`)
4. **Postprocessing** — result generation (`services/postprocessor.py`)

### Successful response — `200`

```json
{
  "success": true,
  "filename": "scan.png",
  "mask_image_base64": "<base64 PNG or null>",
  "overlay_image_base64": "<base64 PNG or null>",
  "metrics": {},
  "metadata": {}
}
```

> Current live behavior: because no ML model is registered yet,
> validation and preprocessing run, then inference raises
> `ModelNotAvailableError` → **503**. The 200 example above shows the
> contract exercised by the test suite with configured adapters
> (`test_segment_endpoint.py`).

### Error response format

All errors use FastAPI's standard shape:

```json
{ "detail": "human readable message" }
```

Internal details, stack traces, and file paths are never included.
Unexpected exceptions are logged server-side only.

### HTTP status codes

| Code | Trigger |
|------|---------|
| 200 | Segmentation completed |
| 400 | Missing filename · unsupported content type · empty file · corrupted image · dimensions exceed `MAX_IMAGE_DIMENSION_PX` · preprocessing rejected the image |
| 413 | File exceeds `MAX_UPLOAD_SIZE_MB` |
| 422 | Multipart `file` field missing (request validation) |
| 503 | Model adapter not loaded (`ModelNotAvailableError`) or postprocessor not configured (`PostprocessingNotConfiguredError`) |
| 500 | Unexpected preprocessing / inference / postprocessing failure |

## 5. Configuration / environment variables

| Variable | Default | Effect |
|----------|---------|--------|
| `DEBUG` | `false` | FastAPI debug mode; `true` exposes tracebacks — never enable in demos |
| `MAX_IMAGE_DIMENSION_PX` | `10000` | Rejects images whose declared width or height exceeds this |
| `MODEL_WEIGHTS_PATH` | unset | Where the future model adapter will load weights from |

Non-env settings (edit `config.py`): upload limits, allowed types, CORS origins
(currently `localhost:3000`/`:5173`), preprocessing parameters
(`PREPROCESS_TARGET_SIZE=(256,256)`, `PREPROCESS_COLOR_MODE="RGB"`,
`PREPROCESS_NORMALIZE=True`, mean/std unset).

No secrets are required or hardcoded.

## 6. Model requirements

- **Framework:** not chosen yet — no ML dependency installed.
- **Weights:** none present in the repository.
- Until the ML team delivers weights + output specification:
  - `PendingModelAdapter.predict()` raises `ModelNotAvailableError` → 503
  - `PendingPostprocessor.process()` raises `PostprocessingNotConfiguredError` → 503
- Integration contract when ready: subclass `BaseModelAdapter`
  (`predict(PreprocessedImageContainer) -> ModelPredictionOutput`, `is_loaded()`)
  and `BasePostprocessor`
  (`process(PostprocessingInput) -> SegmentationResultOutput`, `is_configured()`),
  load weights once at construction.

## 7. Local development

```bash
cd backend
python -m pip install -r requirements.txt   # Python 3.10+ (developed on 3.13)
uvicorn main:app --reload                   # serves http://0.0.0.0:8000
```

Run tests:

```bash
python -m pytest -v
```

## 8. Example request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/segment \
  -F "file=@knee_scan.png;type=image/png"
```

## 9. Example responses

Current real behavior (model pending) — `503`:

```json
{
  "detail": "No trained ML model weights or framework adapter registered. Real model implementation is pending main branch updates from the ML team."
}
```

Rejected file — `400`:

```json
{ "detail": "Unsupported file type 'text/plain'. Allowed types: image/bmp, image/jpeg, image/jpg, image/png, image/tiff, image/webp." }
```

Success contract (as produced when adapters are configured, verified in tests) — `200`:

```json
{
  "success": true,
  "filename": "medical_scan.png",
  "mask_image_base64": "<base64-encoded PNG mask>",
  "overlay_image_base64": "<base64-encoded PNG overlay>",
  "metrics": { },
  "metadata": { }
}
```
