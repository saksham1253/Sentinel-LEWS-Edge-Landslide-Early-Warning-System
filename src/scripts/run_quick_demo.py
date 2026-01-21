import sys
import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add src to path
# Assuming script is in src/scripts/
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.append(src_dir)

from ingestion.loader import load_shimla_data
from preprocess.soil_props import estimate_soil_parameters
from models.fisical_fos import compute_fos_vectorized
from models.ml_residual import MLResidual
import config

def fos_to_risk(fos):
    """
    Conservative risk mapping:
    FoS < 0.9 → High risk
    FoS ~1.0 → Medium
    FoS >1.2 → Safe
    """
    return 1.0 / (1.0 + np.exp(10.0 * (fos - 1.0)))

def generate_sms(lat: float, lon: float, risk: float, fos: float) -> str:
    """
    Generate <160 char SMS alert.
    """
    # Example: ALERT: High Landslide Risk (0.85). loc:31.12,77.15 FoS:0.9. Evacuate.
    return f"ALERT: High Landslide Risk ({risk:.2f}). Loc:{lat:.4f},{lon:.4f} FoS:{fos:.2f}. AC:Immediate"

def main():
    start_time = time.time()
    print("=== Sentinel-LEWS Edge Pipeline ===")
    
    # 1. Load Data
    # Assuming the csv is in the root or accessible. 
    # Try looking in standard paths
    csv_candidates = [
        "shimla_final_grid.csv",
        os.path.join(os.path.dirname(src_dir), "shimla_final_grid.csv"),
    ]
    csv_path = None
    for p in csv_candidates:
        if os.path.exists(p):
            csv_path = p
            break
            
    if not csv_path:
        # Fallback to absolute path from user context if possible, but let's try strict relative first.
        # If strict fails, we might mock or error.
        print(f"Error: Dataset not found. Searched: {csv_candidates}")
        return

    df = load_shimla_data(csv_path)
    
    # 2. Preprocess / Feature Engineering
    df = estimate_soil_parameters(df)
    
    print(f"Data Stats:")
    print(f"  Slope: Min {df['slope'].min():.1f}, Max {df['slope'].max():.1f}, Mean {df['slope'].mean():.1f}")
    print(f"  Elev:  Min {df['elevation'].min():.1f}, Max {df['elevation'].max():.1f}")
    print(f"  Clay:  Mean {df['clay'].mean():.2f}")
    
    # 3. Physics Model Inference
    # Map inputs
    soil_params = {
        'c': df['c'].values,
        'phi': df['phi'].values,
        'gamma': df['gamma'].values,
        'depth': df['depth'].values,
        'ksat': df['ksat'].values
    }
    
    # Use R_7d as rainfall proxy if available, or just a heavy rain scenario
    # User said R_7d is available.
    # Assuming R_7d is in mm.
    # We treat R_7d as the "event rainfall" or derive intensity.
    # Let's assume R_7d represents saturation, and we add a storm event on top?
    # Or just use R_7d as the input to the 'accumulated rain' logic.
    # The compute_fos_grid takes 'initial_saturation' and 'rainfall_intensity'.
    # We can approximate 'initial_saturation' from R_30d if available or just 0.5.
    # And use R_7d as the storm.
    
    # Simple approx:
    initial_sat = np.full(len(df), 0.5) # Default
    if 'R_30d' in df.columns:
        # Normalize R_30d to 0-1 saturation proxy? Max rain ~500mm?
        initial_sat = np.clip(df['R_30d'] / 500.0, 0.0, 0.9)
    
    # Rainfall intensity: Take R_7d and assume it fell over ... 7 days? 
    # Or is it "Rainfall last 7 days"?
    # The prompt says "time-series rainfall columns such as 2020-01-01...".
    # And "R_7d .. used as proxies for soil saturation".
    # Let's assume a hypothetical storm for prediction?
    # "Predict ... with at least 6-hour lead time."
    # Let's assume a 50mm/hr storm for 6 hours to see what breaks.
    # OR use R_7d magnitude as the stressor.
    # Let's use a fixed design storm for "Early Warning" of an incoming storm.
    # Design storm: 30mm/hr for 6 hours.
    
    # Extreme event stress test
    design_rain_mmph = 50.0
    design_duration_h = 12.0
    
    slope_deg = df['slope'].values
    
    fos_values = compute_fos_vectorized(
        slope_deg=df['slope'].values,
        elevation=df['elevation'].values,
        soil_params=soil_params,
        current_saturation=initial_sat,
        rainfall_intensity_mmph=design_rain_mmph,
        duration_hours=design_duration_h
    )

    # 4. ML Residual
    ml_model = MLResidual()
    # Features for ML: Lat, Lon, Elevation, Slope, R_7d
    ml_feats = df[['lat', 'lon', 'elevation', 'slope']].values
    if 'R_7d' in df.columns:
        r7 = df['R_7d'].values[:, None]
        ml_feats = np.hstack([ml_feats, r7])
        
    residual = ml_model.predict_residual(ml_feats)
    
    # 5. Risk Calculation
    # FoS_final = FoS_phys + Residual
    fos_final = fos_values + residual
    risk_probs = fos_to_risk(fos_final)
    
    df['fos'] = fos_final
    df['risk'] = risk_probs
    
    # 6. Top Hotspots
    # Filter risk > threshold
    threshold = getattr(config, 'RISK_THRESHOLD', 0.75)
    hotspots = df[df['risk'] > threshold].copy()
    
    # Sort by risk desc
    hotspots = hotspots.sort_values('risk', ascending=False).head(10)
    
    # 7. Generate Alerts
    alerts = []
    print("\n[HOTSPOTS DETECTED]")
    for idx, row in hotspots.iterrows():
        msg = generate_sms(row['lat'], row['lon'], row['risk'], row['fos'])
        alerts.append(msg)
        print(msg)
        
    if len(alerts) == 0:
        print(f"No hotspots found > {threshold} risk.")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n[METRICS]")
    print(f"Total time: {duration:.4f}s")
    print(f"Total points processed: {len(df)}")
    print(f"Peak Risk: {df['risk'].max():.4f}")
    print(f"Min FoS: {df['fos'].min():.4f}")
    
    if duration > 15.0:
        print("WARNING: Performance constraint violated (>15s)")
    else:
        print("SUCCESS: Performance constraint met (<15s)")

    # 8. Smoothed Heatmap of Risk (Grid + imshow)
    try:
        print("\n[HEATMAP] Generating smoothed 2D risk heatmap...")
        
        lat_min, lat_max = df['lat'].min(), df['lat'].max()
        lon_min, lon_max = df['lon'].min(), df['lon'].max()
        grid_size = 200  # 200x200 grid for smoothing

        lat_grid = np.linspace(lat_min, lat_max, grid_size)
        lon_grid = np.linspace(lon_min, lon_max, grid_size)

        # Empty grids
        risk_grid = np.zeros((grid_size, grid_size))
        count_grid = np.zeros((grid_size, grid_size))

        # Map each point to a grid cell
        lat_idx = np.searchsorted(lat_grid, df['lat'].values) - 1
        lon_idx = np.searchsorted(lon_grid, df['lon'].values) - 1
        lat_idx = np.clip(lat_idx, 0, grid_size-1)
        lon_idx = np.clip(lon_idx, 0, grid_size-1)

        # Aggregate risk
        for i, j, r in zip(lat_idx, lon_idx, df['risk'].values):
            risk_grid[i, j] += r
            count_grid[i, j] += 1

        # Avoid division by zero
        count_grid[count_grid == 0] = 1
        risk_grid /= count_grid

        # Plot
        plt.figure(figsize=(10, 6))
        plt.imshow(
            risk_grid,
            origin='lower',
            extent=[lon_min, lon_max, lat_min, lat_max],
            cmap='hot',
            vmin=0.0,
            vmax=1.0,
            aspect='auto'
        )
        plt.colorbar(label='Landslide Risk Probability')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title('Shimla Landslide Risk Heatmap')

        # Optional: Overlay top hotspots
        if not hotspots.empty:
            plt.scatter(hotspots['lon'], hotspots['lat'], color='blue', edgecolor='white', s=50, label='Top Hotspots')
            plt.legend()

        plt.tight_layout()
        plt.savefig('shimla_risk_heatmap.png', dpi=300)
        plt.show()
        
        print("Smoothed heatmap saved as shimla_risk_heatmap.png")
    except Exception as e:
        print(f"Failed to generate smoothed heatmap: {e}")


