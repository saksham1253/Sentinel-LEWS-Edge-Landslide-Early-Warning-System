import pandas as pd
import xarray as xr
import numpy as np
import rasterio
from rasterio.transform import from_origin
from datetime import datetime
import os

def fetch_imd_gauges(start_date: datetime, end_date: datetime, region: str) -> pd.DataFrame:
    """
    Fetch gauge data from IMD (Indian Meteorological Department) sources.
    Returns normalized DataFrame with UTC timestamps.
    
    Args:
        start_date: Start datetime
        end_date: End datetime
        region: Region identifier
        
    Returns:
        pd.DataFrame: Columns [timestamp_utc, station_id, lat, lon, rainfall_mm]
    """
    # TODO: Implement actual API/Scraper
    # Returning mock data for now
    print(f"Fetching IMD data for {region} from {start_date} to {end_date}")
    
    dates = pd.date_range(start=start_date, end=end_date, freq='1H', tz='UTC')
    stations = ['STN_001', 'STN_002', 'STN_003']
    data = []
    
    for stn in stations:
        # Simulate some random rainfall
        rainfall = np.random.exponential(scale=2.0, size=len(dates))
        rainfall[rainfall < 0.5] = 0.0 # Sparsity
        
        df = pd.DataFrame({
            'timestamp_utc': dates,
            'station_id': stn,
            'lat': 27.0 + np.random.rand(), 
            'lon': 80.0 + np.random.rand(),
            'rainfall_mm': rainfall
        })
        data.append(df)
        
    return pd.concat(data, ignore_index=True)

def fetch_gpm_imerg(start_date: datetime, end_date: datetime, bbox: list) -> xr.Dataset:
    """
    Fetch GPM IMERG satellite precipitation data.
    
    Args:
        start_date: Start datetime
        end_date: End datetime
        bbox: [min_lon, min_lat, max_lon, max_lat]
        
    Returns:
        xr.Dataset: varying by time, lat, lon
    """
    print(f"Fetching GPM IMERG for {bbox} from {start_date} to {end_date}")
    
    # Mock xarray dataset
    times = pd.date_range(start=start_date, end=end_date, freq='30min', tz='UTC')
    lons = np.linspace(bbox[0], bbox[2], 50)
    lats = np.linspace(bbox[1], bbox[3], 50)
    
    precipitation = np.random.rand(len(times), len(lats), len(lons)) * 5.0
    
    ds = xr.Dataset(
        data_vars=dict(
            precipitation_cal=(["time", "lat", "lon"], precipitation)
        ),
        coords=dict(
            time=times,
            lat=lats,
            lon=lons
        ),
        attrs=dict(description="Mock GPM IMERG Data")
    )
    return ds

def fetch_dem(source="SRTM", bounds=None) -> str:
    """
    Fetch DEM raster path. In a real system this might download or return a path to a cached file.
    
    Args:
        source: SRTM or Cartosat
        bounds: Optional bounds
        
    Returns:
        str: Path to local DEM file
    """
    # Create a dummy DEM if it doesn't exist
    dem_path = os.path.join("data", "static", f"mock_dem_{source}.tif")
    os.makedirs(os.path.dirname(dem_path), exist_ok=True)
    
    if not os.path.exists(dem_path):
        print(f"Generating mock DEM at {dem_path}")
        transform = from_origin(80.0, 27.5, 0.0001, 0.0001) # Approx 10m
        arr = np.random.rand(1000, 1000) * 500 + 1000 # Elevation 1000-1500m
        
        with rasterio.open(
            dem_path,
            'w',
            driver='GTiff',
            height=arr.shape[0],
            width=arr.shape[1],
            count=1,
            dtype=arr.dtype,
            crs='+proj=latlong',
            transform=transform,
        ) as dst:
            dst.write(arr, 1)
            
    return dem_path

def read_archived_rainfall_csv(path: str) -> pd.DataFrame:
    """
    Read historical rainfall CSV and normalize columns/time.
    
    Expected columns in CSV: timestamp, rain_mm, station_id (optional)
    """
    df = pd.read_csv(path)
    # Basic normalization logic
    if 'timestamp' in df.columns:
        df['timestamp_utc'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC')
    elif 'time' in df.columns:
         df['timestamp_utc'] = pd.to_datetime(df['time']).dt.tz_localize('UTC')
         
    return df
