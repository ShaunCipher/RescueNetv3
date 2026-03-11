import customtkinter as ctk

class EditFacilities(ctk.CTkFrame):
    def __init__(self, parent, map_handler, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.map_handler = map_handler
        
        # 1. Show Facility Nodes Switch
        self.show_nodes_var = ctk.BooleanVar(value=False)
        self.node_toggle = ctk.CTkSwitch(
            self, 
            text="Show Facility Nodes",
            variable=self.show_nodes_var,
            command=self.handle_node_visibility,
            progress_color="#2fa572"
        )
        self.node_toggle.pack(fill="x", padx=10, pady=(10, 5))

        # 2. Category Filter Label
        self.label = ctk.CTkLabel(self, text="Filter Category:", font=("Arial", 11, "italic"))
        self.label.pack(anchor="w", padx=10)

        # 3. Dropdown (ComboBox)
        self.categories = [
            "Show All", "None", "DRRM", "Hospitals", 
            "Firestations", "Policestations", "Churches", "Schools"
        ]
        
        self.category_dropdown = ctk.CTkComboBox(
            self,
            values=self.categories,
            command=self.handle_filter_selection,
            state="readonly"
        )
        self.category_dropdown.set("Show All")
        self.category_dropdown.pack(fill="x", padx=10, pady=(0, 10))

    def handle_node_visibility(self):
        # Pass the master switch state and current dropdown choice
        self.map_handler.update_facility_visibility(
            self.show_nodes_var.get(),
            self.category_dropdown.get()
        )

    def handle_filter_selection(self, choice):
        # Re-trigger visibility logic whenever the dropdown changes
        self.map_handler.update_facility_visibility(
            self.show_nodes_var.get(),
            choice
        )