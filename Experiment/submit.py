import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json

class SubmitPage(tk.Frame):
    def __init__(self, master, go_back_callback):
        super().__init__(master, bg="white")
        self.master = master
        self.go_back_callback = go_back_callback

        # Tiêu đề (căn trên giữa)
        self.label = tk.Label(self, text="Submit Experiment", font=("Arial", 24, "bold"), bg="white", fg="black")
        self.label.place(relx=0.5, y=20, anchor="n")

        # Khung chính để căn giữa các thành phần
        center_frame = tk.Frame(self, bg="white")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Ô nhập đường dẫn
        self.path_var = tk.StringVar()
        path_frame = tk.Frame(center_frame, bg="white")
        path_frame.pack(pady=30)

        tk.Label(path_frame, text="Choose target folder:", bg="white", font=("Arial", 18)).pack(side="left")
        tk.Entry(path_frame, textvariable=self.path_var, width=40, font=("Arial", 16)).pack(side="left", padx=10)
        tk.Button(path_frame, text="Browse", font=("Arial", 14), command=self.browse_folder).pack(side="left")

        # Nút Submit (to hơn, căn giữa)
        tk.Button(center_frame, text="Submit", bg="green", fg="white", font=("Arial", 18, "bold"),
                  width=20, height=2, command=self.submit).pack(pady=20)

        # Nút back ở góc trái trên
        tk.Button(self, text="Back", command=self.go_back, bg="gray", fg="white", font=("Arial", 12)).place(x=10, y=10)

        # Thoát bằng ESC
        self.master.bind("<Escape>", lambda e: self.master.destroy())

        # Tổng hợp dữ liệu
        self.summary_data = {
            "total_apps": 13,
            "completed_apps": 0,
            "incomplete_apps": 13,
            "app_details": {}
        }

        self.tasks = {
            "Mouse Movement": [
                "Farid Karimli et al",
                "Project Gameface - Google",
                "Our Method",
                "Use Mouse"
            ],
            "Mouse Jitter": [
                "Farid Karimli et al",
                "Project Gameface - Google",
                "Our Method",
                "Use Mouse"
            ],
            "Move Box": [
                "Our Method",
                "Use Keyboard"
            ], 
            "Ping Pong": [
                "Our Method",
                "Use Keyboard"
            ],
            "Survey": "0"
        }

        self.file_names = []
        for task, apps in self.tasks.items():
            if isinstance(apps, list):
                for app in apps:
                    file_name = f"{app.replace(' ', '_').lower()}_{task.replace(' ', '_').lower()}"
                    self.file_names.append(file_name)
            else:
                file_name = f"{apps.replace(' ', '_').lower()}_{task.replace(' ', '_').lower()}"
                self.file_names.append(file_name)

        print("File names to check:", self.file_names)
        print("len(file_names):", len(self.file_names))
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)

    def process_data(self):
        for file in os.listdir("data"):
            if file.endswith(".json"):
                with open(os.path.join("data", file), "r", encoding="utf-8") as f:
                    file_name = file[:-5]  # Loại bỏ .json
                    if file_name in self.file_names:
                        self.summary_data["completed_apps"] += 1
                        self.summary_data["incomplete_apps"] -= 1
                        self.summary_data["app_details"][file_name] = json.load(f)
                    # Xử lý dữ liệu ở đây
                    
    def submit(self):
        path = self.path_var.get()
        if not path:
            messagebox.showwarning("Missing Path", "Please choose a folder to submit!")
        else:
            self.process_data()
            print(f"completed_apps: {self.summary_data['completed_apps']}")
            if self.summary_data["completed_apps"] < self.summary_data["total_apps"]:
                messagebox.showwarning("Incomplete Data", "You have not completed all tasks. Please ensure all tasks are done before submitting.")
                return
            summary_file = os.path.join(path, "summary.json")
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(self.summary_data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Done", f"Data has been submitted to:\n{path}")
            self.go_back()

    def go_back(self):
        self.pack_forget()
        self.go_back_callback()
