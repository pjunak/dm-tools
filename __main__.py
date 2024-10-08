
import customtkinter as ctk
from ui import DMToolsUI
import argparse

def main():
    # Argument parser for optional debug flag
    parser = argparse.ArgumentParser(description="Dungeon Master Music Player")
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    ctk.set_appearance_mode("dark")  # Set appearance mode (light, dark, system)
    ctk.set_default_color_theme("blue")  # Set default theme color

    root = ctk.CTk()  # CustomTkinter window
    app = DMToolsUI(root, debug=args.debug)
    root.mainloop()

if __name__ == "__main__":
    main()
