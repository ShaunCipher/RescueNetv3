import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class NetworkEditor(ctk.CTkToplevel):
    def __init__(self, master, workspace=None):
        super().__init__(master)
        self.workspace = workspace
        
        # 1. Full Screen Configuration
        self.title("Road Network Editor")
        self.after(0, lambda: self.state('zoomed')) # Full screen on launch
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 2. Main Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT PANEL (Toolbox) ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#2b2b2b")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # --- RIGHT PANEL (Canvas) ---
        self.canvas_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.canvas_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.setup_sidebar_content()
        self.setup_canvas()

    def setup_sidebar_content(self):
        """Adds buttons to the editor sidebar."""
        ctk.CTkLabel(self.sidebar, text="NETWORK EDITOR", font=("Arial", 20, "bold")).pack(pady=20)

        # Tool Buttons
        self.btn_add_node = self.create_tool_btn("📍 Add Facility Node", "#1f538d")
        self.btn_add_road = self.create_tool_btn("⚪ Add Road Node", "#3d3d3d")
        self.btn_draw_edge = self.create_tool_btn("🛣️ Draw New Road", "#28a745")
        self.btn_delete = self.create_tool_btn("🗑️ Delete Element", "#c0392b")

        # Bottom Actions
        self.btn_save = ctk.CTkButton(self.sidebar, text="💾 Save Changes", fg_color="#28a745", hover_color="#218838")
        self.btn_save.pack(side="bottom", fill="x", padx=20, pady=(5, 10))

        self.btn_exit = ctk.CTkButton(self.sidebar, text="❌ Exit Editor", fg_color="#3d3d3d", command=self.on_close)
        self.btn_exit.pack(side="bottom", fill="x", padx=20, pady=10)

    def create_tool_btn(self, text, color):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color=color, height=40, anchor="w")
        btn.pack(fill="x", padx=15, pady=8)
        return btn

    def setup_canvas(self):
        """Placeholder for the interactive graph."""
        self.fig, self.ax = plt.subplots(figsize=(10, 8), facecolor='#1a1a1a')
        self.ax.set_facecolor('#1a1a1a')
        self.ax.set_xticks([]); self.ax.set_yticks([]) # Hide axes
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def on_close(self):
        self.destroy()