# 1. installing a virtual environment   python -m venv venv
# 2. activation                         venv\Scripts\activate 
# 3. Installing libraries                pip install ... (psutil, sv_ttk)                                                                                                         )

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from Controller.controller import USBController  # Import main class

####################### ===== main ===== #######################
def main():
    try:
        # Create the main window
        root = tk.Tk()
        
        # Setting the application icon
        if os.name == 'nt':  # Windows
            try:
                root.iconbitmap(default='icon.ico')  # Place icon.ico in the same folder
            except:
                pass  # The icon is not required
        
        # Initializing and running the application
        app = USBController(root)
        
        # Handling window closing
        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                root.destroy()
                sys.exit(0)
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Starting the main loop
        root.mainloop()
    
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application crashed:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
