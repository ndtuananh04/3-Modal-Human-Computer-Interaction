import tkinter as tk
from tkinter import messagebox
import random
import time
import json

class MoveBoxPage(tk.Frame):
    def __init__(self, master, go_back_callback, app_name, task_name):
        super().__init__(master, bg="white")
        self.master = master
        self.go_back_callback = go_back_callback

        self.GRID_ROWS = 20
        self.GRID_COLS = 20
        self.MARGIN_RATIO = 0.11  # phần trăm margin nhỏ xung quanh
        self.BOX_SIZE = 60  # sẽ tính lại khi resize

        self.player_pos = [0, 0]
        self.target_pos = [self.GRID_ROWS // 2, self.GRID_COLS // 2]

        self.obstacles = set()
        self.boxes = [[None for _ in range(self.GRID_COLS)] for _ in range(self.GRID_ROWS)]
        tk.Label(self, text=app_name, font=("Arial", 20), bg="white", fg="black").place(relx=0.5, y=20, anchor="n")
        
        self.master.bind("<Key>", self.on_key_press)
        self.master.bind("<Configure>", self.update_positions)

        # Tracking metrics
        # Latency
        self.start_time = None
        # Count steps
        self.step_count = 0
        # Data
        self.data = {
            "task_name": task_name,
            "app_name": app_name,
            "time": 0,
            "step_count": 0,
        }

    def show_loading_then_generate(self):
        self.loading_label = tk.Label(
            self, text="Generating maze, please wait...",
            font=("Arial", 20), bg="white"
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        self.update()    # 👈 Cho phép hệ thống vẽ xong
        self.create_grid()
        self.generate_maze()        # 👈 Sau đó mới bắt đầu tính toán nặng
        tk.Button(self, text="Back", font=("Arial", 12), bg="gray", fg="white",
                  command=self.go_back).place(x=10, y=10)

    def generate_maze(self):
        # Tùy chọn sinh chướng ngại vật tại đây:
        def generate_obstacles(rows, cols):
            obstacles = set()

            one_forth_rows = rows // 4
            three_forth_rows = 3 * one_forth_rows
            one_forth_cols = cols // 4
            two_forth_cols = 2 * one_forth_cols
            three_forth_cols = 3 * one_forth_cols

            for i in range(three_forth_rows):
                obstacles.add((i, one_forth_cols))
            for i in range(one_forth_cols, three_forth_cols):
                obstacles.add((three_forth_rows, i))
            for i in range(three_forth_rows, one_forth_rows, -1):
                obstacles.add((i, three_forth_cols))
            for i in range(three_forth_cols, two_forth_cols, -1):
                obstacles.add((one_forth_rows, i))
            return obstacles

        self.obstacles = generate_obstacles(self.GRID_ROWS, self.GRID_COLS)
        # Đặt player và target tránh tường
        self.obstacles.discard(tuple(self.player_pos))
        self.obstacles.discard(tuple(self.target_pos))

        self.draw_boxes()
        
        self.loading_label.destroy()

    def go_back(self):
        self.pack_forget()
        self.go_back_callback()

    def create_grid(self):
        for row in range(self.GRID_ROWS):
            for col in range(self.GRID_COLS):
                label = tk.Label(self, bg="white", bd=1, relief="solid")
                self.boxes[row][col] = label
                label.place(width=self.BOX_SIZE, height=self.BOX_SIZE)

    def draw_boxes(self):
        for row in range(self.GRID_ROWS):
            for col in range(self.GRID_COLS):
                box = self.boxes[row][col]
                if [row, col] == self.player_pos:
                    box.configure(bg="#FFCCCC")
                elif [row, col] == self.target_pos:
                    box.configure(bg="light green")
                elif (row, col) in self.obstacles:
                    box.configure(bg="light gray")
                else:
                    box.configure(bg="white")

    def on_key_press(self, event):
        if self.start_time is None:
            self.start_time = time.time()
        self.step_count += 1
        dr, dc = 0, 0
        if event.keysym.lower() == 'w':
            dr = -1
        elif event.keysym.lower() == 's':
            dr = 1
        elif event.keysym.lower() == 'a':
            dc = -1
        elif event.keysym.lower() == 'd':
            dc = 1

        old_r, old_c = self.player_pos
        new_r = old_r + dr
        new_c = old_c + dc

        if (0 <= new_r < self.GRID_ROWS and
            0 <= new_c < self.GRID_COLS and
            (new_r, new_c) not in self.obstacles):

            # ✅ Cập nhật lại màu ô cũ
            if (old_r, old_c) == tuple(self.target_pos):
                self.boxes[old_r][old_c].configure(bg="green light")
            else:
                self.boxes[old_r][old_c].configure(bg="white")

            # ✅ Cập nhật lại ô mới thành người chơi
            self.player_pos = [new_r, new_c]
            self.boxes[new_r][new_c].configure(bg="#FFCCCC")

        # ✅ Kiểm tra nếu đến đích
        if self.player_pos == self.target_pos:
            self.data["time"] = time.time() - self.start_time
            self.data["step_count"] = self.step_count
            print(f"Total time: {self.data['time']:.2f} seconds")
            print(f"Total steps: {self.data['step_count']}")
            with open("./data/" + self.data["app_name"].lower().replace(" ", "_") + "_" + self.data["task_name"].lower().replace(" ", "_") + ".json", "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("🎉", "Data was saved, thank you so much!")
            self.go_back()

    def update_positions(self, event=None):
        win_width = self.master.winfo_width()
        win_height = self.master.winfo_height()

        margin_x = int(win_width * self.MARGIN_RATIO)
        margin_y = int(win_height * self.MARGIN_RATIO)

        grid_width = win_width - 2 * margin_x
        grid_height = win_height - 2 * margin_y

        # Tính lại kích thước ô
        self.BOX_SIZE = min(grid_width // self.GRID_COLS, grid_height // self.GRID_ROWS)

        offset_x = (win_width - self.BOX_SIZE * self.GRID_COLS) // 2
        offset_y = (win_height - self.BOX_SIZE * self.GRID_ROWS) // 2

        for row in range(self.GRID_ROWS):
            for col in range(self.GRID_COLS):
                x = offset_x + col * self.BOX_SIZE
                y = offset_y + row * self.BOX_SIZE
                if self.boxes[row][col] is None:
                    continue
                self.boxes[row][col].place(x=x, y=y, width=self.BOX_SIZE, height=self.BOX_SIZE)
