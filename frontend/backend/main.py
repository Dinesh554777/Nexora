from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd
import numpy as np
from pathlib import Path

app = FastAPI(title="KneeVision AI API", version="1.0.0")

# CORS configuration - Allow all localhost origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATA MODELS
# ============================================================================

class PatientMeasurements(BaseModel):
    femurWidth: float = Field(..., gt=0, description="Femur width in mm")
    femurAP: float = Field(..., gt=0, description="Femur anterior-posterior dimension in mm")
    tibiaWidth: float = Field(..., gt=0, description="Tibia width in mm")
    tibiaAP: float = Field(..., gt=0, description="Tibia anterior-posterior dimension in mm")

class ImplantRecommendation(BaseModel):
    implantId: str
    implantName: str
    size: str
    matchScore: float
    confidence: float
    measurementDifference: float
    rank: Optional[int] = None

class ImplantMatchResponse(BaseModel):
    recommendation: ImplantRecommendation
    alternatives: List[ImplantRecommendation]

class PatientRecord(BaseModel):
    id: str
    age: int
    sex: str
    meniscusThickness: float
    oaStatus: str
    analysisStatus: str

class AnalyticsResponse(BaseModel):
    totalPatients: int
    oaPatients: int
    nonOaPatients: int
    oaPercentage: float
    avgMeniscusThickness: float
    minMeniscusThickness: float
    maxMeniscusThickness: float
    patients: List[PatientRecord]
    ageDistribution: List[dict]
    sexDistribution: List[dict]

# ============================================================================
# IMPLANT DATABASE (Demo data)
# ============================================================================

IMPLANT_DATABASE = [
    {
        "id": "IMP-2024-A7",
        "name": "Genesis II Total Knee System",
        "femurWidth": 65.0,
        "femurAP": 58.0,
        "tibiaWidth": 72.0,
        "tibiaAP": 48.0,
        "sizes": ["Small", "Medium", "Large", "XL"]
    },
    {
        "id": "IMP-2024-B3",
        "name": "Attune Knee System",
        "femurWidth": 64.5,
        "femurAP": 57.5,
        "tibiaWidth": 71.0,
        "tibiaAP": 47.5,
        "sizes": ["Small", "Medium", "Large", "XL"]
    },
    {
        "id": "IMP-2024-C5",
        "name": "NexGen LPS-Flex",
        "femurWidth": 66.0,
        "femurAP": 59.0,
        "tibiaWidth": 73.0,
        "tibiaAP": 49.0,
        "sizes": ["Small", "Medium", "Large", "XL"]
    },
    {
        "id": "IMP-2024-D2",
        "name": "Persona Knee System",
        "femurWidth": 63.0,
        "femurAP": 56.0,
        "tibiaWidth": 70.0,
        "tibiaAP": 46.5,
        "sizes": ["Small", "Medium", "Large", "XL"]
    },
    {
        "id": "IMP-2024-E8",
        "name": "Triathlon Total Knee",
        "femurWidth": 67.0,
        "femurAP": 60.0,
        "tibiaWidth": 74.0,
        "tibiaAP": 50.0,
        "sizes": ["Small", "Medium", "Large", "XL"]
    },
]

# ============================================================================
# PATIENT DATA (Demo data)
# ============================================================================

