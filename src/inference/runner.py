import numpy as np
import pandas as pd
import json
import os
import time
from datetime import datetime

from src.models.fisical_fos import compute_fos_grid
from src.models.ml_residual import MLResidualModel
from src.preprocess.downscale import downscale_rainfall
from src.fusion.kalman_fusion import KalmanFuser

class InferenceRunner:
    def __init__(self, config=None):
        self.config = config or {}
        # Initialize internal state
        self.grid_shape = (500, 500) # Default, should come from DEM
        self.fusion_engine = KalmanFuser(self.grid_shape)
        
        # Load Static Data (DEM, Soil) - Mocks for now
        self.dem = np.ones(self.grid_shape) * 1000.0
        self.soil_params = {
            'c': np.ones(self.grid_shape) * 5000.0,
            'phi': np.ones(self.grid_shape) * 30.0,
            'gamma': np.ones(self.grid_shape) * 20000.0,
            'depth': np.ones(self.grid_shape) * 2.0,
            'ksat': np.ones(self.grid_shape) * 1e-5
        }
        self.initial_saturation = np.zeros(self.grid_shape)
        
        # Load ML Model
        self.ml_model = MLResidualModel() # Need to load weights IRL
        
    def ingest(self, payload: dict):
        """
        Ingest sensor data and update state.
        payload: {timestamp, radar_tile, gauges...}
        """
        # Parsing logic here
        # For prototype, just log
        print(f"Ingested data for {payload.get('timestamp_utc')}")
        return {"status": "ok", "items_processed": len(payload.get('gauges', []))}
        
    def predict(self):
        """
        Run full inference pipeline.
        """
        start_time = time.time()
        
        # 1. Get Dynamic Data (Simulated for now)
        # In real app, we'd fetch from self.latest_rain_grid
        coarse_rain = np.random.rand(50, 50) * 10.0 # Mock
        
        # 2. Downscale
        rain_fine = downscale_rainfall(coarse_rain, self.dem, coarse_res=1000, fine_res=10)
        
        # 3. Fuse
        fused_rain = self.fusion_engine.update(rain_fine, 'satellite')
        
        # 4. Physical Model
        fos_grid = compute_fos_grid(self.dem, self.soil_params, self.initial_saturation, np.mean(fused_rain))
        
        # 5. ML Correction
        # Construct features for ML
        # Flatten for tabular prediction
        # Limit to potentially unstable cells to save compute
        mask = fos_grid < 1.5
        indices = np.where(mask)
        
        if len(indices[0]) > 0:
            # Create feature DF (mock)
            features = pd.DataFrame({
                'fos': fos_grid[mask],
                'rain_1d': fused_rain[mask] * 24, # Mock accum
                'slope': np.random.rand(len(indices[0])) * 30,
                'curvature': np.zeros(len(indices[0])),
                'soil_moisture': self.initial_saturation[mask],
                'landcover': np.ones(len(indices[0]))
            })
            
            # Add missing cols for shape match
            for col in ['rain_3d']: 
                features[col] = 0.0
                
            # predict residuals (if model loaded)
            try:
                # residuals = self.ml_model.predict(features)
                # corrected_fos = fos_grid[mask] + residuals
                pass
            except:
                pass
                
        # 6. Generate Risk Map
        # Risk = 1 / FoS (Simple proxy)
        risk_map = 1.0 / (fos_grid + 0.1)
        risk_map = np.clip(risk_map, 0.0, 1.0)
        
        # 7. Identify Hotspots
        hotspots = []
        flat_risk = risk_map.flatten()
        top_k_idx = np.argsort(flat_risk)[-10:]
        
        for idx in top_k_idx:
            r, c = np.unravel_index(idx, self.grid_shape)
            hotspots.append({
                "cell_id": f"r{r}c{c}",
                "lat": 27.0 + r*0.0001,
                "lon": 80.0 + c*0.0001,
                "risk": float(risk_map[r,c]),
                "confidence": 0.8
            })
            
        latency = time.time() - start_time
        
        return {
            "run_id": "test_run",
            "timestamp_utc": datetime.utcnow().isoformat(),
            "latency_sec": latency,
            "top_hotspots": hotspots,
            "summary": {
                "max_risk": float(np.max(risk_map)),
                "num_high_risk": int(np.sum(risk_map > 0.8))
            }
        }
