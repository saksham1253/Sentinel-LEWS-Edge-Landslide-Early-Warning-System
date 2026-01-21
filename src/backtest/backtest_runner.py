import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta
from src.inference.runner import InferenceRunner
from src.backtest.metrics import calculate_lead_time

def run_backtest(rainfall_csv, events_csv, region_id):
    print(f"Running backtest for {region_id}...")
    
    # Load Data
    rain_df = pd.read_csv(rainfall_csv)
    # Ensure sorted by time
    rain_df['timestamp_utc'] = pd.to_datetime(rain_df['timestamp_utc'])
    rain_df = rain_df.sort_values('timestamp_utc')
    
    events_df = pd.read_csv(events_csv)
    events_df['timestamp_utc'] = pd.to_datetime(events_df['timestamp_utc'])
    
    runner = InferenceRunner()
    
    alerts_log = []
    
    # Simulation Loop
    for idx, row in rain_df.iterrows():
        current_time = row['timestamp_utc']
        
        # 1. Ingest (Mocking payload construction)
        payload = {
            "timestamp_utc": current_time.isoformat(),
            "gauges": [], # populate from row if available
            "region_id": region_id
        }
        runner.ingest(payload)
        
        # 2. Predict
        result = runner.predict()
        
        # 3. Check for alerts
        top_hotspots = result.get('top_hotspots', [])
        for hotspot in top_hotspots:
            if hotspot['risk'] > 0.8:
                alerts_log.append({
                    "time": current_time,
                    "lat": hotspot['lat'],
                    "lon": hotspot['lon'],
                    "risk": hotspot['risk']
                })
        
        # Progress indication
        if idx % 10 == 0:
            print(f"Processed {current_time}")

    # Evaluate against Events
    total_lead_time = 0
    detected_events = 0
    
    for _, event in events_df.iterrows():
        event_time = event['timestamp_utc']
        event_loc = (event['lat'], event['lon'])
        
        # Find matching alerts within distance and time window (say 24h prior)
        relevant_alerts = []
        for alert in alerts_log:
            dt = (event_time - alert['time']).total_seconds() / 3600.0
            if 0 < dt < 24: # Alert was before event
                # Check distance (simplified)
                dist = np.sqrt((alert['lat'] - event_loc[0])**2 + (alert['lon'] - event_loc[1])**2)
                if dist < 0.01: # approx 1km
                    relevant_alerts.append(alert['time'])
        
        if relevant_alerts:
            lead = calculate_lead_time(relevant_alerts, event_time)
            print(f"Event at {event_time} detected! Lead time: {lead:.2f} hours")
            if lead >= 4.0:
                 print("SUCCESS: Met acceptance validation (>4h).")
            total_lead_time += lead
            detected_events += 1
        else:
            print(f"Event at {event_time} MISSED.")
            
    print(f"Backtest Complete. Detected {detected_events}/{len(events_df)} events.")

if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--rainfall", required=True)
    # ...
    # args = parser.parse_args()
    pass
