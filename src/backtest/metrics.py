import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

def compute_metrics(y_true_grid, y_pred_grid):
    y_true = y_true_grid.flatten()
    y_pred = y_pred_grid.flatten()
    
    # Binary classification metrics
    y_pred_binary = (y_pred > 0.8).astype(int)
    
    return {
        "precision": precision_score(y_true, y_pred_binary, zero_division=0),
        "recall": recall_score(y_true, y_pred_binary, zero_division=0),
        "f1": f1_score(y_true, y_pred_binary, zero_division=0),
        "auc": roc_auc_score(y_true, y_pred) if len(np.unique(y_true)) > 1 else 0.5
    }

def calculate_lead_time(alert_times: list, event_time: str):
    """
    Calculate max lead time in hours.
    """
    if not alert_times:
        return 0.0
    
    event_dt = np.datetime64(event_time)
    earliest_alert = np.min([np.datetime64(t) for t in alert_times])
    
    lead_time = (event_dt - earliest_alert) / np.timedelta64(1, 'h')
    return max(0.0, lead_time)
