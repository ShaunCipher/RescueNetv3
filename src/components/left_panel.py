import customtkinter as ctk

class LeftPanel(ctk.CTkFrame):
    def __init__(self, master, toggle_cmd, workspace=None, **kwargs):
        super().__init__(master, width=250, corner_radius=0, fg_color="#2b2b2b", **kwargs)
        self.workspace = workspace
        
        # --- 1. CLOSE BUTTON ---
        self.close_btn = ctk.CTkButton(
            self, text="<", width=20, height=60, 
            fg_color="#3d3d3d", command=toggle_cmd
        )
        self.close_btn.place(relx=1.0, rely=0.5, anchor="e")
        
        # --- 2. FACILITY FILTER SECTION ---
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=10, pady=(20, 10))
        
        ctk.CTkLabel(
            self.filter_frame, text="FACILITIES", 
            font=("Arial", 11, "bold"), text_color="gray"
        ).pack(anchor="w", padx=10, pady=(0, 5))

        self.checkbox_container = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
        self.checkbox_container.pack(fill="x")

        # --- 3. STATUS DROPDOWN SECTION ---
        self.status_section = ctk.CTkFrame(self, fg_color="transparent")
        self.status_section.pack(fill="x", padx=10, pady=10)

        # The Dropdown Toggle Button
        self.status_toggle_btn = ctk.CTkButton(
            self.status_section, 
            text="▼ Check Facility Status", 
            height=35,
            fg_color="#3d3d3d",
            hover_color="#4d4d4d",
            anchor="w",
            command=self.toggle_status_menu
        )
        self.status_toggle_btn.pack(fill="x")

        # The actual container that will show/hide (initially empty)
        self.status_dropdown_container = ctk.CTkFrame(self.status_section, fg_color="#333333")
        self.is_dropdown_open = False

        # --- 4. ACTIONS SECTION ---
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=10, pady=20)

        self.route_btn = ctk.CTkButton(
            self.action_frame, 
            text="Route facilities", 
            height=40,
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.open_routing
        )
        self.route_btn.pack(fill="x", padx=10)

    def toggle_status_menu(self):
        """Toggles the visibility of the status checkboxes."""
        if self.is_dropdown_open:
            self.status_dropdown_container.pack_forget()
            self.status_toggle_btn.configure(text="▶ Check Facility Status")
        else:
            self.status_dropdown_container.pack(fill="x", pady=(5, 0))
            self.status_toggle_btn.configure(text="▼ Check Facility Status")
        
        self.is_dropdown_open = not self.is_dropdown_open

    def setup_filters(self):
        """Initializes both facility filters and the status dropdown."""
        # 1. Clear existing for re-runs
        for widget in self.checkbox_container.winfo_children():
            widget.destroy()
        for widget in self.status_dropdown_container.winfo_children():
            widget.destroy()

        # 2. Build Facility Filters (your existing logic)
        if self.workspace and hasattr(self.workspace, 'filter_engine'):
            self.workspace.filter_engine.build_filter_ui(self.checkbox_container)

        # 3. Build Status Dropdown (your updated StatusManager)
        if self.workspace and hasattr(self.workspace, 'status_manager'):
            categories = ["churches", "drrm", "firestations", "hospitals", "schools", "policestations"]
            self.workspace.status_manager.build_dropdown_ui(self.status_dropdown_container, categories)

    def open_routing(self):
        if self.workspace and hasattr(self.workspace, 'routing_engine'):
            self.workspace.routing_engine.open_route_window(self.workspace.all_data)