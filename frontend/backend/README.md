# KneeVision AI Backend

FastAPI backend for KneeVision AI orthopedic analysis platform.

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## Running the Server

```bash
# Development mode with auto-reload
python -m uvicorn main:app --reload

# Or use the script directly
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### GET /analytics
Get comprehensive OA analytics and patient data.

**Response:**
```json
{
  "totalPatients": 15,
  "oaPatients": 8,
  "nonOaPatients": 7,
  "oaPercentage": 53.3,
  "avgMeniscusThickness": 4.3,
  "minMeniscusThickness": 2.5,
  "maxMeniscusThickness": 6.3,
  "patients": [...],
  "ageDistribution": [...],
  "sexDistribution": [...]
}
```

### POST /implant-match
Match patient measurements to optimal knee implant.

**Request Body:**
```json
{
  "femurWidth": 65.5,
  "femurAP": 58.2,
  "tibiaWidth": 72.3,
  "tibiaAP": 48.7
}
```

**Response:**
```json
{
  "recommendation": {
    "implantId": "IMP-2024-A7",
    "implantName": "Genesis II Total Knee System",
    "size": "Medium",
    "matchScore": 94.5,
    "confidence": 92.3,
    "measurementDifference": 0.8,
    "rank": 1
  },
  "alternatives": [...]
}
```

### GET /health
Health check endpoint.

## CORS

Configured to allow requests from:
- `http://localhost:5173` (Vite dev server)
- `http://127.0.0.1:5173`
