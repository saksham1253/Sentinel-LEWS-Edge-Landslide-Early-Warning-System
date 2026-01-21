# System Design: Sentinel-LEWS

## 1. Physics Model
We use an Infinite Slope Model coupled with a simplified Green-Ampt infiltration scheme.
 Equation:
 $$ FoS = \frac{c + (\gamma z \cos^2 \alpha - u) \tan \phi}{\gamma z \sin \alpha \cos \alpha} $$

## 2. Sensor Fusion
Kalman Filter (Scalar) applied per-cell.
State: Rain Intensity.
Meas: Satellite (IMERG/GPM), Radar, Gauges.

## 3. Architecture
Edge-native design.
- Ingestion: Polling every 15 min.
- Processing: <15s for 500km2.
- Alert: SMS via GSM modem (simulated).
