import customtkinter as ctk
from src.components.core.accident_visibility import AccidentVisibility

class RightPanel(ctk.CTkFrame):
    def __init__(self, master, accident_manager=None, ax=None, fig=None, **kwargs):
        self.toggle_cmd = kwargs.pop('toggle_cmd', None)
        super().__init__(master, **kwargs)
        
        self.am = accident_manager
        self.vis_logic = AccidentVisibility(ax, fig) if ax and fig else None

        self.setup_ui()

    def setup_ui(self):
        # Header
        self.label = ctk.CTkLabel(self, text="Accident Report", font=("Arial", 14, "bold"))
        self.label.pack(pady=(20, 10), padx=20)

        # Visibility Switch
        self.show_acc_var = ctk.BooleanVar(value=True)
        self.vis_switch = ctk.CTkSwitch(
            self, 
            text="Show Accident Location",
            variable=self.show_acc_var,
            command=self.handle_toggle,
            progress_color="#e74c3c"
        )
        self.vis_switch.pack(pady=10, padx=20)

        # Initial plot on startup
        self.refresh_from_csv()

    def handle_toggle(self):
        if self.vis_logic:
            self.vis_logic.toggle_visibility(self.show_acc_var.get())

    def refresh_from_csv(self):
        """Re-reads CSV and updates map. Can be called externally."""
        if self.vis_logic:
            self.vis_logic.update_map()