if __name__ == "__main__":
    main()

# import sys
# import os
# import time
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt

# # Path setup
# current_dir = os.path.dirname(os.path.abspath(__file__))
# src_dir = os.path.dirname(current_dir)
# sys.path.append(src_dir)

# from ingestion.loader import load_shimla_data
# from preprocess.soil_props import estimate_soil_parameters
# from models.fisical_fos import compute_fos_vectorized
# from models.ml_residual import MLResidual
# import config


# def fos_to_risk(fos: np.ndarray) -> np.ndarray:
#     """
#     Conservative FoS → Risk mapping.
#     """
#     return 1.0 / (1.0 + np.exp(10.0 * (fos - 1.0)))


# def generate_sms(lat, lon, risk, fos):
#     return (
#         f"ALERT: Landslide Risk {risk:.2f}. "
#         f"Loc:{lat:.4f},{lon:.4f} FoS:{fos:.2f}. Act Immediately."
#     )[:160]


# def main():
#     print("=== Sentinel-LEWS Edge Snapshot ===")
#     t0 = time.time()

#     csv_candidates = [
#         "shimla_final_grid.csv",
#         os.path.join(os.path.dirname(src_dir), "shimla_final_grid.csv"),
#     ]
#     csv_path = next((p for p in csv_candidates if os.path.exists(p)), None)
#     if not csv_path:
#         print("Dataset not found.")
#         return

