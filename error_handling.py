import logging

class ErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger('DMTools.ErrorHandler')

    def log_error(self, error_message: str):
        """Log an error message."""
        self.logger.error(f"Error occurred: {error_message}")

    def handle_file_error(self, file_path: str):
        """Handle file-related errors such as missing or invalid files."""
        error_message = f"File not found or invalid: {file_path}"
        self.log_error(error_message)

    def handle_general_exception(self, exception: Exception):
        """Handle general exceptions and log them."""
        self.log_error(str(exception))
