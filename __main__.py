import tkinter as tk
from ui import DMToolsUI
import argparse

def main():
    # Argument parser for optional debug flag
    parser = argparse.ArgumentParser(description="Dungeon Master Music Player")
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    root = tk.Tk()
    app = DMToolsUI(root, debug=args.debug)
    root.mainloop()

if __name__ == "__main__":
    main()
