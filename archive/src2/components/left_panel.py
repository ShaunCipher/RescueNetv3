import customtkinter as ctk

class LeftPanel(ctk.CTkFrame):
    def __init__(self, master, toggle_cmd, workspace=None, **kwargs):
        super().__init__(master, width=250, corner_radius=0, fg_color="#2b2b2b", **kwargs)
        self.workspace = workspace
        
        # --- 1. CLOSE BUTTON ---
        # Positioned to the right of the panel to allow users to hide the sidebar
        self.close_btn = ctk.CTkButton(
            self, text="<", width=20, height=60, 
            fg_color="#3d3d3d", command=toggle_cmd
        )
        self.close_btn.place(relx=1.0, rely=0.5, anchor="e")
        
        # --- 2. FACILITY VISIBILITY SECTION (Dropdown 1) ---
        self.facility_section = ctk.CTkFrame(self, fg_color="transparent")
        self.facility_section.pack(fill="x", padx=10, pady=(20, 5))

        self.facility_toggle_btn = ctk.CTkButton(
            self.facility_section, 
            text="▼ Facility Visibility", 
            height=35,
            fg_color="#3d3d3d",
            hover_color="#4d4d4d",
            anchor="w",
            command=self.toggle_facility_menu
        )
        self.facility_toggle_btn.pack(fill="x")

        # Container for visibility checkboxes
        self.facility_dropdown_container = ctk.CTkFrame(self.facility_section, fg_color="#333333")
        self.facility_dropdown_container.pack(fill="x", pady=(5, 0)) 
        self.is_facility_open = True # Start open by default

        # --- 3. STATUS OVERLAYS SECTION (Dropdown 2) ---
        self.status_section = ctk.CTkFrame(self, fg_color="transparent")
        self.status_section.pack(fill="x", padx=10, pady=5)

        self.status_toggle_btn = ctk.CTkButton(
            self.status_section, 
            text="▶ Check Facility Status", 
            height=35,
            fg_color="#3d3d3d",
            hover_color="#4d4d4d",
            anchor="w",
            command=self.toggle_status_menu
        )
        self.status_toggle_btn.pack(fill="x")

        # Container for status checkboxes (starts hidden)
        self.status_dropdown_container = ctk.CTkFrame(self.status_section, fg_color="#333333")
        self.is_status_open = False

        # --- 4. ACTIONS SECTION ---
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=10, pady=20)

        self.route_btn = ctk.CTkButton(
            self.action_frame, 
            text="Route Facilities", 
            height=40,
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.open_routing
        )
        self.route_btn.pack(fill="x", padx=10)

    # --- TOGGLE LOGIC ---

    def toggle_facility_menu(self):
        """Shows or hides the facility visibility checkboxes."""
        if self.is_facility_open:
            self.facility_dropdown_container.pack_forget()
            self.facility_toggle_btn.configure(text="▶ Facility Visibility")
        else:
            self.facility_dropdown_container.pack(fill="x", pady=(5, 0))
            self.facility_toggle_btn.configure(text="▼ Facility Visibility")
        self.is_facility_open = not self.is_facility_open

    def toggle_status_menu(self):
        """Shows or hides the status overlay checkboxes."""
        if self.is_status_open:
            self.status_dropdown_container.pack_forget()
            self.status_toggle_btn.configure(text="▶ Check Facility Status")
        else:
            self.status_dropdown_container.pack(fill="x", pady=(5, 0))
            self.status_toggle_btn.configure(text="▼ Check Facility Status")
        self.is_status_open = not self.is_status_open

    # --- INITIALIZATION ---

    def setup_filters(self):
        """
        Populates both dropdown containers using their respective logic engines.
        This is called from gui.py after components are initialized.
        """
        # 1. Populate Facility Visibility (FilterLogic)
        if self.workspace and hasattr(self.workspace, 'filter_engine'):
            self.workspace.filter_engine.build_dropdown_ui(self.facility_dropdown_container)

        # 2. Populate Status Overlays (StatusManager)
        if self.workspace and hasattr(self.workspace, 'status_manager'):
            # Categories match your CSV naming convention
            status_cats = ["churches", "drrm", "firestations", "hospitals", "schools", "policestations"]
            self.workspace.status_manager.build_dropdown_ui(self.status_dropdown_container, status_cats)

    def open_routing(self):
        """Triggered by the Route Facilities button."""
        if self.workspace and hasattr(self.workspace, 'routing_engine'):
            # Passes all_data to the routing window for processing
            self.workspace.routing_engine.open_route_window(self.workspace.all_data)