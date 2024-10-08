import sys
from PyQt6.QtWidgets import QApplication
from ui import DMToolsUI

def main():
    app = QApplication(sys.argv)
    
    # Create the main window for the music player UI
    window = DMToolsUI(debug=True)
    window.show()

    # Start the main event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