#     df = load_shimla_data(csv_path)
#     df = estimate_soil_parameters(df)

#     soil_params = {
#         'c': df['c'].values,
#         'phi': df['phi'].values,
#         'gamma': df['gamma'].values,
#         'depth': df['depth'].values,
#         'ksat': df['ksat'].values,
#     }

#     slope_deg = df['slope'].values
#     elevation = df['elevation'].values

#     # --- Antecedent saturation proxy ---
#     if 'R_30d' in df.columns:
#         saturation = np.clip(df['R_30d'].values / 400.0, 0.1, 0.9)
#     else:
#         saturation = np.full(len(df), 0.3)

#     # --- Design storm ---
#     rain_mmph = 35.0
#     duration_h = 6.0

#     fos_phys = compute_fos_vectorized(
#         slope_deg=slope_deg,
#         elevation=elevation,
#         soil_params=soil_params,
#         current_saturation=saturation,
#         rainfall_intensity_mmph=rain_mmph,
#         duration_hours=duration_h
#     )

#     # --- ML residual ---
#     ml = MLResidual()
#     ml_feats = df[['lat', 'lon', 'elevation', 'slope']].values
#     residual = ml.predict_residual(ml_feats)

#     fos_final = fos_phys + residual
#     risk = fos_to_risk(fos_final)

#     df['fos'] = fos_final
#     df['risk'] = risk

#     threshold = getattr(config, "RISK_THRESHOLD", 0.85)
#     hotspots = df[(df['risk'] > threshold) & (df['fos'] < 1.0)]
#     hotspots = hotspots.sort_values('risk', ascending=False).head(10)

#     print("\n[HOTSPOTS]")
#     for _, r in hotspots.iterrows():
#         print(generate_sms(r['lat'], r['lon'], r['risk'], r['fos']))

#     print(f"\nProcessed {len(df)} cells in {time.time() - t0:.2f}s")
#     print(f"Peak Risk: {df['risk'].max():.3f}")
#     print(f"Min FoS: {df['fos'].min():.3f}")


# if __name__ == "__main__":
#     main()
