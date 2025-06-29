import tkinter as tk
import customtkinter as ctk
from srcc.pipeline import Pipeline
from srcc.gui import GUI

def main():
    pipeline = Pipeline()
    pipeline.start()

    root = ctk.CTk()
    app = GUI(root)

    def on_close():
        pipeline.stop()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
    
