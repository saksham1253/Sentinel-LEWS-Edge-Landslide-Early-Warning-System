import numpy as np
from scipy.ndimage import label, sum_labels
from src.offline.sms_simulator import SMSSimulator

class AlertEngine:
    def __init__(self, config=None):
        self.config = config or {}
        self.primary_thresh = 0.8
        self.secondary_thresh = 0.6
        self.cluster_min_size = 10 # cells (1000 m2)
        self.sms_sender = SMSSimulator()
        
    def evaluate(self, risk_grid: np.ndarray, lat_grid: np.ndarray, lon_grid: np.ndarray, timestamp: str):
        """
        Evaluate risk grid and trigger alerts.
        """
        alerts = []
        
        # Rule 1: High Risk Cells
        high_risk_mask = risk_grid >= self.primary_thresh
        
        # Rule 2: Clustered Moderate Risk
        mod_risk_mask = risk_grid >= self.secondary_thresh
        labeled_array, num_features = label(mod_risk_mask)
        
        # Calculate size of each cluster
        # bincount returns count of 0 (background), 1, 2...
        counts = np.bincount(labeled_array.ravel())
        
        # Ignore background (0)
        counts[0] = 0
        
        valid_clusters = np.where(counts >= self.cluster_min_size)[0]
        
        triggered_mask = np.zeros_like(risk_grid, dtype=bool)
        
        # Process Clusters
        for cluster_id in valid_clusters:
            cluster_mask = (labeled_array == cluster_id)
            triggered_mask |= cluster_mask
            
            # Generate Alert for this cluster
            # Find centroid
            indices = np.where(cluster_mask)
            center_idx = (int(np.mean(indices[0])), int(np.mean(indices[1])))
            
            lat = lat_grid[center_idx]
            lon = lon_grid[center_idx]
            
            sector_id = f"SEC-{center_idx[0]//10}-{center_idx[1]//10}" # Simple Sector ID
            
            # Send SMS
            msg = self.sms_sender.generate_message(
                timestamp,
                sector_id,
                lat, lon,
                zones=[f"Z{center_idx[0]}"], # Mock Zone
                url_code="CODE" + str(cluster_id)
            )
            self.sms_sender.send_mock(msg)
            
            alerts.append({
                "type": "CLUSTER",
                "lat": lat,
                "lon": lon,
                "risk_avg": np.mean(risk_grid[cluster_mask]),
                "size": counts[cluster_id],
                "sms": msg
            })
            
        return alerts, triggered_mask
