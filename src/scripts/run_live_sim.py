import sys
import os
import time
import json
import random
import numpy as np
import pandas as pd

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.append(src_dir)

from ingestion.loader import load_shimla_data
from preprocess.soil_props import estimate_soil_parameters
# from models.fisical_fos import compute_fos_grid # Removed, using vectorized locally
from core.fusion import SensorFusionEngine
import config

def run_live_loop():
    print("=== Sentinel-LEWS LIVE SIMULATION ===")
    print("Mode: Rolling 6-Hour Forecast (10m x 10m)")
    print("Status: OFFLINE MODE (Edge Local)")
    print("Press Ctrl+C to stop.\n")
    
    # Init
    csv_candidates = ["shimla_final_grid.csv", "../shimla_final_grid.csv"]
    csv_path = None
    for p in csv_candidates:
        if os.path.exists(p): csv_path = p; break
        
    if not csv_path: print("Data missing."); return

    df = load_shimla_data(csv_path)
    df = estimate_soil_parameters(df)
    
    fusion_engine = SensorFusionEngine()
    
    # Pre-compute static arrays for speed
    slope_deg = df['slope'].values
    elevation = df['elevation'].values
    lat_arr = df['lat'].values
    lon_arr = df['lon'].values
    
    soil_params = {
        'c': df['c'].values,
        'phi': df['phi'].values,
        'gamma': df['gamma'].values,
        'depth': df['depth'].values,
        'ksat': df['ksat'].values
    }
    
    # === MEMORY STATE ===
    # Initial Saturation: 20% default
    current_saturation = np.full(len(df), 0.2, dtype=np.float32)
    
    # Mock Stations (lat, lon)
    stations = [
        {'id': 'S1', 'lat': 31.1, 'lon': 77.1},
        {'id': 'S2', 'lat': 31.2, 'lon': 77.2},
        {'id': 'S3', 'lat': 31.05, 'lon': 77.15},
    ]
    
    cycle_count = 0
    decay_rate = 0.98 # Saturation decays 2% per cycle (approx 10-15 mins real time assumption?)
    
    while True:
        cycle_count += 1
        print(f"\n[CYCLE #{cycle_count}] Fetching Sensor Data...")
        t0 = time.time()
        
        # 1. Simulate Live Sensors (Random Storm Logic)
        # Randomly fluctuate intensity to simulate passing storm
        base_intensity = 10.0 + 40.0 * np.sin(cycle_count * 0.5) # Oscillate 0-50
        base_intensity = max(0.0, base_intensity)
        
        current_readings = []
        for s in stations:
            # Add noise
            val = base_intensity + random.uniform(-5, 5)
            # Occasional fault
            if random.random() < 0.1: val = 9999.0 # Spike
            
            current_readings.append({
                'id': s['id'], 'lat': s['lat'], 'lon': s['lon'], 'val': max(0.0, val)
            })
            
        # 2. Fuse & Filter
        clean_sensors = fusion_engine.filter_anomalies(current_readings)
        print(f"  Raw: {len(current_readings)} -> Clean: {len(clean_sensors)}")
        
        if clean_sensors:
            max_rain = max(s['val'] for s in clean_sensors)
        else:
            max_rain = 0.0
            
        print(f"  Driving Rainfall Intensity: {max_rain:.1f} mm/hr")
        
        # 3. Update Saturation (Memory)
        # Saturation increases with rain.
        # Simple bucket model: dS/dt = (Infiltration - Drainage) / (Porosity * Depth)
        # Hackathon approx: 
        # Add pro-rated rain: (mm/hr / 6 cycles_per_hr?) -> Let's assume 1 cycle = 1 hour for demo speed?
        # Or more realistic: 1 cycle = step.
        # increase = Rain(mm) / 1000 / (Porosity * Depth)
        # We model "Effective Rain Accumulation".
        
        # Accumulate: +0.05 saturation per 10mm of rain?
        # Let's say max_rain falls for "1 hour" equivalent in this step
        added_sat = (max_rain / 100.0) * 0.1 # 100mm -> +0.1 sat? Rough.
        
        current_saturation = current_saturation * decay_rate + added_sat
        current_saturation = np.clip(current_saturation, 0.1, 1.0)
        
        avg_sat = np.mean(current_saturation)
        print(f"  Soil Saturation (Avg): {avg_sat*100:.1f}%")
        
        # 4. Predict
        # Using vectorized model
        from models.fisical_fos import compute_fos_vectorized
        
        fos_values = compute_fos_vectorized(
            slope_deg=df['slope'].values,
            elevation=df['elevation'].values,
            soil_params=soil_params,
            current_saturation=current_saturation,
            rainfall_intensity_mmph=max_rain,
            duration_hours=6.0
        )

        
        # 5. Assessment & Alerting
        # New logic: 
        # FoS < 0.9 -> High (Probability > 80%)
        # FoS 0.9-1.1 -> Medium 
        # FoS > 1.2 -> Low
        
        # Sigmoid tuning: Center at 1.0, steepness 10
        # P = 1 / (1 + exp(10 * (FoS - 1.0)))
        risk = 1.0 / (1.0 + np.exp(10.0 * (fos_values - 1.0)))
        critical_count = np.sum(fos_values < 1.0)

        t_end = time.time()
        
        print(f"  Risk Assessment Complete in {t_end - t0:.3f}s")
        print(f"  Critical Cells (FoS < 1.0): {critical_count}")
        
        if critical_count > 100:
            print(f"  [!!!] SMS ALERT: {critical_count} zones unstable! Rain: {max_rain:.1f}mm/hr")
            
        # Sleep for demo pace
        time.sleep(1.0)

