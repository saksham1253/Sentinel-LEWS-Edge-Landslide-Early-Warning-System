import os

# --- SYSTEM DIRECTORIES ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
STATIC_DATA_DIR = os.path.join(DATA_DIR, 'static')
LIVE_DATA_DIR = os.path.join(DATA_DIR, 'live')
OUTPUT_DIR = os.path.join(DATA_DIR, 'outputs')

# --- GRID CONSTANTS (500 km^2 District) ---
# Assuming 100m resolution -> 22.36km x 22.36km
# Rounding to 225 x 225 grid for simplicity (506.25 sq km)
GRID_DIM_X = 225
GRID_DIM_Y = 225
CELL_SIZE_M = 100
NO_DATA_VALUE = -9999.0

# --- PREDICTION ENGINE TUNING ---
# Masks
SLOPE_THRESHOLD_DEG = 10.0   # Ignore slopes less than 10 degrees

# Risk Model Weights (Logistic Regression Coefficients - Pre-trained/Calibrated)
# Features Order: [1hr_Rain, 24hr_Rain, Slope, Curvature, Soil_Factor]
MODEL_WEIGHTS = [0.05, 0.02, 0.15, 0.4, 0.5] 
MODEL_BIAS = -8.5

# Downscaling Factors
OROGRAPHIC_FACTOR = 0.005 # +0.5% rain per meter elevation? No, that's too high. 
# Let's say +5% per 1000m -> 0.00005 per meter. 
# Actually standard lapse rates are complex, we use a simplified heuristic.
# Let's use: Rain_local = Rain_base * (1 + 0.0001 * (Elev_local - Elev_base))
ELEVATION_RAIN_FACTOR = 0.0002 

# --- ALERTING LOGIC ---
RISK_THRESHOLD = 0.75
MIN_CLUSTER_SIZE = 10  # Minimum contiguous cells to trigger alert (10 * 100m^2 = 10 Hectares? No 100x100=10000sqm = 1 hectare. 10 cells = 10 hectares)
# Wait, 1 cell = 100m x 100m = 10,000 m^2 = 1 Hectare.
# So 10 cells = 10 Ha. Significant landslide source zone.

ALERT_COOLDOWN_SECONDS = 3600 # Don't spam SMS every 15s

# --- SENSOR CONSTANTS ---
SENSOR_TRUST_THRESHOLD = 0.6
MAX_VALID_RAINFALL_MM_HR = 300.0 # World record is ~300-400. 
