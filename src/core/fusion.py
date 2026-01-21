import numpy as np
from typing import List, Dict, Tuple

class SensorFusionEngine:
    """
    Lightweight Sensor Fusion and Anomaly Detection for Edge Deployment.
    Fuses sparse ground station data with gridded satellite/model rainfall.
    """
    
    def __init__(self, elevation_grid: np.ndarray = None):
        self.elevation = elevation_grid
        self.trust_scores = {} # sensor_id -> score (0.0 to 1.0)
        
    def filter_anomalies(self, stations: List[Dict]) -> List[Dict]:
        """
        Detect and remove faulty sensor readings.
        Rules:
        1. Range check (0mm to 500mm/hr)
        2. Stuck check (requires history, simplified here)
        3. Statistical outlier (Z-score if enough sensors)
        """
        valid = []
        values = [s['val'] for s in stations]
        
        if not values:
            return []
            
        # Median filter for gross outliers
        median_val = np.median(values)
        mad = np.median(np.abs(np.array(values) - median_val)) # Median Absolute Deviation
        
        threshold = 3.0 * mad if mad > 0 else 50.0 # Fallback threshold if all uniform
        
        for s in stations:
            val = s['val']
            
            # Rule 1: Physcial Limits
            if not (0.0 <= val <= 500.0):
                print(f"[FUSION] Dropping sensor {s['id']}: Value {val} out of bounds.")
                continue
                
            # Rule 2: Outlier detection (skip if too few sensors)
            if len(stations) > 4:
                if abs(val - median_val) > threshold and val > 10.0:
                    print(f"[FUSION] Dropping sensor {s['id']}: Statistical outlier ({val} vs med {median_val})")
                    continue
            
            valid.append(s)
            
        return valid

    def fuse_rainfall_idw(self, 
                          base_grid: np.ndarray, 
                          stations: List[Dict], 
                          lat_grid: np.ndarray, 
                          lon_grid: np.ndarray,
                          power: float = 2.0) -> np.ndarray:
        """
        Fuse ground stations into base grid using Inverse Distance Weighting (IDW).
        Correction = IDW(Station_Val - Base_Val_at_Station)
        Final = Base + Correction
        
        Args:
            base_grid: Background rainfall grid (e.g. satellite/forecast)
            stations: List of dicts {'lat':f, 'lon':f, 'val':f}
            lat_grid, lon_grid: Meshgrid of coordinates
        """
        if not stations:
            return base_grid
            
        # 1. Calculate residuals at station points
        # For this demo, we assume base_grid is flat or stations provide the 'truth'
        # We'll create an adjustment surface.
        
        adjustment_surface = np.zeros_like(base_grid)
        total_weights = np.zeros_like(base_grid)
        
        # Optimization: Don't compute full N*M distance matrix for every station if grid is huge.
        # But for 500km^2 (approx 500x500 grid maybe?), it's manageable on edge if optimized.
        # Let's use a simplified approach: broadcast subtraction
        
        # To keep it fast (<1s), we might downsample for the weight calc then upscale?
        # Or just loop stations (usually < 20)
        
        for s in stations:
            d_lat = lat_grid - s['lat']
            d_lon = lon_grid - s['lon']
            # Euclidean distance approx (deg)
            dist_sq = d_lat**2 + d_lon**2
            dist_sq = np.maximum(dist_sq, 1e-10) # Avoid div0
            
            weights = 1.0 / (dist_sq ** (power / 2.0))
            
            # Here we assume the station overrides the local value.
            # Correction field
            # We want Final = IDW(Station) ??
            # Usually: Fused = Alpha * Satellite + (1-Alpha) * IDW(Ground)
            # Or Residual Kriging.
            
            # Let's do simple Residual IDW.
            # Residual R_s = Station_Obs - Base_Grid_Value_Nearest
            # But calculating Nearest for every station is tricky without KDTree.
            # Let's assume the 'base_grid' is uniform or low-res pattern, and we just want to
            # Interpolate station values and blend?
            
            # Hackathon Strategy:
            # Create a "Station Grid" using IDW.
            # Blend with Base Grid.
            
            adjustment_surface += s['val'] * weights
            total_weights += weights
            
        # IDW Interpolated Rainfall
        station_grid = adjustment_surface / total_weights
        
        # Blending: High confidence in stations near stations, lower far away?
        # For EWS, ground stations are Gold Standard.
        # Let's use the station_grid widely, but fallback to base_grid where weights are low?
        # Simpler: Just return station_grid (assuming adequate coverage) or 
        # Mean(Station, Base).
        
        # Let's return weighted average
        # If total_weight is high, trust station.
        # normalized distance metric?
        
        # For this prototype: Return IDW of stations (assuming we have stations).
        # If no stations, return base.
        
        return station_grid