if __name__ == "__main__":
    try:
        run_live_loop()
    except KeyboardInterrupt:
        print("Stopped.")

# import sys
# import os
# import time
# import random
# import numpy as np

# current_dir = os.path.dirname(os.path.abspath(__file__))
# src_dir = os.path.dirname(current_dir)
# sys.path.append(src_dir)

# from ingestion.loader import load_shimla_data
# from preprocess.soil_props import estimate_soil_parameters
# from models.fisical_fos import compute_fos_vectorized
# from core.fusion import SensorFusionEngine


# def run_live_loop():
#     print("=== Sentinel-LEWS LIVE SIMULATION ===")

#     df = load_shimla_data("shimla_final_grid.csv")
#     df = estimate_soil_parameters(df)

#     slope = df['slope'].values
#     elevation = df['elevation'].values

#     soil_params = {
#         'c': df['c'].values,
#         'phi': df['phi'].values,
#         'gamma': df['gamma'].values,
#         'depth': df['depth'].values,
#         'ksat': df['ksat'].values,
#     }

#     saturation = np.full(len(df), 0.2)
#     decay = 0.98

#     fusion = SensorFusionEngine()
#     cycle = 0

#     while True:
#         cycle += 1
#         rain = max(0.0, 25.0 + 25.0 * np.sin(cycle * 0.4))
#         rain += random.uniform(-5, 5)
#         rain = max(rain, 0.0)

#         added_sat = (rain / 100.0) * 0.1
#         saturation = saturation * decay + added_sat
#         saturation = np.clip(saturation, 0.1, 1.0)

#         fos = compute_fos_vectorized(
#             slope_deg=slope,
#             elevation=elevation,
#             soil_params=soil_params,
#             current_saturation=saturation,
#             rainfall_intensity_mmph=rain,
#             duration_hours=6.0
#         )

#         risk = 1.0 / (1.0 + np.exp(10.0 * (fos - 1.0)))
#         critical = np.sum((risk > 0.85) & (fos < 1.0))

#         print(f"[Cycle {cycle}] Rain={rain:.1f} mm/h | Critical={critical}")

#         if critical > 200 and rain > 20:
#             print("🚨 SMS ALERT: Significant slope instability detected!")

#         time.sleep(1)


# if __name__ == "__main__":
#     try:
#         run_live_loop()
#     except KeyboardInterrupt:
#         print("Simulation stopped.")
