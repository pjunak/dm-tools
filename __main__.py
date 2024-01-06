import tkinter as tk
from ui import DMToolsUI

def main():
    root = tk.Tk()
    app = DMToolsUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
