import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt
import os

# Components
from src.components.top_nav import TopNavigation
from src.components.left_panel import LeftPanel
from src.components.right_panel import RightPanel
from src.components.main_workspace import MainWorkspace 

# Core Engines
from src.components.core.command_center import CommandCenter 
from src.components.core.status_manager import StatusManager
from src.theme import Theme

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 1. WINDOW SETUP & PROTOCOL ---
        self.title("RescueNet | DRRM Parian Calamba")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        ctk.set_appearance_mode("dark")

        # Fullscreen setup
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

        # --- 3. DRAGGABLE CONTAINER (PanedWindow) ---
        self.paned_window = tk.PanedWindow(
            self, 
            orient=tk.HORIZONTAL, 
            bg=Theme.BG_DARK,
            sashwidth=4, 
            sashpad=0, 
            borderwidth=0
        )
        self.paned_window.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)

        # --- 4. INITIALIZE COMPONENTS (Strict Order) ---
        
        # A. Create Workspace FIRST
        self.center_view = MainWorkspace(self.paned_window)

        # B. Create the Command Center "Brain" 
        self.cmd_center = CommandCenter(
            master_registry=self.center_view.master_registry, 
            fig=self.center_view.fig, 
            ax=self.center_view.ax
        )

        # C. THE HANDSHAKE (Crucial Fix)
        # Identify the manager for use in the RightPanel and TopNav
        self.acc_manager = None
        if hasattr(self.center_view, "report_manager"):
            self.acc_manager = self.center_view.report_manager
            self.cmd_center.report_manager = self.acc_manager
        else:
            print("WARNING: report_manager not found in MainWorkspace!")

        # D. Initialize Status Manager
        self.center_view.status_manager = StatusManager(
            fig=self.center_view.fig,
            ax=self.center_view.ax,
            master_registry=self.center_view.master_registry
        )

        # E. Create Top Nav
        self.top_nav = TopNavigation(
            self, 
            self.toggle_left, 
            self.toggle_right,
            command_center=self.cmd_center 
        )
        self.top_nav.grid(row=0, column=0, sticky="new")

        # F. Initialize Side Panels
        self.left_panel = LeftPanel(
            self.paned_window, 
            toggle_cmd=self.toggle_left,
            workspace=self.center_view
        )
        
        if hasattr(self.left_panel, "setup_filters"):
            self.left_panel.setup_filters()

        # FIXED: Passing the accident_manager here to solve the TypeError
        self.right_panel = RightPanel(
            self.paned_window, 
            toggle_cmd=self.toggle_right,
            accident_manager=self.acc_manager
        )

        # --- 5. LOG SYSTEM STATUS ---
        try:
            self.center_view.log_analysis("GUI Initialized: Systems Linked.")
            self.center_view.log_analysis("Command Center & Accident Manager online.")
        except Exception:
            pass 


        # --- 6. ADD TO PANED WINDOW ---
        self.paned_window.add(self.left_panel, width=280, stretch="never")
        self.paned_window.add(self.center_view, stretch="always")
        # Set to 320 to fit the new Command Center content
        self.paned_window.add(self.right_panel, width=320, stretch="never")

        # --- 7. FLOATING RE-OPEN BUTTONS ---
        self.btn_reopen_left = ctk.CTkButton(
            self, text=">", width=20, height=60, 
            fg_color=Theme.BG_DARKER, hover_color=Theme.HOVER_GRAY,
            command=self.toggle_left
        )
        
        self.btn_reopen_right = ctk.CTkButton(
            self, text="<", width=20, height=60, 
            fg_color=Theme.BG_DARKER, hover_color=Theme.HOVER_GRAY,
            command=self.toggle_right
        )

        self.left_visible = True
        self.right_visible = True

    # --- TOGGLE LOGIC ---
    def _refresh_panes(self):
        for pane in [self.left_panel, self.center_view, self.right_panel]:
            try: self.paned_window.forget(pane)
            except: pass
        
        if self.left_visible:
            self.paned_window.add(self.left_panel, width=280, stretch="never")
        self.paned_window.add(self.center_view, stretch="always")
        if self.right_visible:
            self.paned_window.add(self.right_panel, width=320, stretch="never")

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


    def on_closing(self):
        plt.close('all')
        self.quit()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()