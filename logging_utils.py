import logging
import os
import time


def setup_logger(debug: bool):
    log_folder = "log"
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_filename = os.path.join(log_folder, f"debug-{timestamp}.log")

    logging.basicConfig(filename=log_filename,
                        level=logging.DEBUG if debug else logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger()
    logger.info("Logging started")
