import customtkinter as ctk
from src.components.editor_tool.editor_left_panel import EditorLeftPanel

class NetworkEditor(ctk.CTkToplevel):
    def __init__(self, parent, workspace=None):
        super().__init__(parent)
        self.workspace = workspace
        self.title("RescueNet Road Network Editor")
        
        self.after(200, lambda: self.state('zoomed')) 
        self.lift()
        self.focus_force()
        self.grab_set() 

        self.is_panel_open = True
        self.current_width = 250 

        # Main layout container
        self.main_container = ctk.CTkFrame(self, corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # 1. Left Panel
        self.left_panel = EditorLeftPanel(
            self.main_container, 
            toggle_cmd=self.toggle_sidebar
        )
        self.left_panel.pack(side="left", fill="y")

        # 2. Content Area (Map/Canvas area)
        self.content_area = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="#1a1a1a")
        self.content_area.pack(side="left", fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.close_editor)

    def toggle_sidebar(self):
        if self.is_panel_open:
            # Collapse: Keep just enough width for the button tab (approx 25px)
            self.left_panel.configure(width=25)
        else:
            # Expand: Return to the previous width
            self.left_panel.configure(width=self.current_width)
            
        self.is_panel_open = not self.is_panel_open
        self.left_panel.update_toggle_icon(self.is_panel_open)

    def close_editor(self):
        self.grab_release()
        self.destroy()