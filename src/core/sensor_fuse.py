import numpy as np
import math
from ..config import *

class SensorFusion:
    def __init__(self):
        self.sensor_history = {} # Keep small history for drift detection

    def validate_sensors(self, raw_sensor_data):
        """
        Input: List of dicts [{'id': 's1', 'val': 12.5, 'ts': ...}, ...]
        Output: List of dicts (only valid ones)
        """
        valid_sensors = []
        values = [s['val'] for s in raw_sensor_data if s['val'] is not None]
        
        if not values:
            return []

        # 1. Global Bounds Check
        clean_pass_1 = []
        for s in raw_sensor_data:
            val = s.get('val', -999)
            if val is None: continue
            if val < 0 or val > MAX_VALID_RAINFALL_MM_HR:
                continue # Physical impossibility
            clean_pass_1.append(s)

        if not clean_pass_1:
            return []

        # 2. Z-Score Filter (Statistical Outlier) 
        # Only apply if we have enough sensors (>5) to be statistically significant
        # Otherwise risk removing the ONLY sensor detecting a cloudburst
        final_pass = clean_pass_1
        
        if len(clean_pass_1) > 5:
            vals = np.array([s['val'] for s in clean_pass_1])
            median = np.median(vals)
            mad = np.median(np.abs(vals - median)) # Median Absolute Deviation (Robust)
            
            # Modified Z-score: 0.6745 * (x - median) / MAD
            # If MAD is 0 (all sensors same), we skip this check
            if mad > 0:
                final_pass = []
                for s in clean_pass_1:
                    mod_z = 0.6745 * (s['val'] - median) / mad
                    if abs(mod_z) > 3.5:
                        # Outlier
                        continue 
                    final_pass.append(s)

        return final_pass

    def get_interpolated_rain_value(self, valid_sensors, grid_x, grid_y):
        # This function is deprecated in favor of the vectorized Downscaler
        pass
