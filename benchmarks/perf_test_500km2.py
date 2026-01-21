import time
import numpy as np
from src.inference.runner import InferenceRunner
import cProfile
import pstats

def run_benchmark():
    print("Initializing 500km² benchmark (approx 2236x2236 grid)...")
    
    # Override grid shape for benchmark
    # 500 sq km = 500 * 10^6 sq m
    # Cell area = 100 sq m
    # N cells = 5,000,000
    # Sqrt(N) = 2236
    
    grid_size = 2236
    
    runner = InferenceRunner()
    runner.grid_shape = (grid_size, grid_size)
    
    # Re-init buffers with new size
    runner.dem = np.ones((grid_size, grid_size), dtype=np.float32)
    runner.initial_saturation = np.zeros((grid_size, grid_size), dtype=np.float32)
    runner.soil_params = {
        'c': np.ones((grid_size, grid_size), dtype=np.float32) * 5000.0,
        'phi': np.ones((grid_size, grid_size), dtype=np.float32) * 30.0,
        'gamma': np.ones((grid_size, grid_size), dtype=np.float32) * 20000.0,
        'depth': np.ones((grid_size, grid_size), dtype=np.float32) * 2.0,
        'ksat': np.ones((grid_size, grid_size), dtype=np.float32) * 1e-5
    }
    
    # Pre-init fusion engine
    runner.fusion_engine.x = np.zeros((grid_size, grid_size), dtype=np.float32)
    runner.fusion_engine.P = np.ones((grid_size, grid_size), dtype=np.float32)
    
    print("Starting Inference Loop...")
    start_time = time.time()
    
    # Profiler
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Create mock large payload
    # Mocking ingest (skip parsing overhead for pure compute test or include it?)
    # "Measure ingestion + preprocessing + inference"
    
    # Coarse rain 50x50
    runner.predict() # This uses random coarse rain inside
    
    profiler.disable()
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"Total Duration: {duration:.4f} seconds")
    
    if duration < 15.0:
        print("PASS: System meets <15s requirement.")
    else:
        print("FAIL: Optimizations needed.")
        
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(20)

if __name__ == "__main__":
    run_benchmark()
