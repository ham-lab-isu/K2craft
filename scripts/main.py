import tkinter as tk
from gui import Kaw2FFFControl

# Main program
if __name__ == "__main__":
    root = tk.Tk()
    app = Kaw2FFFControl(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
