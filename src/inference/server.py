from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import gzip
import json
from datetime import datetime

from src.inference.runner import InferenceRunner

app = FastAPI(title="Sentinel-LEWS Edge Server")
app.add_middleware(GZipMiddleware, minimum_size=1000)

runner = InferenceRunner()

# Pydantic Schemas
class GaugeRead(BaseModel):
    id: str
    lat: float
    lon: float
    ts: str
    rain_mm: float
    status: str

class IngestRequest(BaseModel):
    timestamp_utc: str
    region_id: str
    radar_tile: Optional[Dict[str, Any]] = None
    satellite_precip: Optional[Dict[str, Any]] = None
    gauges: List[GaugeRead]
    soil_moistures: Optional[List[float]] = None
    dem_hash: Optional[str] = None

@app.post("/ingest")
async def ingest_data(payload: IngestRequest):
    try:
        data = payload.dict()
        result = runner.ingest(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
async def predict_risk():
    """
    Triggers risk assessment.
    Returns compressed JSON if Accept-Encoding header supports gzip (handled by middleware),
    or strictly if we want to force manual binary response.
    """
    try:
        result = runner.predict()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "model_loaded": runner.ml_model is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/backtest")
async def run_backtest():
    return {"message": "Not implemented in server yet, run CLI"}
