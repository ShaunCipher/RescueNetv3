import customtkinter as ctk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.image as mpimg
import os

class NetworkEditor(ctk.CTkToplevel):
    def __init__(self, master, workspace=None):
        super().__init__(master)
        self.workspace = workspace
        self.has_unsaved_changes = False 
        
        # 1. Window Configuration
        self.title("Road Network Editor")
        self.after(0, lambda: self.state('zoomed')) 
        self.lift()
        self.attributes("-topmost", True)
        self.after(500, lambda: self.attributes("-topmost", False))
        self.focus_force()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 2. Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # LEFT PANEL (Sidebar)
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#2b2b2b")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # RIGHT PANEL (Canvas)
        self.canvas_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.canvas_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.setup_sidebar_content()
        self.setup_canvas()

    def setup_sidebar_content(self):
        """Builds the sidebar with tools and bottom action buttons."""
        ctk.CTkLabel(self.sidebar, text="NETWORK EDITOR", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Tool Buttons (Top Section)
        ctk.CTkButton(self.sidebar, text="📍 Edit Nodes", fg_color="#3d3d3d").pack(fill="x", padx=15, pady=8)
        ctk.CTkButton(self.sidebar, text="🛣️ Edit Roads", fg_color="#3d3d3d").pack(fill="x", padx=15, pady=8)
        
        # --- BOTTOM ACTION SECTION ---
        # Exit Editor at the very bottom
        self.exit_btn = ctk.CTkButton(
            self.sidebar, text="❌ Exit Editor", 
            fg_color="#3d3d3d", hover_color="#c0392b",
            command=self.on_close
        )
        self.exit_btn.pack(side="bottom", fill="x", padx=20, pady=(0, 20))

        # Save Changes sitting directly ABOVE Exit Editor
        self.save_btn = ctk.CTkButton(
            self.sidebar, 
            text="💾 Save Changes", 
            fg_color="#28a745", 
            hover_color="#218838",
            font=("Arial", 13, "bold"),
            command=self.confirm_save
        )
        self.save_btn.pack(side="bottom", fill="x", padx=20, pady=10)

    def setup_canvas(self):
        """Initializes the map with visible coordinate axes."""
        self.fig, self.ax = plt.subplots(figsize=(10, 8), facecolor='#1a1a1a')
        self.ax.set_facecolor('#1a1a1a')

        self.ax.tick_params(axis='both', colors='white', labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color('#555555')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.display_map_background()

    def display_map_background(self):
        """Loads map.png onto the canvas."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.abspath(os.path.join(current_dir, '..', '..', 'img', 'map.png'))

        if os.path.exists(img_path):
            img = mpimg.imread(img_path)
            self.ax.imshow(img, zorder=0)
        else:
            self.ax.text(0.5, 0.5, "map.png not found", color='white', ha='center', transform=self.ax.transAxes)

        self.ax.set_aspect('equal')
        self.canvas.draw()

    def confirm_save(self):
        """Verification popup before data processing."""
        response = messagebox.askyesno(
            "Confirm Save", 
            "Are you sure you want to save all changes?\n\nThis action will update your network data files."
        )
        if response:
            self.perform_save_logic()

    def perform_save_logic(self):
        """Placeholder for core saving logic."""
        print("DEBUG: Changes saved to disk.")
        self.has_unsaved_changes = False
        messagebox.showinfo("Saved", "Changes applied successfully!")

    def on_close(self):
        """Close logic with unsaved changes check."""
        if self.has_unsaved_changes:
            response = messagebox.askyesnocancel("Unsaved Changes", "Save before exiting?")
            if response is True: 
                self.perform_save_logic()
                self.destroy()
            elif response is False: 
                self.destroy()
        else:
            self.destroy()