import numpy as np
from ..config import *

class RainfallDownscaler:
    def __init__(self, elevation_grid):
        """
        elevation_grid: (Y, X) numpy array of elevation in meters
        """
        self.elevation = elevation_grid
        # Create coordinate grids
        rows, cols = elevation_grid.shape
        self.y_coords, self.x_coords = np.mgrid[0:rows, 0:cols]
        # In real life, convert to meters. We assume 1 unit = CELL_SIZE_M
        self.y_coords = self.y_coords * CELL_SIZE_M
        self.x_coords = self.x_coords * CELL_SIZE_M

    def compute_rainfall_grid(self, sensor_list, default_rain=0.0):
        """
        sensor_list: list of {'x': m, 'y': m, 'val': mm} (Already projected to local grid metric coords)
        """
        if not sensor_list:
            return np.full(self.elevation.shape, default_rain)

        # Vectorized IDW
        weights_sum = np.zeros(self.elevation.shape)
        weighted_val_sum = np.zeros(self.elevation.shape)
        
        # Mean elevation of input sensors (for orographic baseline)
        sensor_elevations = []

        for sensor in sensor_list:
            sx, sy, val = sensor['x'], sensor['y'], sensor['val']
            
            # Distance squared (avoid sqrt for speed)
            dist_sq = (self.x_coords - sx)**2 + (self.y_coords - sy)**2
            
            # Avoid division by zero (if grid center is exactly on sensor)
            dist_sq[dist_sq < 1] = 1.0 
            
            w = 1.0 / dist_sq
            
            weights_sum += w
            weighted_val_sum += (w * val)
            
            # Approximate sensor elevation from grid (nearest neighbor)
            # Map metric x,y back to indices
            ix = int(np.clip(sx / CELL_SIZE_M, 0, GRID_DIM_X-1))
            iy = int(np.clip(sy / CELL_SIZE_M, 0, GRID_DIM_Y-1))
            sensor_elevations.append(self.elevation[iy, ix])

        # Base interpolated rainfall
        base_rain = weighted_val_sum / weights_sum
        
        # Orographic Correction
        # Valid only if we have sensor elevation context
        if sensor_elevations:
            avg_sens_elev = np.mean(sensor_elevations)
            # Delta Elevation
            delta_elev = self.elevation - avg_sens_elev
            # Factor: e.g. 1.0 + (0.0002 * 500m) = 1.1x rain at 500m above sensor
            oro_factor = 1.0 + (ELEVATION_RAIN_FACTOR * delta_elev)
            # Clip to be reasonable (0.5x to 2.0x) - prevent exploding rain on peaks
            oro_factor = np.clip(oro_factor, 0.5, 2.5) 
            
            final_rain = base_rain * oro_factor
        else:
            final_rain = base_rain

        return np.maximum(final_rain, 0) # No negative rain
