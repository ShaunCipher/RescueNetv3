import customtkinter as ctk
from src.components.core.accident_visibility import AccidentVisibility
from src.components.core.accident_inspect import AccidentInspector

class RightPanel(ctk.CTkFrame):
    def __init__(self, master, accident_manager=None, ax=None, fig=None, workspace=None, **kwargs):
        self.toggle_cmd = kwargs.pop('toggle_cmd', None)
        super().__init__(master, **kwargs)
        
        self.ax = ax
        self.fig = fig
        self.workspace = workspace
        self.am = accident_manager
        self.vis_logic = AccidentVisibility(ax, fig) if ax and fig else None
        self.inspector = None

        self.setup_ui()

    def setup_ui(self):
        self.label = ctk.CTkLabel(self, text="Accident Report", font=("Arial", 14, "bold"))
        self.label.pack(pady=(20, 10), padx=20)

        self.show_acc_var = ctk.BooleanVar(value=True)
        self.vis_switch = ctk.CTkSwitch(
            self, 
            text="Show Accident Location",
            variable=self.show_acc_var,
            command=self.handle_toggle,
            progress_color="#e74c3c"
        )
        self.vis_switch.pack(pady=10, padx=20)

        self.refresh_from_csv()

    def handle_toggle(self):
        if self.vis_logic:
            self.vis_logic.toggle_visibility(self.show_acc_var.get())

    def refresh_from_csv(self):
        """Updates the map and binds the click events to the new markers."""
        if self.vis_logic:
            self.vis_logic.update_map()
        
        # Respect whatever the toggle switch is currently set to
            self.vis_logic.toggle_visibility(self.show_acc_var.get())
        
            acc_artist = getattr(self.vis_logic, 'accident_plot', None)
            if acc_artist:
                plots = {'accident': acc_artist}
                self.inspector = AccidentInspector(
                    self.fig,
                    self.ax,
                    plots,
                    workspace=self.workspace
                )   