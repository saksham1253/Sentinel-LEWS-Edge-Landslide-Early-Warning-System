import numpy as np
import cv2 # using opencv for fast resizing if available, else scipy
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import zoom

def compute_slope(dem: np.ndarray, cell_size: float) -> np.ndarray:
    """
    Compute slope in degrees from DEM.
    Simple finite difference.
    """
    dy, dx = np.gradient(dem, cell_size)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    return np.degrees(slope_rad)

def downscale_rainfall(coarse_rain: np.ndarray, 
                       dem: np.ndarray, 
                       coarse_res: float, 
                       fine_res: float = 10.0,
                       mode: str = 'deterministic') -> np.ndarray:
    """
    Downscale coarse rainfall grid to match DEM resolution using terrain-aware Weighting.
    
    Args:
        coarse_rain: 2D numpy array of rainfall (mm)
        dem: 2D numpy array of elevation (m) matching the fine grid target shape
        coarse_res: Resolution of coarse grid in meters (e.g. 10000 for 10km)
        fine_res: Resolution of fine grid (DEM) in meters (e.g. 10)
        mode: 'deterministic' (slope-weighted) or 'stochastic' (adds noise)
        
    Returns:
        high_res_rain_grid: 2D numpy array at fine resolution
    """
    
    # 1. Bilinear Interpolation to target shape
    scale_factor = coarse_res / fine_res
    
    # Note: We assume coarse_rain covers the exact same extent as DEM for simplicity
    # In production, we'd use geotransforms to align. 
    # Here we use scipy.ndimage.zoom
    
    zoom_factors = (dem.shape[0] / coarse_rain.shape[0], dem.shape[1] / coarse_rain.shape[1])
    rain_bilinear = zoom(coarse_rain, zoom_factors, order=1) # order=1 is bilinear
    
    # 2. Compute Slope
    slope = compute_slope(dem, fine_res)
    
    # 3. Slope Weighting (Orographic effect proxy)
    # detailed: Rain increases with slope generally on windward side. 
    # Simplified model: R_fine = R_base * (1 + 0.05 * normalized_slope)
    slope_norm = (slope - np.mean(slope)) / (np.std(slope) + 1e-6)
    weights = 1.0 + 0.1 * slope_norm # 0.1 is arbitrary orographic factor
    weights = np.clip(weights, 0.5, 2.0)
    
    rain_fine = rain_bilinear * weights
    
    # 4. Energy Conservation (Mass Balance)
    # The total volume of water should be approximately preserved.
    # Vol_coarse = Sum(R_coarse) * CellArea_coarse
    # Vol_fine = Sum(R_fine) * CellArea_fine
    
    total_rain_coarse = np.sum(coarse_rain) * (coarse_res**2)
    total_rain_fine = np.sum(rain_fine) * (fine_res**2)
    
    correction_factor = total_rain_coarse / (total_rain_fine + 1e-6)
    rain_fine = rain_fine * correction_factor
    
    if mode == 'stochastic':
        # Add random noise for uncertainty quantification
        noise = np.random.normal(0, 0.1 * np.mean(rain_fine), rain_fine.shape)
        rain_fine = np.maximum(0, rain_fine + noise)
        
    return rain_fine
