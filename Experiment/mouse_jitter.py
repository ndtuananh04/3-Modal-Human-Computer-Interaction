import tkinter as tk
from tkinter import messagebox
import json

class MouseJitterPage(tk.Frame):
    def __init__(self, master, go_back_callback, app_name, task_name):
        super().__init__(master, bg="white")
        self.master = master
        self.go_back_callback = go_back_callback
    
        # Canvas để vẽ
        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Nút quay lại
        self.back_button = tk.Button(self, text="Back", command=self.go_back)
        self.back_button.place(x=10, y=10)
        self.inform_label = tk.Label(self, text="Press Enter To Start", font=("Arial", 20), bg="white", fg="black")
        self.inform_label.place(relx=0.5, y=70, anchor="n")

        tk.Label(self, text=app_name, font=("Arial", 20), bg="white", fg="black").place(relx=0.5, y=20, anchor="n")
        # Dấu cộng
        self.canvas.bind("<Configure>", self.draw_plus)

        # Bắt sự kiện chuột
        self.canvas.bind("<Motion>", self.on_mouse_move)

        # Bắt phím Enter
        self.master.bind("<Return>", self.on_enter_press)

        # Lưu điểm trước đó để vẽ đường
        self.tracking_mouse_path = False
        self.last_x = None
        self.last_y = None

        # Tracking metrics
        self.diff = 0
        self.cnt = 0

        self.data = {
            "task_name": task_name,
            "app_name": app_name,
            "deviation": 0,
        }

    def go_back(self):
        self.pack_forget()
        self.go_back_callback()

    def draw_plus(self, event=None):
        self.canvas.delete("plus")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        length = 20
        self.canvas.create_line(w//2 - length, h//2, w//2 + length, h//2, fill="black", width=2, tags="plus")
        self.canvas.create_line(w//2, h//2 - length, w//2, h//2 + length, fill="black", width=2, tags="plus")

    def on_enter_press(self, event=None):
        self.inform_label.config(text="Data is being saved...", font=("Arial", 20), bg="white", fg="black")
        self.tracking_mouse_path = True
        self.after(10000, self.show_saved_message)

    def show_saved_message(self):
        if self.cnt > 0:
            self.data["deviation"] = self.diff / self.cnt
        with open("./data/" + self.data["app_name"].lower().replace(" ", "_") + "_" + self.data["task_name"].lower().replace(" ", "_") + ".json", "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        self.inform_label.config(text="Data was saved, thank you so much!")
        self.tracking_mouse_path = False

    def on_mouse_move(self, event):
        if not self.tracking_mouse_path:
            return
        
        if self.last_x is not None and self.last_y is not None:
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, fill="skyblue", width=2, tags="trail")
        self.last_x = event.x
        self.last_y = event.y

        # Tính độ lệch
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        self.diff += ((event.x - w // 2) ** 2 + (event.y - h // 2) ** 2) ** 0.5
        self.cnt += 1
