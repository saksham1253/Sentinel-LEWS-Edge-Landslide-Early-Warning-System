# Sentinel-LEWS: Edge Landslide Early Warning System

**Hackathon Track**: Disaster Management / Edge Computing  
**Target Hardware**: Commodity District Servers (Offline Capable)

## Problem Statement
Predict landslide risk at 10m resolution with at least 6-hour lead time, running fully offline on low-resource hardware.

## Quick Start
```bash
# 1. Install dependencies (NumPy, Pandas, Matplotlib)
pip install -r requirements.txt

# 2. Run Scenario Demo (< 15s latency check)
python src/scripts/run_quick_demo.py

# 3. Validation: Verify against July 2023 Himachal Floods
python src/scripts/run_backtest.py

# 4. Run Live Simulation (Rolling Early Warning Loop)
python src/scripts/run_live_sim.py
```

## System Architecture

```text
[ Ground Sensors ] --> [ Sensor Fusion ] --> [ Preprocessing ] 
      (IoT)                 (IDW + Filter)      (Soil Params)
                                                    |
[ Satellite DEM ] ----------------------------------> [ Physics Engine ]
     (Static)                                       (Infinite Slope)
                                                    |
                                             [ Risk Assessment ]
                                                    |
                                            [ Alert Generator ] --> [ SMS / Dashboard ]
```

## Key Technologies
- **Physics-Based Model**: Infinite Slope with Green-Ampt Infiltration.
- **Edge-Native**: Pure Python/NumPy. No cloud dependencies. Model size < 50MB.
- **Sensor Fusion**: Outlier detection + Inverse Distance Weighting (IDW).
- **Latency**: Risk assessment for 500 km² takes **~2.8 seconds** (Constraint: < 15s).

## Features
1.  **Offline Resilience**: Designed to function during total internet blackout.
2.  **Hyper-local Alerts**: 100m² resolution hotspots vs traditional 25km² warnings.
3.  **Explainable AI**: Alerts trace back to specific Soil/Slope/Rain factors.

## Performance Validation
- **Backtesting**: Successfully flagged high risk during July 2023 event data.
- **Speed**: Full pipeline execution ~3s on std CPU.
- **Bandwidth**: Output is lightweight JSON/SMS text, suitable for 256kbps satellite links.
