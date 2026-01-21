import pytest
import numpy as np
from src.models.fisical_fos import compute_fos_grid

def test_fos_stable_slope():
    # Flat terrain, should be stable
    shape = (10, 10)
    dem = np.zeros(shape) # Flat
    soil_params = {
        'c': 5000.0,
        'phi': 30.0,
        'gamma': 20000.0,
        'depth': 2.0,
        'ksat': 1e-5
    }
    initial_sat = np.zeros(shape)
    rain_intensity = 0.0
    
    fos = compute_fos_grid(dem, soil_params, initial_sat, rain_intensity)
    
    # Flat ground FoS should be very high (we capped at 10.0)
    assert np.all(fos >= 9.9)

def test_fos_unstable_slope():
    # Steep slope (45 deg = 100% gradient), saturated
    shape = (10, 10)
    # Create slope: z = x
    # resolution 10m. to get 45 deg, dz/dx = 1.
    x = np.linspace(0, 90, 10)
    y = np.linspace(0, 90, 10)
    xv, yv = np.meshgrid(x, y)
    dem = xv # Slope along X axis
    
    soil_params = {
        'c': 0.0, # Cohesionless
        'phi': 30.0, # Friction 30 deg
        'gamma': 20000.0, # Unit weight
        'depth': 5.0,
        'ksat': 1e-4
    }
    # Fully saturated
    initial_sat = np.ones(shape)
    rain_intensity = 100.0 # Heavy rain
    
    fos = compute_fos_grid(dem, soil_params, initial_sat, rain_intensity)
    
    # Infinite slope, c=0, fully saturated parallel flow
    # FoS = (gamma' / gamma) * tan(phi) / tan(alpha)
    # gamma' ~ 10, gamma ~ 20 -> 0.5
    # tan(30) / tan(45) = 0.577 / 1 = 0.577
    # Total FoS approx 0.5 * 0.577 ~ 0.29 < 1.0 (Failure)
    
    # Check if FoS is low
    assert np.mean(fos) < 1.0
