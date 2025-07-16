import tkinter as tk
from tkinter import messagebox, Scrollbar, Canvas
import json

class SurveyPage(tk.Frame):
    def __init__(self, master, go_back_callback, app_name, task_name):
        super().__init__(master, bg="white")
        self.master = master
        self.go_back_callback = go_back_callback
        self.app_name = app_name
        self.task_name = task_name
        self.max_points = 10

        self.data = {
            "task_name": task_name,
            "app_name": app_name,
            "responses": {
                "mouse": {},
                "keyboard": {}
            }
        }

        self.mouse_questions = [
            "Có tốn nhiều thời gian để thành thạo ứng dụng không",
            "Việc nhấn trái/phải chuột phản hồi có nhanh không",
            "Việc di chuột có phản hồi nhanh không",
            "Việc nhấn trái/ phải chuột có khó không",
            "Để di chuyển chuột chính xác có khó không",
            "Việc di chuột theo hướng dọc có khó không",
            "Việc di chuột theo hướng ngang có khó không",
            "Việc di chuyển chuột có gây mỏi không",
            "Bạn đánh giá có thể ứng dụng chuột này cho người khuyết tật không"
        ]
        self.keyboard_questions = [
            "Việc ấn nút có khó không",
            "Việc ấn nút độ trễ cao không",
            "Việc ấn nút có dễ bị nhầm không",
            "Liệu có thể ứng dụng việc ấn nút này hỗ trợ người khuyết tật tương tác nhanh không"
        ]

        self.mouse_entries = []
        self.keyboard_entries = []

        self.build_ui()

    def build_ui(self):
        # Nút Back
        tk.Button(self, text="← Back", command=self.go_back, font=("Arial", 12)).place(x=10, y=10)

        # Tiêu đề trang
        tk.Label(self, text=self.app_name, font=("Arial", 24, "bold"), bg="white").pack(pady=(20, 5))
        tk.Label(self, text="Đánh giá trên thang điểm 1 đến 10", font=("Arial", 16), bg="white").pack(pady=(20, 0))

        # Scrollable canvas
        canvas = Canvas(self, bg="white", highlightthickness=0)
        scrollbar = Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame_container = tk.Frame(canvas, bg="white")
        self.scroll_frame = tk.Frame(scroll_frame_container, bg="white")
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        scroll_frame_container.bind_all("<MouseWheel>", _on_mousewheel)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        

        # Center the content frame
        scroll_frame_container.columnconfigure(0, weight=1)
        self.scroll_frame.pack(anchor="center", pady=20)

        # Mouse Section
        tk.Label(self.scroll_frame, text="Mouse Evaluation", font=("Arial", 20, "bold"), bg="white").grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(10, 5))

        headers = ["", "Farid Karimli", "Project Gameface", "Our Method", "Use Mouse"]
        for i, header in enumerate(headers):
            self.scroll_frame.columnconfigure(i, weight=1)
            tk.Label(
                self.scroll_frame,
                text=header,
                font=("Arial", 14),
                bg="white",
                width=10,
                anchor="center",          # Căn giữa trong Label
                justify="center",
            ).grid(row=1, column=i, padx=0, pady=0, sticky="nsew")  # Căn giữa trong ô lưới

        for r, question in enumerate(self.mouse_questions):
            # Label câu hỏi — không căn giữa
            tk.Label(
                self.scroll_frame,
                text=question,
                font=("Arial", 14),
                bg="white",
                anchor="w",            # Căn trái nội dung trong Label
                width=50,
                wraplength=400,
                justify="left",
            ).grid(row=r+2, column=0, sticky="w", padx=10, pady=5)

            row_entries = []
            for c in range(4):
                entry = tk.Entry(
                    self.scroll_frame,
                    font=("Arial", 14),
                    width=2,
                    bd=2,
                    relief="solid"
                )
                entry.grid(row=r+2, column=c+1, padx=80, pady=20, sticky="nsew")  # Căn giữa trong lưới
                row_entries.append(entry)
            self.mouse_entries.append(row_entries)

        # Keyboard Section
        base_row = len(self.mouse_questions) + 3
        tk.Label(self.scroll_frame, text="Keyboard Evaluation", font=("Arial", 20, "bold"), bg="white").grid(row=base_row, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 5))

        for i, question in enumerate(self.keyboard_questions):
            # Câu hỏi: căn trái
            tk.Label(
                self.scroll_frame,
                text=question,
                font=("Arial", 14),
                bg="white",
                anchor="w",
                width=50,
                wraplength=400,
                justify="left"
            ).grid(row=base_row + 1 + i, column=0, sticky="w", padx=10, pady=5)

            # Entry: căn giữa
            entry = tk.Entry(
                self.scroll_frame,
                font=("Arial", 14),
                width=2,
                bd=2,
                relief="solid"
            )
            entry.grid(row=base_row + 1 + i, column=1, padx=80, pady=20, sticky="nsew")
            self.keyboard_entries.append(entry)

        # Submit button
        tk.Button(self.scroll_frame, text="Submit", font=("Arial", 16), bg="green", fg="white",
                  command=self.submit).grid(row=base_row + len(self.keyboard_questions) + 2, column=0, columnspan=5, pady=60)

        scroll_frame_container.update_idletasks()
        width = self.master.winfo_width() - scroll_frame_container.winfo_reqwidth()
        canvas.create_window((width // 2, 0), window=scroll_frame_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def go_back(self):
        self.pack_forget()
        self.go_back_callback()

    def submit(self):
        mouse_data = {}
        for i, row in enumerate(self.mouse_entries):
            q_label = self.mouse_questions[i]
            answers = []
            for entry in row:
                val = entry.get().strip()
                if not val or not val.isdigit() or not (1 <= int(val) <= self.max_points):
                    messagebox.showerror("Error", f"Invalid input in mouse question {i+1}. Must be 1–{self.max_points}.")
                    return
                answers.append(int(val))
            mouse_data[q_label] = answers

        keyboard_data = {}
        for i, entry in enumerate(self.keyboard_entries):
            val = entry.get().strip()
            if not val or not val.isdigit() or not (1 <= int(val) <= self.max_points):
                messagebox.showerror("Error", f"Invalid input in keyboard question {i+1}. Must be 1–{self.max_points}.")
                return
            keyboard_data[self.keyboard_questions[i]] = int(val)

        self.data["responses"]["mouse"] = mouse_data
        self.data["responses"]["keyboard"] = keyboard_data

        filename = f"./data/{self.app_name.lower().replace(' ', '_')}_{self.task_name.lower().replace(' ', '_')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

        messagebox.showinfo("Success", "Survey submitted successfully!")
        self.go_back()
