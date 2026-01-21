import pandas as pd
import numpy as np
import os

def load_shimla_data(csv_path: str) -> pd.DataFrame:
    """
    Load the Shimla dataset from CSV.
    
    Args:
        csv_path: Path to the CSV file.
        
    Returns:
        pd.DataFrame: Loaded data.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}")
    
    print(f"[LOADER] Loading dataset from {csv_path}...")
    # Read CSV
    # Using low_memory=False to avoid mixed type warnings if any, usually fine for 50MB
    df = pd.read_csv(csv_path)
    
    print(f"[LOADER] Loaded {len(df)} records.")
    
    # Basic validation
    required_cols = ['lat', 'lon', 'elevation', 'slope', 'clay', 'sand', 'silt', 'bulk', 'R_7d']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
        
    return df
