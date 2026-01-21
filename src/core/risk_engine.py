import numpy as np
from ..config import *

class RiskEngine:
    def __init__(self):
        # Features: [1hr_Rain, 24hr_Rain, Slope, Curvature, Soil_Factor]
        self.weights = np.array(MODEL_WEIGHTS)
        self.bias = MODEL_BIAS

    def compute_risk(self, feature_stack, slope_mask):
        """
        feature_stack: (5, Y, X) numpy array of features
        slope_mask: (Y, X) boolean array (True = Process, False = Safe)
        
        Returns: (Y, X) probability map
        """
        # Initialize output
        risk_map = np.zeros(slope_mask.shape, dtype=np.float32)
        
        # Flatten for processing (Vector operation) -> Only masked pixels
        # Taking "slope_mask" as the pixels TO process (High slope)
        valid_indices = np.where(slope_mask)
        
        if valid_indices[0].size == 0:
            return risk_map # Safe zone
        
        # Extract features for valid pixels
        # stack shape: (5, Y, X)
        # We need (N, 5) where N is number of valid pixels
        valid_features = feature_stack[:, valid_indices[0], valid_indices[1]].T 
        
        # Linear Combination (W*x + b)
        # (N, 5) dot (5,) -> (N,)
        logits = np.dot(valid_features, self.weights) + self.bias
        
        # Sigmoid Function
        probs = 1.0 / (1.0 + np.exp(-logits))
        
        # Map back to grid
        risk_map[valid_indices] = probs
        
        return risk_map
