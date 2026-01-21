import cProfile
import pstats
import io
import time
from functools import wraps

def profile_performance(output_file=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            pr = cProfile.Profile()
            pr.enable()
            start = time.time()
            
            result = func(*args, **kwargs)
            
            end = time.time()
            pr.disable()
            
            print(f"Function {func.__name__} took {end-start:.4f}s")
            
            s = io.StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats('cumtime')
            ps.print_stats(20)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(s.getvalue())
            else:
                print(s.getvalue())
                
            return result
        return wrapper
    return decorator
