from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.oa_analytics import generate_analytics
from services.implant_matching import match_implants


app = FastAPI(
    title="Nexora Medical Analytics API",
    description="Implant Matching and OA Analytics Backend",
    version="1.0.0"
)


# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Nexora Backend API is running",
        "status": "success"
    }


@app.get("/analytics")
def get_analytics():
    """
    Return OA analytics.
    """

    return generate_analytics()


@app.post("/implant-match")
def implant_match(
    femur_width: float,
    femur_ap: float,
    tibia_width: float,
    tibia_ap: float
):
    """
    Recommend suitable implants based on
    patient femur and tibia measurements.
    """

    recommendations = match_implants(
        femur_width,
        femur_ap,
        tibia_width,
        tibia_ap
    )

    return {
        "status": "success",
        "recommendations": recommendations
    }