import logging
import os
import time


def setup_logger(debug: bool = False) -> logging.Logger:
    logger = logging.getLogger('DMToolsLogger')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    if not logger.hasHandlers():
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG if debug else logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    return logger
