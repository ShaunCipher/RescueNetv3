import customtkinter as ctk
from .facility_forms import FacilityFormWindow

class EditFacilities(ctk.CTkFrame):
    def __init__(self, parent, map_handler, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.map_handler = map_handler
        
        # State tracking for adding new facilities
        self.adding_mode = False 
        
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

        # --- NEW: Add Facility Button ---
        self.add_btn = ctk.CTkButton(
            self, 
            text="Add Facility", 
            command=self.toggle_add_mode,
            fg_color="#2fa572", 
            hover_color="#23855a"
        )
        self.add_btn.pack(fill="x", padx=10, pady=10)

    def handle_node_visibility(self):
        """Toggles the visibility of plotted nodes on the map."""
        self.map_handler.update_facility_visibility(
            self.show_nodes_var.get(),
            self.category_dropdown.get()
        )

    def handle_filter_selection(self, choice):
        """Updates map visibility when a specific category is chosen."""
        self.map_handler.update_facility_visibility(
            self.show_nodes_var.get(),
            choice
        )

    # --- Facility Placement Logic ---

    def toggle_add_mode(self):
        """Enables placement mode where the next map click triggers a form."""
        self.adding_mode = not self.adding_mode
        
        if self.adding_mode:
            # Change UI to indicate we are waiting for a click
            self.add_btn.configure(text="Click Map to Place...", fg_color="#d35b5b")
            # Connect the map click listener
            self.map_handler.enable_click_listener(self.on_map_clicked)
        else:
            self.reset_add_button()

    def reset_add_button(self):
        self.adding_mode = False
        self.add_btn.configure(text="Add Facility", fg_color="#2fa572")
        self.map_handler.disable_click_listener()

    def on_map_clicked(self, x, y):
        self.open_facility_form(x, y)
        self.reset_add_button()

    def open_facility_form(self, x, y):
        from .facility_forms import FacilityFormWindow
        FacilityFormWindow(self.master, x, y, self.map_handler)