PATIENT_DATA = [
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

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_euclidean_distance(measurements: PatientMeasurements, implant: dict) -> float:
    """Calculate Euclidean distance between patient measurements and implant dimensions"""
    return np.sqrt(
        (measurements.femurWidth - implant["femurWidth"]) ** 2 +
        (measurements.femurAP - implant["femurAP"]) ** 2 +
        (measurements.tibiaWidth - implant["tibiaWidth"]) ** 2 +
        (measurements.tibiaAP - implant["tibiaAP"]) ** 2
    )

def determine_size(avg_measurement: float) -> str:
    """Determine implant size based on average measurement"""
    if avg_measurement < 50:
        return "Small"
    elif avg_measurement < 60:
        return "Medium"
    elif avg_measurement < 70:
        return "Large"
    else:
        return "XL"

def calculate_match_score(distance: float, max_distance: float) -> float:
    """Convert distance to match score (0-100)"""
    # Inverse relationship: smaller distance = higher score
    if max_distance == 0:
        return 100.0
    score = max(0, 100 - (distance / max_distance * 100))
    return round(score, 1)

def calculate_confidence(match_score: float, distance: float) -> float:
    """Calculate confidence based on match score and distance"""
    # Higher match score and lower distance = higher confidence
    base_confidence = match_score * 0.8
    distance_penalty = min(distance * 2, 20)  # Max 20% penalty
    confidence = max(0, min(100, base_confidence - distance_penalty))
    return round(confidence, 1)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def read_root():
    return {
        "message": "KneeVision AI API",
        "version": "1.0.0",
        "endpoints": {
            "analytics": "/analytics",
            "implant_match": "/implant-match"
        }
    }

@app.get("/analytics", response_model=AnalyticsResponse)
def get_analytics():
    """Get comprehensive OA analytics and patient data"""
    try:
        df = pd.DataFrame(PATIENT_DATA)
        
        # Calculate summary statistics
        total_patients = len(df)
        oa_patients = len(df[df["oaStatus"] == "OA"])
        non_oa_patients = len(df[df["oaStatus"] == "Non-OA"])
        oa_percentage = round((oa_patients / total_patients * 100), 1) if total_patients > 0 else 0.0
        
        avg_meniscus = round(df["meniscusThickness"].mean(), 1)
        min_meniscus = round(df["meniscusThickness"].min(), 1)
        max_meniscus = round(df["meniscusThickness"].max(), 1)
        
        # Age distribution
        age_bins = [(30, 40), (41, 50), (51, 60), (61, 70), (71, 80)]
        age_distribution = []
        for min_age, max_age in age_bins:
            age_group_df = df[(df["age"] >= min_age) & (df["age"] <= max_age)]
            oa_count = len(age_group_df[age_group_df["oaStatus"] == "OA"])
            non_oa_count = len(age_group_df[age_group_df["oaStatus"] == "Non-OA"])
            age_distribution.append({
                "age": f"{min_age}-{max_age}",
                "OA": oa_count,
                "NonOA": non_oa_count
            })
        
        # Sex distribution
        sex_distribution = []
        for sex in ["M", "F"]:
            sex_df = df[df["sex"] == sex]
            oa_count = len(sex_df[sex_df["oaStatus"] == "OA"])
            non_oa_count = len(sex_df[sex_df["oaStatus"] == "Non-OA"])
            sex_distribution.append({
                "sex": "Male" if sex == "M" else "Female",
                "OA": oa_count,
                "NonOA": non_oa_count
            })
        
        # Convert patients to response format
        patients = [
            PatientRecord(**patient) for patient in PATIENT_DATA
        ]
        
        return AnalyticsResponse(
            totalPatients=total_patients,
            oaPatients=oa_patients,
            nonOaPatients=non_oa_patients,
            oaPercentage=oa_percentage,
            avgMeniscusThickness=avg_meniscus,
            minMeniscusThickness=min_meniscus,
            maxMeniscusThickness=max_meniscus,
            patients=patients,
            ageDistribution=age_distribution,
            sexDistribution=sex_distribution
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating analytics: {str(e)}")

@app.post("/implant-match", response_model=ImplantMatchResponse)
def match_implant(measurements: PatientMeasurements):
    """Match patient measurements to optimal knee implant"""
    try:
        # Calculate distances for all implants
        results = []
        for implant in IMPLANT_DATABASE:
            distance = calculate_euclidean_distance(measurements, implant)
            results.append({
                "implant": implant,
                "distance": distance
            })
        
        # Sort by distance (ascending)
        results.sort(key=lambda x: x["distance"])
        
        # Calculate max distance for normalization
        max_distance = max(r["distance"] for r in results) if results else 1.0
        
        # Determine size based on average measurement
        avg_measurement = (
            measurements.femurWidth + measurements.femurAP +
            measurements.tibiaWidth + measurements.tibiaAP
        ) / 4
        
        # Build recommendations
        recommendations = []
        for idx, result in enumerate(results):
            implant = result["implant"]
            distance = result["distance"]
            match_score = calculate_match_score(distance, max_distance)
            confidence = calculate_confidence(match_score, distance)
            size = determine_size(avg_measurement)
            
            recommendations.append(
                ImplantRecommendation(
                    implantId=implant["id"],
                    implantName=implant["name"],
                    size=size,
                    matchScore=match_score,
                    confidence=confidence,
                    measurementDifference=round(distance, 2),
                    rank=idx + 1
                )
            )
        
        if not recommendations:
            raise HTTPException(status_code=404, detail="No suitable implants found")
        
        # Return best match as recommendation, rest as alternatives
        return ImplantMatchResponse(
            recommendation=recommendations[0],
            alternatives=recommendations[1:4]  # Top 3 alternatives
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching implant: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "KneeVision AI API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
