import sys
import logging
from PyQt6.QtWidgets import QApplication
from ui import DMToolsUI

# Set up logging with UTF-8 encoding for console
logging.basicConfig(
    handlers=[logging.StreamHandler(sys.stdout)],
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

sys.stdout.reconfigure(encoding='utf-8')  # Ensure stdout uses UTF-8 encoding

def main():
    app = QApplication(sys.argv)
    window = DMToolsUI(debug=True)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
