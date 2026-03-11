import customtkinter as ctk
from src.components.editor_tool.editor_left_panel import EditorLeftPanel
from src.components.editor_tool.workspace import Workspace

class NetworkEditor(ctk.CTkToplevel):
    # Change 'workspace_data' back to 'workspace' here
    def __init__(self, parent, workspace=None): 
        super().__init__(parent)
        self.workspace = workspace # Store the passed workspace reference
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

        # 2. Workspace Area (The Matplotlib piece)
        self.editor_workspace = Workspace(self.main_container)
        self.editor_workspace.pack(side="left", fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.close_editor)

    def toggle_sidebar(self):
        if self.is_panel_open:
            self.left_panel.configure(width=25)
        else:
            self.left_panel.configure(width=self.current_width)
            
        self.is_panel_open = not self.is_panel_open
        self.left_panel.update_toggle_icon(self.is_panel_open)

    def close_editor(self):
        self.grab_release()
        self.destroy()