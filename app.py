import tkinter as tk
from srcc.pipeline import Pipeline
from srcc.gui import GUI

def main():
    pipeline = Pipeline()
    pipeline.start()

    root = tk.Tk()
    app = GUI(root)

    def on_close():
        pipeline.stop()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
    
