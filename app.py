import tkinter as tk
import customtkinter as ctk
from srcc.pipeline import Pipeline
from srcc.gui import GUI

def main():
    pipeline = Pipeline()
    pipeline.start()

    app = GUI()
    app.mainloop()

if __name__ == "__main__":
    main()
    
