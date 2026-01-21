import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

class SensorHealthMonitor:
    def __init__(self, deviation_threshold=3.0):
        self.threshold = deviation_threshold
        
    def check_health(self, sensors_df: pd.DataFrame) -> pd.DataFrame:
        """
        Check sensor health using spatial consistency.
        
        Args:
            sensors_df: [id, lat, lon, value, status]
            
        Returns:
            sensors_df with updated 'status' (OK/SUSPECT/FAIL)
        """
        if len(sensors_df) < 3:
            return sensors_df # Not enough to vote
        
        coords = sensors_df[['lat', 'lon']].values
        values = sensors_df['value'].values
        
        # Distance matrix
        dists = cdist(coords, coords)
        np.fill_diagonal(dists, np.inf) # Ignore self
        
        statuses = sensors_df['status'].copy()
        
        for i in range(len(sensors_df)):
            if statuses.iloc[i] == 'FAIL':
                continue
                
            # Find 3 nearest neighbors
            nearest_idx = np.argsort(dists[i])[:3]
            neighbor_vals = values[nearest_idx]
            
            # Predict value (Spatial Median)
            prediction = np.median(neighbor_vals)
            
            # Check deviation
            # We use MAD (Median Absolute Deviation) of neighbors for scale
            mad = np.median(np.abs(neighbor_vals - prediction)) + 1e-6
            z_score = abs(values[i] - prediction) / mad
            
            if z_score > self.threshold:
                statuses.iloc[i] = 'SUSPECT'
                
        sensors_df['status'] = statuses
        return sensors_df
