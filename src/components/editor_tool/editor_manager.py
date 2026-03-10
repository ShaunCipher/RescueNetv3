from .map_renderer import MapRenderer
from .event_handler import EventHandler

class EditorManager:
    def __init__(self, shell, workspace, canvas_frame):
        self.shell = shell
        self.workspace = workspace
        self.has_unsaved_changes = False
        
        # Initialize the fragmented tools
        self.renderer = MapRenderer(canvas_frame)
        self.events = EventHandler(self.renderer, self)
        
        # Start the view
        self.renderer.draw_background()

    def setup_filter_ui(self, container):
        # We will add logic here to build checkboxes in the sidebar
        pass

    def handle_map_interaction(self, x, y):
        print(f"Manager received click at: {x}, {y}")
        self.has_unsaved_changes = True

    def save_to_disk(self):
        print("Manager calling DataHandler to save CSVs...")
        self.has_unsaved_changes = False