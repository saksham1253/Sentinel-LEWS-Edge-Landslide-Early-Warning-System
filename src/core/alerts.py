import numpy as np
import datetime
from ..config import *

class AlertSystem:
    def __init__(self):
        self.last_alert_time = 0
        self.alert_outbox = []

    def check_alert_conditions(self, risk_map):
        """
        Check connectivity of high-risk voxels.
        Returns: (Alert_Bool, Message)
        """
        # Threshold
        high_risk_mask = (risk_map > RISK_THRESHOLD).astype(np.int32)
        
        if np.sum(high_risk_mask) < MIN_CLUSTER_SIZE:
            return False, ""

        # Find Connected Components (Pure Python/Numpy to avoid Scipy dependency for <50MB)
        # 1. Get coordinates of all high risk points
        # Structure: Set of (y, x)
        points = set(map(tuple, np.argwhere(high_risk_mask)))
        
        visited = set()
        max_cluster_size = 0
        num_clusters = 0
        
        # Simple BFS / Flood Fill
        for pt in points:
            if pt in visited:
                continue
            
            # Start new cluster
            num_clusters += 1
            current_cluster_size = 0
            stack = [pt]
            visited.add(pt)
            
            while stack:
                cy, cx = stack.pop()
                current_cluster_size += 1
                
                # Check 4-neighbors
                for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
                    ny, nx = cy+dy, cx+dx
                    if (ny, nx) in points and (ny, nx) not in visited:
                        visited.add((ny, nx))
                        stack.append((ny, nx))
            
            if current_cluster_size > max_cluster_size:
                max_cluster_size = current_cluster_size

        if max_cluster_size >= MIN_CLUSTER_SIZE:
            return self.trigger_alert(max_cluster_size)
        
        return False, ""

    def trigger_alert(self, cluster_size):
        now = datetime.datetime.now()
        # Cooldown check
        if (now.timestamp() - self.last_alert_time) < ALERT_COOLDOWN_SECONDS:
            return False, "COOLDOWN"

        self.last_alert_time = now.timestamp()
        
        # Format SMS
        # Estimate ward/area (Mocking a geocoder or simple grid mapping)
        # In real system, map Grid (X,Y) -> Ward Name via lookup layer
        time_str = (now + datetime.timedelta(hours=4)).strftime("%H:%M") # +4 hours lead
        
        msg = (f"ALERT: Landslide Risk HIGH. detected {cluster_size} connected danger zones. "
               f"Evacuate low-lying drains before {time_str} IST. "
               f"- District Control Room")
        
        # Enforce 160 chars
        msg = msg[:160]
        
        # Save to outbox
        self.alert_outbox.append({
            "ts": now.isoformat(),
            "msg": msg
        })
        
        # In a real system, this would write to a GSM Modem UART
        with open("sms_outbox_gateway.txt", "a") as f:
            f.write(f"[{now.isoformat()}] {msg}\n")
            
        return True, msg
