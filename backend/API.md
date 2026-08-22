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
| GET | `/health/db` | PostgreSQL connectivity check |
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

## 4. `GET /health/db`

Reports truthful database connectivity. Never returns `DATABASE_URL`,
passwords, or internal error details.

Response when connected (`200`):

```json
{
  "status": "ok",
  "database": { "configured": true, "connected": true, "detail": "database connection ok" }
}
```

Response when PostgreSQL is unreachable or `DATABASE_URL` is unset (`200`, honest status):

```json
{
  "status": "unavailable",
  "database": {
    "configured": false,
    "connected": false,
    "detail": "DATABASE_URL is not configured. Set it via the environment or backend/.env (see backend/.env.example)."
  }
}
```

## 5. `POST /api/v1/segment`

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
5. **Persistence** — one committed `predictions` row in PostgreSQL (`services/persistence.py`): `success` after the full pipeline, or `failed` (sanitized stage + exception class name) when inference/postprocessing raised. Validation/preprocessing rejections are never persisted.

Persistence is best-effort: a database failure after successful inference is
logged server-side and reported via `/health/db` but never masks an
already-computed result, and no partial or invalid records are ever created
(single-row transactions).

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

## 6. Configuration / environment variables

| Variable | Default | Effect |
|----------|---------|--------|
| `DEBUG` | `false` | FastAPI debug mode; `true` exposes tracebacks — never enable in demos |
| `MAX_IMAGE_DIMENSION_PX` | `10000` | Rejects images whose declared width or height exceeds this |
| `MODEL_WEIGHTS_PATH` | unset | Where the future model adapter will load weights from |
| `DATABASE_URL` | unset | PostgreSQL connection string (SQLAlchemy format). Required for persistence and migrations; app boots without it, persistence is skipped with a server-side warning. Treated as a secret: never logged or returned by any endpoint. Password special characters must be percent-encoded (`@` → `%40`). |
| `NEXORA_API_KEY` | unset | Secret key for future external ML/API integration. Loaded from env or `backend/.env` (template: `.env.example`). Held as `SecretStr`; never logged. App starts without it — access via `settings.require_api_key()` raises a clear error when an integration needs it. |

Non-env settings (edit `config.py`): upload limits, allowed types, CORS origins
(currently `localhost:3000`/`:5173`), preprocessing parameters
(`PREPROCESS_TARGET_SIZE=(256,256)`, `PREPROCESS_COLOR_MODE="RGB"`,
`PREPROCESS_NORMALIZE=True`, mean/std unset).

No secrets are required or hardcoded.

## 7. Model requirements

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

## 8. PostgreSQL database

The backend persists segmentation metadata in PostgreSQL via SQLAlchemy 2.0
(`database/`, `models/prediction.py`) with Alembic migrations (`migrations/`).
Driver: `psycopg` 3 (installed with the `[binary]` extra via `requirements.txt`).

### 8.1 Required environment variables

Set `DATABASE_URL` in `backend/.env` (gitignored; template: `.env.example`):

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/nexora
```

Never commit real credentials anywhere. Percent-encode special characters in
the password (`@` → `%40`, etc.).

### 8.2 Create the Nexora database (once)

Using psql (adjust paths/credentials for your install):

```bash
psql -U postgres -h localhost -c "CREATE DATABASE nexora;"
```

or from pgAdmin: right-click Databases → Create → Database… → `nexora`.

Optionally create a dedicated least-privilege role instead of reusing a
superuser:

```sql
CREATE ROLE nexora_app LOGIN PASSWORD '<choose-a-strong-password>';
GRANT ALL PRIVILEGES ON DATABASE nexora TO nexora_app;
```

### 8.3 Run migrations

All commands run from `backend/`. Alembic reads `DATABASE_URL` from
`backend/.env` automatically (`migrations/env.py`).

```bash
python -m alembic upgrade head        # apply all pending migrations
python -m alembic current             # show applied revision
python -m alembic downgrade -1        # revert last migration
python -m alembic downgrade base      # drop all schema (destructive)
python -m alembic revision --autogenerate -m "message"   # new migration after model changes
```

Current revisions:

| Revision | Migration |
|----------|-----------|
| `0001` | create `predictions` table (+ `ix_predictions_status` index) |

Note: tests create throwaway SQLite schemas directly and do not use Alembic;
`Base.metadata.create_all()` is never used outside the test suite.

### 8.4 Schema — `predictions` table

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | autoincrement |
| status | VARCHAR(16) | `success` / `failed`, indexed |
| original_filename | VARCHAR(512) | truncated client-supplied name |
| image_width / image_height | INTEGER | original pixel dimensions |
| model_name | VARCHAR(128) | reserved for future registered adapters |
| execution_time_ms | FLOAT | inference time when available |
| metrics_json / metadata_json | JSON | postprocessor outputs |
| error_message | TEXT | sanitized `stage: ExceptionClass` on failures only |
| created_at / updated_at | TIMESTAMPTZ | server defaults |

Mask/overlay pixels are intentionally NOT stored as blobs (they are returned
inline by the API). If object/file storage is added later, reference columns
belong here — discuss before introducing large binary fields.

### 8.5 Verify connectivity

```bash
curl http://127.0.0.1:8000/health/db
```

`{"status": "ok", ...}` means PostgreSQL accepts connections. Failures return
honest status without credentials or internal details.

## 9. Local development

```bash
cd backend
python -m pip install -r requirements.txt   # Python 3.10+ (developed on 3.13)
uvicorn main:app --reload                   # serves http://0.0.0.0:8000
```

Run tests:

```bash
python -m pytest -v
```

## 10. Example request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/segment \
  -F "file=@knee_scan.png;type=image/png"
```

## 11. Example responses

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
