import customtkinter as ctk
from .map_handler import MapHandler
from .editor_controls import EditorControls

class Workspace(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, corner_radius=0, fg_color="#1a1a1a", **kwargs)
        
        # 1. Initialize Map Logic
        self.map_handler = MapHandler(self)
        self.map_widget = self.map_handler.get_canvas_widget()
        self.map_widget.pack(fill="both", expand=True)

        # 2. Initialize the external Controls component
        self.controls = EditorControls(
            self, 
            toolbar=self.map_handler.toolbar,
            refresh_cmd=self.refresh_map_plot
        )
        self.controls.place(relx=0.02, rely=0.02, anchor="nw")

        # 3. Load and plot the facility nodes immediately on startup
        self.map_handler.load_and_plot_facilities()

    def refresh_map_plot(self):
        # Optional: You can clear the axis here if you want a clean slate
        self.map_handler.ax.clear() 
        self.map_handler.load_and_plot_facilities()