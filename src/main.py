import time
import json
import os
import numpy as np
import datetime
from core.sensor_fuse import SensorFusion
from core.geofuncs import RainfallDownscaler
from core.risk_engine import RiskEngine
from core.alerts import AlertSystem
import config

class SentinelSupervisor:
    def __init__(self):
        print("[INIT] Booting Sentinel-LEWS Core...")
        
        # Load Static Data
        print("[INIT] Loading Terrain Data...")
        try:
            self.elevation = np.load(os.path.join(config.STATIC_DATA_DIR, 'elevation.npy'))
            self.slope = np.load(os.path.join(config.STATIC_DATA_DIR, 'slope.npy'))
            self.soil = np.load(os.path.join(config.STATIC_DATA_DIR, 'soil_stability.npy'))
        except FileNotFoundError:
            print("[ERROR] Static data missing! Run 'setup_mock_data.py' first.")
            exit(1)

        # Pre-compute Susceptibility Mask (Optimization)
        # 1 = Process, 0 = Ignore
        print("[INIT] Computing Static Susceptibility Mask...")
        self.static_mask = (self.slope >= config.SLOPE_THRESHOLD_DEG)
        print(f"[INIT] Mask active. Processing {np.sum(self.static_mask)} / {self.static_mask.size} voxels.")

        # Init Modules
        self.sensor_fusion = SensorFusion()
        self.downscaler = RainfallDownscaler(self.elevation)
        self.risk_engine = RiskEngine()
        self.alert_system = AlertSystem()

    def read_live_sensors(self):
        # In a real system, this reads from a serial port or JSON file stream
        # For this demo, we read a 'current_sensors.json' if it exists
        fpath = os.path.join(config.LIVE_DATA_DIR, 'sensors.json')
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def run_cycle(self):
        start_time = time.time()
        
        # 1. Ingest
        raw_sensors = self.read_live_sensors()
        valid_sensors = self.sensor_fusion.validate_sensors(raw_sensors)
        
        # 2. Downscale (Rainfall 1hr)
        # Note: In real system, we'd also track 24hr rain buffer. 
        # Here we assume sensor value X is the critical driver.
        rain_grid = self.downscaler.compute_rainfall_grid(valid_sensors)
        
        # 3. Create Feature Stack
        # [1hr, 24hr, Slope, Curvature(0), Soil]
        # Valid features must match model weights order
        
        # Mocking 24hr rain as 5x current rain for demo
        rain_24 = rain_grid * 5.0 
        curvature = np.zeros_like(self.slope) # Mock
        
        feature_stack = np.stack([
            rain_grid,
            rain_24,
            self.slope,
            curvature,
            self.soil
        ]) # Shape (5, Y, X)
        
        # 4. Inference
        risk_map = self.risk_engine.compute_risk(feature_stack, self.static_mask)
        max_risk = np.max(risk_map) if risk_map.size > 0 else 0.0
        
        # 5. Alert Logic
        alert_active, alert_msg = self.alert_system.check_alert_conditions(risk_map)
        
        # 6. Status Update
        latency = (time.time() - start_time) * 1000
        status = {
            "timestamp": datetime.datetime.now().isoformat(),
            "max_risk": float(max_risk),
            "active_sensors": len(valid_sensors),
            "sensor_trust_avg": 0.9, # Placeholder
            "alert_active": alert_active,
            "last_alert_msg": alert_msg,
            "compute_latency_ms": int(latency)
        }
        
        # Atomic Write
        with open(os.path.join(config.OUTPUT_DIR, 'system_status.json'), 'w') as f:
            json.dump(status, f)
            
        return status

def main():
    supervisor = SentinelSupervisor()
    print("[SYSTEM] Entered Operation Loop.")
    
    while True:
        try:
            status = supervisor.run_cycle()
            # print(f"[HEARTBEAT] Max Risk: {status['max_risk']:.3f} | Latency: {status['compute_latency_ms']}ms")
            # Sleep 2s
            time.sleep(2)
        except KeyboardInterrupt:
            print("Shutting down...")
            break
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
