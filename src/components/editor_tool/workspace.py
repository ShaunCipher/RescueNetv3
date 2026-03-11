import customtkinter as ctk
from .map_handler import MapHandler

class Workspace(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, corner_radius=0, fg_color="#1a1a1a", **kwargs)
        
        # Initialize the map handler
        self.map_handler = MapHandler(self)
        
        # Get the widget and display it
        self.map_widget = self.map_handler.get_canvas_widget()
        self.map_widget.pack(fill="both", expand=True)

    def redraw(self):
        """Call this whenever nodes are added/moved."""
        self.map_handler.canvas.draw()