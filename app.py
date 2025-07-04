import tkinter as tk
import customtkinter as ctk
from srcc.pipeline import Pipeline
from srcc.guii import GUI
from srcc.gui.main_window import MainWindow

def main():
    pipeline = Pipeline()
    pipeline.start()

    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
    
