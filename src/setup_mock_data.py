import numpy as np
import os
import json
import config

def generate_mock_data():
    print(f"Generating synthetic terrain {config.GRID_DIM_X}x{config.GRID_DIM_Y}...")
    
    # 1. Elevation (Gaussian Hill in middle)
    x = np.linspace(-10, 10, config.GRID_DIM_X)
    y = np.linspace(-10, 10, config.GRID_DIM_Y)
    X, Y = np.meshgrid(x, y)
    
    # Base terrain: 500m + hill up to 2000m
    elevation = 500 + 1500 * np.exp(-(X**2 + Y**2)/20.0) 
    # Add noise
    elevation += np.random.normal(0, 10, elevation.shape)
    
    np.save(os.path.join(config.STATIC_DATA_DIR, 'elevation.npy'), elevation.astype(np.float32))
    
    # 2. Slope (Gradient)
    # Simple magnitude of gradient
    gy, gx = np.gradient(elevation, config.CELL_SIZE_M)
    slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
    slope_deg = np.degrees(slope_rad)
    
    np.save(os.path.join(config.STATIC_DATA_DIR, 'slope.npy'), slope_deg.astype(np.float32))
    
    # 3. Soil Stability (0.0=Unstable, 1.0=Solid Rock)
    # Random with spatial coherence
    soil = np.clip(np.random.normal(0.5, 0.2, elevation.shape), 0.1, 1.0)
    np.save(os.path.join(config.STATIC_DATA_DIR, 'soil_stability.npy'), soil.astype(np.float32))
    
    print("Static data generated.")

    # 4. Mock Sensors
    sensors = [
        {"id": "s1", "x": 5000, "y": 5000, "val": 0.0},
        {"id": "s2", "x": 10000, "y": 10000, "val": 10.0},
        {"id": "s3", "x": 15000, "y": 15000, "val": 5.0},
        # A broken sensor
        {"id": "s4", "x": 20000, "y": 20000, "val": -999.0} 
    ]
    
    with open(os.path.join(config.LIVE_DATA_DIR, 'sensors.json'), 'w') as f:
        json.dump(sensors, f)
        
    print("Mock sensor stream created.")

if __name__ == "__main__":
    generate_mock_data()
