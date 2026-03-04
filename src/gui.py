import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt
from src.components.top_nav import TopNavigation
from src.components.left_panel import LeftPanel
from src.components.right_panel import RightPanel
from src.components.main_workspace import MainWorkspace 
from src.theme import Theme

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 1. WINDOW SETUP & PROTOCOL ---
        self.title("RescueNet | DRRM Parian")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Set appearance to system theme (usually dark)
        ctk.set_appearance_mode("dark")

        # Get screen dimensions and set geometry
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        
        try:
            self.state('zoomed')
        except tk.TclError:
            pass

        # --- 2. LAYOUT CONFIGURATION ---
        # Column 0 takes full width; Row 1 takes all vertical space below Nav
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- 3. TOP NAVIGATION ---
        self.top_nav = TopNavigation(self, self.toggle_left, self.toggle_right)
        self.top_nav.grid(row=0, column=0, sticky="new")

        # --- 4. DRAGGABLE CONTAINER (PanedWindow) ---
        self.paned_window = tk.PanedWindow(
            self, 
            orient=tk.HORIZONTAL, 
            bg=Theme.BG_DARK,
            sashwidth=4, 
            sashpad=0, 
            borderwidth=0
        )
        self.paned_window.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)

        # --- 5. INITIALIZE COMPONENTS (Order Matters!) ---
        
        # Create Workspace FIRST so we can pass it to the panels for linking
        self.center_view = MainWorkspace(self.paned_window)

        # Create Left Panel and pass the workspace reference for Filter Logic
        self.left_panel = LeftPanel(
            self.paned_window, 
            toggle_cmd=self.toggle_left,
            workspace=self.center_view
        )
        
        # Build the Facility Checkboxes now that workspace (and its plots) exists
        if hasattr(self.left_panel, "setup_filters"):
            self.left_panel.setup_filters()

        self.right_panel = RightPanel(self.paned_window, toggle_cmd=self.toggle_right)

        # Log link confirmation to the modular terminal
        try:
            self.center_view.log_analysis("GUI System successfully linked to modular Terminal.")
            self.center_view.log_analysis("Filter Logic initialized in Left Panel.")
        except Exception:
            pass 

        # --- 6. ADD TO PANED WINDOW ---
        # Add panes in order: Left -> Center -> Right
        self.paned_window.add(self.left_panel, width=250, stretch="never")
        self.paned_window.add(self.center_view, stretch="always")
        self.paned_window.add(self.right_panel, width=250, stretch="never")

        # --- 7. FLOATING RE-OPEN BUTTONS ---
        # These appear only when a panel is collapsed
        self.btn_reopen_left = ctk.CTkButton(
            self, text=">", width=15, height=60, 
            fg_color=Theme.BG_DARKER,
            hover_color=Theme.HOVER_GRAY,
            command=self.toggle_left
        )
        
        self.btn_reopen_right = ctk.CTkButton(
            self, text="<", width=15, height=60, 
            fg_color=Theme.BG_DARKER,
            hover_color=Theme.HOVER_GRAY,
            command=self.toggle_right
        )

        # Track visibility states for toggle logic
        self.left_visible = True
        self.right_visible = True

    # --- TOGGLE LOGIC ---

    def _refresh_panes(self):
        """Helper to re-add visible panes in the correct order to the PanedWindow"""
        for pane in [self.left_panel, self.center_view, self.right_panel]:
            try:
                self.paned_window.forget(pane)
            except:
                pass
        
        if self.left_visible:
            self.paned_window.add(self.left_panel, width=250, stretch="never")
        
        self.paned_window.add(self.center_view, stretch="always")
        
        if self.right_visible:
            self.paned_window.add(self.right_panel, width=250, stretch="never")

    def toggle_left(self):
        """Collapses or expands the Left Panel"""
        if self.left_visible:
            self.paned_window.forget(self.left_panel)
            self.btn_reopen_left.place(relx=0.0, rely=0.5, anchor="w")
            self.left_visible = False
        else:
            self.btn_reopen_left.place_forget()
            self.left_visible = True
            self._refresh_panes()

    def toggle_right(self):
        """Collapses or expands the Right Panel"""
        if self.right_visible:
            self.paned_window.forget(self.right_panel)
            self.btn_reopen_right.place(relx=1.0, rely=0.5, anchor="e")
            self.right_visible = False
        else:
            self.btn_reopen_right.place_forget()
            self.right_visible = True
            self._refresh_panes()

    def on_closing(self):
        """Proper shutdown sequence to prevent memory leaks from Matplotlib"""
        plt.close('all')
        self.quit()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()