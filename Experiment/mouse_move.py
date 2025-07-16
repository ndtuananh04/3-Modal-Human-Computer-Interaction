import tkinter as tk
import time
import json
from tkinter import messagebox

class MouseMovementPage(tk.Frame):
    def __init__(self, master, go_back_callback, app_name, task_name):
        super().__init__(master, bg="white")

        self.master = master
        self.go_back_callback = go_back_callback

        self.GRID_ROWS = 3
        self.GRID_COLS = 3
        self.current_index = 0  # Theo dõi index của box đang hiển thị

        # Dữ liệu cho box
        self.box_size = [[(100, 100), (40, 40), (150, 150)],
                         [(50, 80), (100, 70), (70, 70)],
                         [(120, 50), (60, 60), (80, 40)]]
        self.color_map = [["yellow", "green", "yellow"],
                          ["green", "yellow", "green"],
                          ["green", "green", "yellow"]]

        # Canvas để vẽ đường
        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Mouse path tracking
        self.prev_x = None
        self.prev_y = None
        self.tracking_mouse_path = False  # Chỉ vẽ khi đang active
        self.canvas.bind("<Motion>", self.draw_mouse_path)

        # Chuỗi click đúng tương ứng
        self.click_requirements = [["right", "left", "right"],
                                   ["left", "right", "left"],
                                   ["left", "left", "right"]]

        self.boxes = []
        self.create_all_boxes()
        self.show_box(self.current_index)
        self.appear_idx = [5, 3, 8, 1, 2, 6, 9, 7, 4]
        # Nút Back
        tk.Button(self, text="Back", font=("Arial", 12), bg="gray", fg="white",
                  command=self.go_back).place(x=10, y=10)
        tk.Label(self, text=app_name, font=("Arial", 20), bg="white", fg="black").place(relx=0.5, y=20, anchor="n")

        self.click_count = 0
        self.bind_all("<Button-1>", self.count_click)
        self.bind_all("<Button-3>", self.count_click)
        self.master.bind("<Configure>", self.update_box_positions)
        self.master.bind("<Escape>", lambda e: self.master.destroy())

        # Tracking metrics
        self.end = False
        self.box_tracking = 0
        # Latency
        self.start_time = None
        self.previous_time = None
        # Tỉ lệ click nhầm
        self.previous_click_count = 0
        # Đường đi lệch so với đường đi tối ưu
        self.total_deviation = 0
        self.count_points = 0
        self.first_point = (None, None)
        self.last_point = (None, None)
        # Data
        self.data = {
            "task_name": task_name,
            "app_name": app_name,
            "points": [],
            "total_time": 0,
        }
    def point_to_line_distance(self, px, py, x1, y1, x2, y2):
        numerator = abs((x2 - x1)*(y1 - py) - (x1 - px)*(y2 - y1))
        denominator = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        return numerator / denominator if denominator != 0 else 0

    def count_click(self, event):
        self.click_count += 1
        print("Click count:", self.click_count)

    def go_back(self):
        self.pack_forget()
        self.go_back_callback()

    def create_all_boxes(self):
        for row in range(self.GRID_ROWS):
            for col in range(self.GRID_COLS):
                box = tk.Label(self, bd=2, relief="solid", font=("Arial", 12), fg="black")
                box.bind("<Button-1>", self.handle_left_click)
                box.bind("<Button-3>", self.handle_right_click)
                self.boxes.append((row, col, box))  # Lưu (vị trí, box)

    def show_box(self, index):
        # Ẩn tất cả box trước
        for _, _, b in self.boxes:
            b.place_forget()

        if index > len(self.boxes):
            # Save data here
            if not self.end:
                self.end = True
                self.total_time = time.time() - self.start_time if self.start_time else 0
                self.data["total_time"] = self.total_time
                print(f"Total time: {self.total_time:.2f} seconds")
                self.tracking_mouse_path = False
                with open("./data/" + self.data["app_name"].lower().replace(" ", "_") + "_" + self.data["task_name"].lower().replace(" ", "_") + ".json", "w", encoding="utf-8") as f:
                    json.dump(self.data, f, indent=4, ensure_ascii=False)
                tk.Label(self, text="Data was saved, thank you so much!", font=("Arial", 20), bg="white", fg="black").place(relx=0.5, y=70, anchor="n")
            return

        row, col, box = self.boxes[index]
        color = self.color_map[row][col]
        w, h = self.box_size[row][col]
        click_type = self.click_requirements[row][col]

        text = "left" if color == "green" else "right"

        # 👉 Tính kích cỡ font dựa theo chiều cao hoặc chiều rộng
        font_size = max(8, min(w, h) // 6)
        font = ("Arial", font_size)

        # Đặt vị trí
        win_width = self.master.winfo_width()
        win_height = self.master.winfo_height()
        padding_x = win_width // (self.GRID_COLS + 1)
        padding_y = win_height // (self.GRID_ROWS + 1)
        x = padding_x * (col + 1) - w // 2
        y = padding_y * (row + 1) - h // 2

        box.configure(bg="light " + color, text=text)
        box.place(x=x, y=y, width=w, height=h)

    def handle_left_click(self, event):
        self.process_click(event.widget, "left")

    def handle_right_click(self, event):
        self.process_click(event.widget, "right")

    def process_click(self, box, click_type):
        row, col, current_box = self.boxes[self.appear_idx[self.current_index] - 1]
        required_click = self.click_requirements[row][col]

        if click_type == required_click:
            if not self.tracking_mouse_path:
                self.start_time = time.time()
            self.tracking_mouse_path = True
            # Click đúng, chuyển sang box tiếp theo
            current_box.place_forget()
            self.current_index += 1
            # Save data here
            self.box_tracking += 1

            win_width = self.master.winfo_width()
            win_height = self.master.winfo_height()
            padding_x = win_width // (self.GRID_COLS + 1)
            padding_y = win_height // (self.GRID_ROWS + 1)

            if self.current_index < len(self.boxes):
                self.first_point =  (padding_x * (col + 1), padding_y * (row + 1))
                row, col, current_box = self.boxes[self.appear_idx[self.current_index] - 1]
                self.last_point = (padding_x * (col + 1), padding_y * (row + 1))

            if self.box_tracking > 1:
                self.diff_count = self.click_count - self.previous_click_count
                self.diff_time = time.time() - self.previous_time if self.previous_time else 0
                self.total_deviation /= self.count_points if self.count_points > 0 else 0
                print(f"Box tracking: {self.box_tracking}, Click diff: {self.diff_count}, Time diff: {self.diff_time:.2f} seconds, Deviation: {self.total_deviation:.2f}")
                self.data["points"].append({
                    "box_index": self.appear_idx[self.current_index - 1],
                    "click_type": click_type,
                    "click_count": self.diff_count,
                    "time": self.diff_time,
                    "deviation": self.total_deviation
                })
            self.total_deviation = 0
            self.count_points = 0
            self.previous_click_count = self.click_count
            self.previous_time = time.time()
            self.show_box(self.appear_idx[self.current_index] - 1 if self.current_index < len(self.appear_idx) else 99)

    def update_box_positions(self, event=None):
        # Cập nhật lại vị trí box hiện tại khi thay đổi kích thước cửa sổ
       self.show_box(self.appear_idx[self.current_index] - 1 if self.current_index < len(self.appear_idx) else 99)

    def draw_mouse_path(self, event):
        if not self.tracking_mouse_path:
            return
        
        if self.prev_x is not None and self.prev_y is not None:
            self.canvas.create_line(self.prev_x, self.prev_y, event.x, event.y,
                                    fill="light blue", width=2, capstyle=tk.ROUND)
        self.prev_x = event.x
        self.prev_y = event.y
        self.total_deviation += self.point_to_line_distance(self.prev_x, self.prev_y,
                                                            self.first_point[0], self.first_point[1],
                                                            self.last_point[0], self.last_point[1])
        self.count_points += 1

