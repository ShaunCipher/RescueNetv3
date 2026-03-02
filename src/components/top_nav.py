import customtkinter as ctk
import tkinter as tk
from utils.clock import get_current_time_string

class TopNavigation(ctk.CTkFrame):
    def __init__(self, master, toggle_left_cmd, toggle_right_cmd, **kwargs):
        super().__init__(master, height=50, corner_radius=0, **kwargs)
        
        self.clock_format = ctk.StringVar(value="24h | MM/DD/YYYY")

        # --- 1. LEFT SIDE: NAVIGATION LABEL ---
        self.nav_label = ctk.CTkLabel(self, text="PROJECT NAVIGATOR", font=("Arial", 12, "bold"), text_color="gray")
        self.nav_label.pack(side="left", padx=20)

        # --- 2. CENTER: MAIN TITLE ---
        # Using .place() to ignore side-packing and hit the absolute center
        self.main_title = ctk.CTkLabel(
            self, 
            text="DRRM Parian Calamba | RescueNet", 
            font=("Arial", 16, "bold")
        )
        self.main_title.place(relx=0.5, rely=0.5, anchor="center")

        # --- 3. RIGHT SIDE: CLOCK & DISCRETE BUTTON ---
        # Settings Button (Packed first to be furthest right)
        self.settings_btn = ctk.CTkButton(
            self, 
            text="⋮", 
            width=20, 
            height=25, 
            fg_color="transparent", 
            text_color="gray",
            hover_color="#333333",
            command=self.show_menu
        )
        self.settings_btn.pack(side="right", padx=(5, 20))

        # Time Label
        self.clock_label = ctk.CTkLabel(self, text="", font=("Consolas", 13))
        self.clock_label.pack(side="right", padx=5)

        # --- POPUP MENU ---
        self.menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", borderwidth=0)
        self.menu.add_command(label="24h | MM/DD/YYYY", command=lambda: self.set_format("24h | MM/DD/YYYY"))
        self.menu.add_command(label="24h | Month DD, YY", command=lambda: self.set_format("24h | Month DD, YY"))
        self.menu.add_command(label="12h | MM/DD/YYYY", command=lambda: self.set_format("12h | MM/DD/YYYY"))
        self.menu.add_command(label="12h | Month DD, YY", command=lambda: self.set_format("12h | Month DD, YY"))

        self.update_clock()

    def set_format(self, fmt):
        self.clock_format.set(fmt)

    def show_menu(self):
        x = self.settings_btn.winfo_rootx()
        y = self.settings_btn.winfo_rooty() + self.settings_btn.winfo_height()
        self.menu.tk_popup(x, y)

    def update_clock(self):
        time_str = get_current_time_string(self.clock_format.get())
        self.clock_label.configure(text=time_str)
        self.after(1000, self.update_clock)