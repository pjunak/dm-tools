import logging
import os, sys
from datetime import datetime

def setup_logger(debug: bool = False) -> logging.Logger:
    log_dir = 'log'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    for f in os.listdir(log_dir):
        try:
            os.remove(os.path.join(log_dir, f))
        except PermissionError:
            print(f"Could not remove log file {f} because it's being used by another process.")

    # Create new log file with datetime
    log_filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.log'
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger('DMToolsLogger')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Prevent adding multiple handlers if called more than once
    if not logger.hasHandlers():
        # File Handler
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG if debug else logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Stream handler for console output
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.DEBUG if debug else logging.INFO)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    
    return logger
