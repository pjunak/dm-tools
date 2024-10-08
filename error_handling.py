
import logging

class ErrorHandler:
    def __init__(self, log_file: str = "error.log") -> None:
        self.log_file = log_file
        logging.basicConfig(filename=self.log_file, level=logging.ERROR,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def log_error(self, error_message: str) -> None:
        """Log an error message."""
        logging.error(error_message)
        print(f"Error: {error_message}")
