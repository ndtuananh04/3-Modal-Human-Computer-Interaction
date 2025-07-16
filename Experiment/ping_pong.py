import tkinter as tk
import random
import json
from tkinter import messagebox

class PingPongPage(tk.Frame):
    def __init__(self, master, go_back_callback, app_name, task_name):
        super().__init__(master, bg="white")
        self.master = master
        self.go_back_callback = go_back_callback

        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Nút quay lại
        self.back_btn = tk.Button(self, text="Back", command=self.go_back, bg="gray", fg="white")
        self.back_btn.place(x=10, y=10)

        # Tốc độ có thể chỉnh
        self.paddle_speed = 100     # tốc độ di chuyển vợt
        self.ball_speed = 4        # tốc độ khung hình (ms)

        self.ball_dx = 4
        self.ball_dy = -4
        self.running = True

        # Setup sau khi canvas được tạo
        self.after(100, self.setup_game)
        tk.Label(self, text=app_name, font=("Arial", 20), bg="white", fg="black").place(relx=0.5, y=20, anchor="n")

        # Dùng A/D thay vì ←/→
        self.master.bind("<a>", self.move_left)
        self.master.bind("<d>", self.move_right)

        self.total_win = 0
        self.game_count = 0
        self.score = 0

        self.score_label = tk.Label(self, text="score: " + str(self.score), font=("Arial", 20), bg="white", fg="black")
        self.score_label.place(relx=0.95, y=20, anchor="n")
        self.total_win_label = tk.Label(self, text="total win: " + str(self.total_win), font=("Arial", 20), bg="white", fg="black")
        self.total_win_label.place(relx=0.85, y=20, anchor="n")

        self.data = {
            "task_name": task_name,
            "app_name": app_name,
            "total_wins": 0,
            "total_games": 0,
        }

    def go_back(self):
        self.running = False
        self.pack_forget()
        self.go_back_callback()

    def setup_game(self):
        self.score_label.config(text="score: " + str(self.score))
        if self.game_count == 4:
            self.data["total_wins"] = self.total_win
            self.data["total_games"] = self.game_count
            with open("./data/" + self.data["app_name"].lower().replace(" ", "_") + "_" + self.data["task_name"].lower().replace(" ", "_") + ".json", "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("🎉", "Data was saved, thank you so much!")
            self.go_back()
            return
        self.running = True
        self.canvas.delete("all")

        width = self.winfo_width() or 800
        height = self.winfo_height() or 600

        # 🎯 Tạo vị trí ngẫu nhiên trong 1/3 phía trên màn hình
        ball_x = random.randint(40, width - 40)
        ball_y = random.randint(40, height // 3)

        # 👉 Hướng bóng ngẫu nhiên (dx, dy ∈ {-4, 4})
        self.ball_dx = random.choice([-4, 4])
        self.ball_dy = random.choice([-4, 4])

        # Tạo bóng và vợt
        self.ball = self.canvas.create_oval(ball_x - 20, ball_y - 20,
                                            ball_x + 20, ball_y + 20,
                                            fill="#FFCCCC", outline="")

        self.paddle = self.canvas.create_rectangle(width//2 - 100, height - 60,
                                                   width//2 + 100, height - 30,
                                                   fill="light green", outline="")

        self.game_loop()

    def move_left(self, event):
        self.canvas.move(self.paddle, -self.paddle_speed, 0)

    def move_right(self, event):
        self.canvas.move(self.paddle, self.paddle_speed, 0)

    def game_loop(self):
        if not self.running:
            return

        self.move_ball()
        self.after(self.ball_speed, self.game_loop)

    def move_ball(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)

        ball_coords = self.canvas.coords(self.ball)
        paddle_coords = self.canvas.coords(self.paddle)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Va chạm tường trái/phải
        if ball_coords[0] <= 0 or ball_coords[2] >= canvas_width:
            self.ball_dx *= -1

        # Va chạm trần
        if ball_coords[1] <= 0:
            self.ball_dy *= -1
            self.score += 1
            self.score_label.config(text="score: " + str(self.score))
            if self.score == 5:
                self.score = 0
                self.game_count += 1
                self.running = False
                self.total_win += 1
                self.total_win_label.config(text="total win: " + str(self.total_win))
                self.canvas.create_text(canvas_width//2, canvas_height//2,
                                    text="You win", fill="Green", font=("Arial", 32))
                self.after(1000, self.setup_game)

        # Va chạm vợt
        if (paddle_coords[0] < ball_coords[2] and
            paddle_coords[2] > ball_coords[0] and
            paddle_coords[1] < ball_coords[3] and
            paddle_coords[3] > ball_coords[1]):
            self.ball_dy *= -1


        # Rơi xuống dưới
        if ball_coords[3] >= canvas_height:
            self.game_count += 1
            self.running = False
            self.canvas.create_text(canvas_width//2, canvas_height//2,
                                    text="Game Over", fill="red", font=("Arial", 32))
            self.score = 0
            self.after(1000, self.setup_game)
