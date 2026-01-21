import os

class Config:
    REGION_ID = os.getenv("REGION_ID", "HIMACHAL_01")
    GRID_RES_M = 10.0
    
    # Thresholds
    RISK_THRESHOLD_PRIMARY = 0.8
    RISK_THRESHOLD_SECONDARY = 0.6
    
    # Model
    MODEL_PATH = os.path.join("models", "artifacts")
    
    # System
    MAX_LATENCY_SEC = 15.0
    
    # Offline
    SMS_GATEWAY_URL = os.getenv("SMS_GATEWAY", "http://localhost:8888/sms")
