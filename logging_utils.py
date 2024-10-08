
import logging
from functools import wraps
from datetime import datetime
import os

def setup_logging(debug: bool = False) -> None:
    """Set up logging with optional debug mode."""
    log_directory = "log"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
        
    log_filename = datetime.now().strftime(f"{log_directory}/%Y-%m-%d_%H-%M-%S.log")
    logging_level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(filename=log_filename, level=logging_level,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def log_method_call(func):
    """Decorator to log method calls in debug mode."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.debug(f"Calling {func.__name__} with args: {args} kwargs: {kwargs}")
        result = func(*args, **kwargs)
        logging.debug(f"{func.__name__} returned {result}")
        return result
    return wrapper
