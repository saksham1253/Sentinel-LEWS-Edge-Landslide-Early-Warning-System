import numpy as np
import pandas as pd

def estimate_soil_parameters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estimate geotechnical parameters from soil texture and bulk density.
    
    Args:
        df: DataFrame containing 'clay', 'sand', 'silt', 'bulk'.
        
    Returns:
        DataFrame with added columns: 'cohesion', 'phi', 'unit_weight', 'soil_depth', 'ksat'.
    """
    print("[PREPROCESS] Estimating soil parameters...")
    
    # 1. Unit Weight (gamma) in kN/m^3
    # Assumption: 'bulk' is typically in deca-kg/m3 or arbitrary units in this dataset.
    # If 135 -> 1.35 g/cm3 -> 13.5 kN/m3.
    # We want kN/m3 directly.
    # 135 * 0.1 = 13.5 kN/m3. (approx 1350 kg/m3 * 9.81 / 1000)
    gamma_knm3 = df['bulk'] * 0.1 
    
    # 2. Soil Depth (z) in meters
    # Heuristic: Steeper slopes have thinner soil.
    slope_rad = np.radians(df['slope'])
    # Range 1.0m to 4.0m
    soil_depth = 4.0 * np.exp(-0.02 * df['slope']) 
    soil_depth = np.clip(soil_depth, 1.0, 5.0)
    
    # 3. Cohesion (c) and Internal Friction Angle (phi)
    # Clay: High C (~20-40 kPa), Low Phi
    # Sand: Low C (~0-2 kPa), High Phi
    
    total = df['clay'] + df['sand'] + df['silt']
    clay_frac = df['clay'] / total
    sand_frac = df['sand'] / total
    silt_frac = df['silt'] / total
    
    # Cohesion (kPa) - OUTPUT IN kPa for the model
    # Conservatism: reduce standard values by 50%
    c_kpa = (20.0 * clay_frac) + (5.0 * silt_frac) + (1.0 * sand_frac)
    
    # Friction (Deg)
    phi = (20.0 * clay_frac) + (28.0 * silt_frac) + (35.0 * sand_frac)
    
    # 4. Ksat (m/s)
    # logK = a*clay + b*silt + c*sand
    log_k = (-7.0 * clay_frac) + (-6.0 * silt_frac) + (-4.0 * sand_frac)
    ksat = np.power(10.0, log_k)
    
    # Append to DF
    df['gamma'] = gamma_knm3
    df['depth'] = soil_depth
    df['c'] = c_kpa # Storing as kPa
    df['phi'] = phi
    df['ksat'] = ksat
    
    return df
