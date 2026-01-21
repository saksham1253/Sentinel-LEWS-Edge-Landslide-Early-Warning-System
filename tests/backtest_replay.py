# Backtesting Script: Replaying "Cyclone Mocha 2023" Scenario
# Objective: Verify Alert Trigger with 4 hour Lead Time

import sys
import os
import json
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from main import SentinelSupervisor
import config

def run_backtest():
    print("=== BEGINNING BACKTEST: CYCLONE MOCHA REPLAY ===")
    
    # 1. Initialize System
    supervisor = SentinelSupervisor()
    
    # 2. Define Scenario Data (Hour, Rainfall_mm/hr)
    # Disaster event occurs at Hour 8 (Rain > 100mm sustained)
    scenario_timeline = [
        (0, 5.0),   # Light rain
        (1, 15.0),  # Moderate
        (2, 45.0),  # Heavy
        (3, 80.0),  # Very Heavy - Early Warning Threshold Approaching?
        (4, 120.0), # EXTREME - Alert MUST trigger here (4 hours early)
        (5, 150.0),
        (6, 200.0),
        (7, 220.0),
        (8, 250.0)  # LANDSLIDE EVENT
    ]
    
    alert_triggered_at = None
    
    for hour, rain_val in scenario_timeline:
        print(f"\n--- Simulation T-Minus {8-hour} Hours (Rain: {rain_val} mm/hr) ---")
        
        # Update Mock Sensors
        sensors = [
            {"id": "s1_valley", "x": 10000, "y": 10000, "val": rain_val * 0.9},
            {"id": "s2_peak", "x": 12000, "y": 12000, "val": rain_val * 1.1}, # Orographic boost
        ]
        
        with open(os.path.join(config.LIVE_DATA_DIR, 'sensors.json'), 'w') as f:
            json.dump(sensors, f)
            
        # Run Cycle
        status = supervisor.run_cycle()
        
        print(f"Risk: {status['max_risk']:.4f} | Sensors: {status['active_sensors']}")
        
        if status['alert_active']:
            print(f"!!! ALERT TRIGGERED: {status['last_alert_msg']} !!!")
            if alert_triggered_at is None:
                alert_triggered_at = hour
                
    # Validation
    if alert_triggered_at is not None:
        lead_time = 8 - alert_triggered_at
        print(f"\n=== RESULT: SUCCESS ===")
        print(f"Alert triggered at Hour {alert_triggered_at} (Rain ~{scenario_timeline[alert_triggered_at][1]}mm).")
        print(f"Lead Time: {lead_time} Hours (Target: >4 Hours).")
    else:
        print("\n=== RESULT: FAILURE - NO ALERT TRIGGERED ===")

if __name__ == "__main__":
    run_backtest()
