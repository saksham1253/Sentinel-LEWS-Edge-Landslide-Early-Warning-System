# System Architecture

## 1. Data Flow
1.  **Ingestion**: `loader.py` reads static terrain grids (DEM, LULC, Soil Texture) and dynamic rainfall.
2.  **Fusion (Edge)**: `fusion.py` validates incoming sensor streams (if connected) and fuses them with satellite rainfall data using IDW.
3.  **Soil Physics**: `soil_props.py` converts raw texture (%) into geotechnical properties (Cohesion, Friction Angle, Ksat) using Pedotransfer functions.
4.  **Inference**: `fisical_fos.py` computes Factor of Safety (FoS) for every pixel (500k+ points).
    *   `FoS < 1.0` = Unstable
    *   `FoS < 1.3` = Critical
5.  **Risk Mapping**: Sigmoid conversion of FoS to probability [0,1].
6.  **Alerting**: Spatial clustering of high-risk pixels triggers SMS generation.

## 2. Offline Guarantees
- All static data (Elevation, Soil) is cached locally.
- The system operates in a "Run Loop" (`run_live_sim.py`) that does not check external APIs unless configured.
- Alerts are printed to stdout (simulating GSM modem buffer).

## 3. Sensor Fault Tolerance
- **Range Checks**: discards <0 or >500 mm/hr.
- **Median Filter**: rejects statistical outliers (e.g. stuck sensor).
- **Fallback**: Defaults to satellite/forecast grid if ground sensors fail.

## 4. Hardware Requirements
- CPU: Dual Core 2.0 GHz+
- RAM: 4 GB
- Storage: 100 MB (Code + Data cache)
- OS: Linux/Windows (Python 3.8+)
