import tkinter as tk
from mouse_move import MouseMovementPage
from mouse_jitter import MouseJitterPage
from box_move import MoveBoxPage
from ping_pong import PingPongPage
from survey import SurveyPage
from submit import SubmitPage
import os

# === Hàm kiểm tra JSON đã xong ===
def is_app_done(app_name, task_name):
    filename = f"{app_name.lower().replace(' ', '_')}_{task_name.lower().replace(' ', '_')}.json"
    print(f"Checking if {filename} exists...")
    return os.path.exists(os.path.join("data", filename))

# === Trang cuối cùng (LeafPage) ===
class LeafPage(tk.Frame):
    def __init__(self, master, go_back_callback, task_name, app_index):
        super().__init__(master, bg="white")
        tk.Button(self, text="← Back", command=go_back_callback).place(x=10, y=10)
        tk.Label(self, text=f"{task_name} - App {app_index}", font=("Arial", 20), bg="white").pack(pady=100)

# === SubPage: Trang có 4 App ===
class SubPage(tk.Frame):
    def __init__(self, master, go_back_callback, task_name):
        super().__init__(master, bg="white")
        self.master = master
        self.task_name = task_name
        self.go_back_callback = go_back_callback
        
        tk.Button(self, text="← Back", command=go_back_callback).place(x=10, y=10)
        tk.Label(self, text=f"{task_name} - Select App", font=("Arial", 20), bg="white").pack(pady=50)

        app_names = ["Farid Karimli et al", "Project Gameface - Google", "Our Method", "Use Mouse"] if task_name != "Move Box" and task_name != "Ping Pong" else ["Our Method", "Use Keyboard"]
        for app_name in app_names:
            label = f"{app_name}"
            if is_app_done(app_name, self.task_name):
                label += " [done]"
            btn = tk.Button(self, text=label, font=("Arial", 16), width=30, height=2,
                            command=lambda i=app_name: self.open_leaf(i))
            btn.pack(pady=10)

    def show_subpage(self):
        if self.master.active_frame:
            self.master.active_frame.pack_forget()
        self.master.active_frame = SubPage(self.master, self.go_back_callback, self.task_name)
        self.master.active_frame.pack(fill="both", expand=True)

    def open_leaf(self, app_name):
        match self.task_name:
            case "Mouse Movement":
                page_class = MouseMovementPage
            case "Mouse Jitter":
                page_class = MouseJitterPage
            case "Move Box":
                page_class = MoveBoxPage
            case "Ping Pong":
                page_class = PingPongPage
        self.master.switch_frame(page_class, self.show_subpage, app_name, self.task_name)

# === Main Menu: 6 nút chính ===
class MainMenu(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="white")
        self.master = master

        tk.Label(self, text="Main Menu", font=("Arial", 24, "bold"), bg="white").pack(pady=50)

        tasks = [
            ("Mouse Movement", "Mouse Movement"),
            ("Mouse Jitter", "Mouse Jitter"),
            ("Move Box", "Move Box"),
            ("Ping Pong", "Ping Pong"),
            ("Survey", "Survey"),
        ]

        for label, task_name in tasks:
            if(task_name != "Survey"):
                tk.Button(
                    self,
                    text=label,
                    font=("Arial", 18),
                    width=25,
                    height=2,
                    command=lambda t=task_name: master.switch_frame(SubPage, master.show_main_menu, t)
                ).pack(pady=10)
            else:
                if is_app_done("0", task_name):
                    label += " [done]"
                tk.Button(
                    self,
                    text=label,
                    font=("Arial", 18),
                    width=25,
                    height=2,
                    command=lambda t=task_name: master.switch_frame(SurveyPage, master.show_main_menu, "0", t)
                ).pack(pady=10)

        tk.Button(self, text="Submit", font=("Arial", 18), width=25, height=2, bg="lightblue",
                  command=lambda: master.switch_frame(SubmitPage, master.show_main_menu)).pack(pady=30)

# === App chính ===
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hand-Free Research Experiment")
        self.attributes('-fullscreen', True)
        self.bind("<Escape>", lambda e: self.destroy())

        self.active_frame = None
        self.show_main_menu()

    def switch_frame(self, FrameClass, go_back_callback, *args):
        if self.active_frame:
            self.active_frame.pack_forget()
        self.active_frame = FrameClass(self, go_back_callback, *args)
        self.active_frame.pack(fill="both", expand=True)
        if type(self.active_frame) == MoveBoxPage:
            self.active_frame.show_loading_then_generate()

    def show_main_menu(self):
        if self.active_frame:
            self.active_frame.pack_forget()
        self.active_frame = MainMenu(self)
        self.active_frame.pack(fill="both", expand=True)

# === Chạy ứng dụng ===
if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")  # Tạo thư mục nếu chưa có
    app = App()
    app.mainloop()
