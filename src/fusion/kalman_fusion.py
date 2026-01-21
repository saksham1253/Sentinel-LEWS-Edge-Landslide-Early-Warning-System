import numpy as np

class KalmanFuser:
    def __init__(self, grid_shape):
        """
        Simple Vectorized Kalman Filter for Precipitation Fusion.
        State: [rain_intensity] (Scalar for speed, or could be [rain, rate])
        We will use a scalar state for maximum speed on edge.
        """
        self.rows, self.cols = grid_shape
        
        # State Estimate x (Initialize with 0)
        self.x = np.zeros(grid_shape)
        
        # Covariance P (Initialize with high uncertainty)
        self.P = np.ones(grid_shape) * 10.0
        
        # Process Noise Q (Model uncertainty)
        self.Q = 0.5 
        
        # Measurement Noise R (Sensor uncertainty)
        # Radar/Sat has higher noise than Gauges
        self.R_sat = 2.0
        self.R_gauge = 0.5
        
    def update(self, measurement_grid, source_type='satellite'):
        """
        Update state with new measurement grid.
        
        Args:
            measurement_grid: 2D numpy array (rain mm/h)
            source_type: 'satellite', 'radar', 'gauge' (interpolated)
        """
        # 1. Prediction Step (Time Update)
        # Assume persistence model x_k = x_{k-1}
        # In full model, could use physics forecast as control input
        x_pred = self.x 
        P_pred = self.P + self.Q
        
        # 2. Update Step (Measurement Update)
        R = self.R_sat if source_type in ['satellite', 'radar'] else self.R_gauge
        
        # Kalman Gain K = P / (P + R)
        K = P_pred / (P_pred + R)
        
        # Innovation y = z - x
        y = measurement_grid - x_pred
        
        # State Update
        self.x = x_pred + K * y
        
        # Covariance Update
        self.P = (1.0 - K) * P_pred
        
        return self.x
        
    def get_estimate(self):
        return self.x, self.P
