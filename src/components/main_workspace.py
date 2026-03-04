import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt 
import matplotlib.image as mpimg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from .terminal_panel import TerminalPanel # Import our new class

class MainWorkspace(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=0, fg_color="transparent", **kwargs)

        # 1. CREATE VERTICAL SPLITTER
        self.v_paned = tk.PanedWindow(
            self, orient=tk.VERTICAL, bg="#1a1a1a", sashwidth=4, sashpad=0, borderwidth=0
        )
        self.v_paned.pack(fill="both", expand=True)

        # --- 2. TOP COMPONENT: MAP AREA ---
        self.work_area = ctk.CTkFrame(self.v_paned, corner_radius=0, fg_color="#212121")
        
        # --- 3. BOTTOM COMPONENT: TERMINAL AREA (Modularized) ---
        self.terminal = TerminalPanel(self.v_paned)

        # 4. ASSEMBLE VERTICAL PANES
        self.v_paned.add(self.work_area, stretch="always")
        self.v_paned.add(self.terminal, height=180, stretch="never")

        # 5. INITIALIZE MAP
        self.setup_map()

    def setup_map(self):
        """Standard Matplotlib Map setup"""
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(10, 8), dpi=100)
        self.fig.patch.set_facecolor('#212121')
        self.ax.set_facecolor('#212121')

        try:
            img = mpimg.imread(r'img\map.png')
            self.ax.imshow(img)
            self.ax.axis('on') 
            self.ax.tick_params(axis='both', colors='#666666', labelsize=8)
            self.ax.set_xlabel("X (Pixels)", color='#444444', fontsize=9)
            self.ax.set_ylabel("Y (Pixels)", color='#444444', fontsize=9)
            self.terminal.log("Map engine loaded successfully.")
        except FileNotFoundError:
            self.ax.text(0.5, 0.5, "map.png not found\nCheck img/ folder", 
                         ha='center', va='center', color='red')
            self.ax.axis('off')
            self.terminal.log("ERROR: Map file not found.")

        self.fig.tight_layout(pad=2.5)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.work_area)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)
        self.canvas.draw()

    def log_analysis(self, message):
        """Forwarding method to keep current compatibility"""
        self.terminal.log(message)