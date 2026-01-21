import numpy as np

def compute_fos_vectorized(
        slope_deg: np.ndarray,
        elevation: np.ndarray,
        soil_params: dict,
        current_saturation: np.ndarray,
        rainfall_intensity_mmph: float,
        duration_hours: float = 6.0
    ) -> np.ndarray:
    """
    Vectorized Infinite Slope Factor of Safety (FoS) Model.
    Designed for cell-wise tabular data (1D arrays).
    
    Units (Consistent kN-m-kPa system):
    - Cohesion: kPa (kN/m²)
    - Gamma: kN/m³
    - Depth: m
    - Stress: kPa
    
    Args:
        slope_deg: Slope in degrees (1D array).
        elevation: Elevation in meters (1D array).
        soil_params: Dict with 1D arrays or scalars:
            - 'c': Cohesion (kPa)
            - 'phi': Friction angle (degrees)
            - 'gamma': Unit weight (kN/m³)
            - 'depth': Soil depth (m)
            - 'ksat': Ksat (m/s)
        current_saturation: Saturation degree [0.0 - 1.0] (1D array).
        rainfall_intensity_mmph: Instantaneous rainfall intensity (mm/hr).
        duration_hours: Duration for Green-Ampt infiltration step.
        
    Returns:
        fos: 1D array of Factor of Safety.
    """
    # Constants
    GAMMA_W = 9.81  # Water unit weight (kN/m³)
    
    # 1. Geometry & Inputs
    # Clip slope to avoid invalid low angles (flat terrain is infinite stability, but we cap it)
    slope_rad = np.radians(np.clip(slope_deg, 0.1, 89.9))
    sin_a = np.sin(slope_rad)
    cos_a = np.cos(slope_rad)
    
    c = soil_params['c']       # kPa
    phi_deg = soil_params['phi']
    gamma = soil_params['gamma'] # kN/m³
    z = soil_params['depth']   # m
    ksat = soil_params['ksat'] # m/s
    
    tan_phi = np.tan(np.radians(phi_deg))
    
    # 2. Transient Infiltration (Green-Ampt Approximation)
    # Convert rain to m/s for comparison with Ksat
    # 1 mm/hr = 1e-3 / 3600 m/s
    rain_rate_ms = rainfall_intensity_mmph * 2.777e-7 
    duration_s = duration_hours * 3600.0
    
    # Infiltration rate is limited by Ksat (if surface is saturated) or Rain Rate
    # Simplified: If Rain > Ksat, we accumulate head? 
    # For FoS, we care about the Wetting Front Depth (Zw).
    # Zw approx = (Inf_Rate * Time) / porosity_proxy
    # We assume effective porosity (ne) ~ 0.3
    ne = 0.3
    
    # Vectorized Infiltration
    inf_rate = np.minimum(rain_rate_ms, ksat) if np.ndim(ksat) > 0 else min(rain_rate_ms, ksat)
    infiltration_depth_m = inf_rate * duration_s # Zw * ne
    
    # Rise in water table due to storm
    h_w_rise = infiltration_depth_m / ne
    
    # Existing water table (from antecedent saturation)
    h_w_initial = current_saturation * z
    
    # Total water height (h_w), clamped to soil depth (z)
    h_w = np.clip(h_w_initial + h_w_rise, 0.0, z)
    
    # 3. Infinite Slope Stresses (kPa)
    
    # Normal Stress (Total) sigma_n = gamma * z * cos^2(alpha)
    # Note: If soil is saturated, gamma should be gamma_sat. 
    # soil_params['gamma'] usually is bulk density. 
    # Let's adjust gamma weighted by saturation? 
    # For simplicitly in hackathon, we assume gamma provided is "bulk moist".
    # We add weight of water? 
    # gamma_eff = gamma + (saturation * porosity * GAMMA_W) ? 
    # Let's stick to the classic: sigma_n = [gamma_dry + m(gamma_sat - gamma_dry)] ...
    # Or simpler: sigma_n = gamma * z * cos^2(alpha) 
    # and u = gamma_w * h_w * cos^2(alpha)
    
    sigma_n = gamma * z * (cos_a**2)
    
    # Pore Water Pressure (u)
    # Flow parallel to slope assumption
    u = GAMMA_W * h_w * (cos_a**2)
    
    # Effective Normal Stress (sigma')
    # Prevent negative stress (suction) for conservative safety
    sigma_prime = np.maximum(sigma_n - u, 0.0)
    
    # Shear Stress (tau) - Driving Force
    tau = gamma * z * sin_a * cos_a
    
    # 4. Factor of Safety Calculation
    # Resisting = c + sigma' * tan(phi)
    resisting = c + sigma_prime * tan_phi
    
    # Driving
    driving = tau
    
    # Handle Stability
    # If driving is tiny (flat), FoS is huge.
    # We use a mask for safe comparison.
    driving = np.maximum(driving, 1e-5) # Avoid div/0
    
    fos = resisting / driving
    
    # 5. Sanity Bounds & Post-Processing
    # Clip FoS to [0, 10] for strictly interpretable range
    # 0 = Fail, >1 = Stable, 10 = Solid Rock/Flat
    fos = np.clip(fos, 0.0, 10.0)
    
    return fos
# import numpy as np

# def compute_fos_vectorized(
#     slope_deg: np.ndarray,
#     elevation: np.ndarray,
#     soil_params: dict,
#     current_saturation: np.ndarray,
#     rainfall_intensity_mmph: float,
#     duration_hours: float = 6.0
# ) -> np.ndarray:
#     """
#     Vectorized Infinite Slope Factor of Safety (FoS) model.
#     Cell-wise (1D arrays), NOT raster-based.
#     """

#     GAMMA_W = 9.81  # kN/m³

#     # --- Geometry ---
#     slope_rad = np.radians(np.clip(slope_deg, 0.1, 89.9))
#     sin_a = np.sin(slope_rad)
#     cos_a = np.cos(slope_rad)

#     c = soil_params['c']
#     phi = soil_params['phi']
#     gamma = soil_params['gamma']
#     z = soil_params['depth']
#     ksat = soil_params['ksat']

#     tan_phi = np.tan(np.radians(phi))

#     # --- Rainfall infiltration (simplified Green-Ampt proxy) ---
#     rain_rate_ms = rainfall_intensity_mmph * 2.777e-7
#     duration_s = duration_hours * 3600.0
#     ne = 0.3  # effective porosity

#     inf_rate = np.minimum(rain_rate_ms, ksat)
#     infiltration_depth = inf_rate * duration_s
#     h_w_rise = infiltration_depth / ne

#     h_w_initial = current_saturation * z
#     h_w = np.clip(h_w_initial + h_w_rise, 0.0, z)

#     # --- Stresses ---
#     sigma_n = gamma * z * cos_a**2
#     u = GAMMA_W * h_w * cos_a**2
#     sigma_eff = np.maximum(sigma_n - u, 0.0)

#     tau = gamma * z * sin_a * cos_a
#     tau = np.maximum(tau, 1e-5)

#     # --- FoS ---
#     resisting = c + sigma_eff * tan_phi
#     fos = resisting / tau

#     return np.clip(fos, 0.0, 10.0)


# def compute_fos_grid(*args, **kwargs):
#     raise RuntimeError(
#         "compute_fos_grid() is deprecated. "
#         "Use compute_fos_vectorized() with slope_deg input."
#     )
