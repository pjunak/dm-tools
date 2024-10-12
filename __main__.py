from PyQt6.QtWidgets import QApplication
from ui.main_ui import DMToolsUI
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DMToolsUI(debug=True)  # Assuming you want debug logging enabled
    window.show()
    sys.exit(app.exec())
