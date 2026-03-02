import customtkinter as ctk
import tkinter as tk
from src.components.top_nav import TopNavigation
from src.components.left_panel import LeftPanel
from src.components.right_panel import RightPanel

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 1. DEVICE ADAPTIVE FULL SCREEN ---
        self.title("RescueNet | DRRM Parian")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        
        try:
            self.state('zoomed')
        except tk.TclError:
            pass

        # --- 2. LAYOUT CONFIGURATION ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- 3. TOP NAVIGATION ---
        self.top_nav = TopNavigation(self, self.toggle_left, self.toggle_right)
        self.top_nav.grid(row=0, column=0, sticky="new")

        # --- 4. DRAGGABLE CONTAINER (PanedWindow) ---
        self.paned_window = tk.PanedWindow(
            self, orient=tk.HORIZONTAL, bg="#1a1a1a", sashwidth=4, sashpad=0, borderwidth=0
        )
        self.paned_window.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)

        # --- 5. INITIALIZE COMPONENTS ---
        # Note: Parents are the paned_window
        self.left_panel = LeftPanel(self.paned_window, toggle_cmd=self.toggle_left)
        self.center_frame = ctk.CTkFrame(self.paned_window, corner_radius=0, fg_color="#212121")
        self.right_panel = RightPanel(self.paned_window, toggle_cmd=self.toggle_right)

        self.main_label = ctk.CTkLabel(self.center_frame, text="Main Workspace Area", font=("Arial", 20))
        self.main_label.place(relx=0.5, rely=0.5, anchor="center")

        # --- 6. ADD TO PANED WINDOW ---
        self.paned_window.add(self.left_panel, width=250, stretch="never")
        self.paned_window.add(self.center_frame, stretch="always")
        self.paned_window.add(self.right_panel, width=250, stretch="never")

        # --- 7. DISCRETE RE-OPEN BUTTONS (Floating) ---
        self.btn_reopen_left = ctk.CTkButton(
            self, text=">", width=15, height=60, fg_color="#2b2b2b", 
            hover_color="#3d3d3d", command=self.toggle_left
        )
        
        self.btn_reopen_right = ctk.CTkButton(
            self, text="<", width=15, height=60, fg_color="#2b2b2b", 
            hover_color="#3d3d3d", command=self.toggle_right
        )

        # Visibility State
        self.left_visible = True
        self.right_visible = True

    # --- TOGGLE LOGIC ---

    def _refresh_panes(self):
        """Helper to re-add visible panes in the correct order"""
        # Remove everything currently in the paned window
        for pane in [self.left_panel, self.center_frame, self.right_panel]:
            try:
                self.paned_window.forget(pane)
            except:
                pass
        
        # Add them back based on current visibility state
        if self.left_visible:
            self.paned_window.add(self.left_panel, width=250, stretch="never")
        
        self.paned_window.add(self.center_frame, stretch="always")
        
        if self.right_visible:
            self.paned_window.add(self.right_panel, width=250, stretch="never")

    def toggle_left(self):
        if self.left_visible:
            self.paned_window.forget(self.left_panel)
            self.btn_reopen_left.place(relx=0.0, rely=0.5, anchor="w")
            self.left_visible = False
        else:
            self.btn_reopen_left.place_forget()
            self.left_visible = True
            self._refresh_panes()

    def toggle_right(self):
        if self.right_visible:
            self.paned_window.forget(self.right_panel)
            self.btn_reopen_right.place(relx=1.0, rely=0.5, anchor="e")
            self.right_visible = False
        else:
            self.btn_reopen_right.place_forget()
            self.right_visible = True
            self._refresh_panes()