import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

class RightPanel(ctk.CTkFrame):
    def __init__(self, master, toggle_cmd, accident_manager, **kwargs):
        # Increased default width to 320 for better table readability
        super().__init__(master, width=320, corner_radius=0, fg_color="#2b2b2b", **kwargs)
        
        self.acc_mgr = accident_manager
        self.toggle_cmd = toggle_cmd
        
        # 1. Close/Toggle Button (The Tab)
        self.close_btn = ctk.CTkButton(
            self, text=">", width=20, height=60, 
            fg_color="#3d3d3d", hover_color="#4d4d4d", command=toggle_cmd
        )
        self.close_btn.place(relx=0.0, rely=0.5, anchor="w")

        # 2. Main Scrollable Container (To hold everything)
        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=(25, 5), pady=10)

        # 3. Header
        ctk.CTkLabel(self.container, text="COMMAND CENTER", font=("Arial", 16, "bold"), text_color="#3498db").pack(pady=(10, 20))

        # --- SECTION: VISIBILITY CONTROLS ---
        self.setup_visibility_section()

        # --- SECTION: REPORTING FORM ---
        self.setup_reporting_section()

        # --- SECTION: DISPATCHER ---
        self.setup_dispatch_section()

    def setup_visibility_section(self):
        """Toggle for Accident Node Visibility"""
        v_frame = ctk.CTkFrame(self.container, fg_color="#333333")
        v_frame.pack(fill="x", pady=5)
        
        self.show_acc_var = tk.BooleanVar(value=True)
        self.vis_switch = ctk.CTkSwitch(
            v_frame, text="Show Accidents", 
            variable=self.show_acc_var,
            command=self.toggle_accident_visibility,
            progress_color="#e74c3c"
        )
        self.vis_switch.pack(pady=10, padx=10)

    def setup_reporting_section(self):
        """Inputs for reporting a new accident"""
        label_font = ("Arial", 12, "bold")
        ctk.CTkLabel(self.container, text="NEW INCIDENT", font=label_font).pack(pady=(20, 10))

        # Location Picker
        self.loc_btn = ctk.CTkButton(
            self.container, text="📍 Pick Map Location", 
            fg_color="#e67e22", hover_color="#d35400",
            command=self.acc_mgr.activate_map_picker
        )
        self.loc_btn.pack(pady=5, fill="x", padx=10)
        
        # We re-link the Manager's label reference to this new one
        self.acc_mgr.loc_label = ctk.CTkLabel(self.container, text="Location: None", font=("Arial", 10, "italic"))
        self.acc_mgr.loc_label.pack()

        # Fields (Connecting manager variables to RightPanel widgets)
        self.acc_mgr.name_entry = self.create_input("Incident Name:")
        self.acc_mgr.victims_entry = self.create_input("Number of Victims:")

        # Severity
        ctk.CTkLabel(self.container, text="Severity Level:").pack(anchor="w", padx=10)
        self.acc_mgr.severity_var = ctk.StringVar(value="Minor")
        ctk.CTkSegmentedButton(
            self.container, values=["Minor", "Moderate", "Critical"], 
            variable=self.acc_mgr.severity_var
        ).pack(fill="x", padx=10, pady=5)

        # Checklist
        ctk.CTkLabel(self.container, text="Resources Needed:").pack(anchor="w", padx=10, pady=(10, 0))
        cb_frame = ctk.CTkFrame(self.container, fg_color="#333333")
        cb_frame.pack(fill="x", padx=10, pady=5)

        self.acc_mgr.need_medical = ctk.CTkCheckBox(cb_frame, text="Medical (Hospital)", font=("Arial", 11))
        self.acc_mgr.need_police = ctk.CTkCheckBox(cb_frame, text="Police Assistance", font=("Arial", 11))
        self.acc_mgr.need_firestation = ctk.CTkCheckBox(cb_frame, text="Fire Station", font=("Arial", 11))
        self.acc_mgr.need_evac = ctk.CTkCheckBox(cb_frame, text="Evacuation Center", font=("Arial", 11))
        
        # Link references so the manager can check states
        self.acc_mgr.checkboxes = [
            self.acc_mgr.need_medical, self.acc_mgr.need_police, 
            self.acc_mgr.need_firestation, self.acc_mgr.need_evac
        ]
        for cb in self.acc_mgr.checkboxes: cb.pack(anchor="w", padx=10, pady=3)

        # Submission Button
        ctk.CTkButton(
            self.container, text="Submit Report", 
            fg_color="#27ae60", hover_color="#219150",
            command=self.acc_mgr.process_submission
        ) .pack(pady=15, fill="x", padx=10)

    def setup_dispatch_section(self):
        ctk.CTkLabel(self.container, text="ACTIVE INCIDENTS", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        
        # 1. Create the Treeview (The 'Table')
        cols = ("ID", "Name", "Severity", "Victims", "Status", "Needs")
        # LINK IT TO THE MANAGER HERE:
        self.acc_mgr.tree = ttk.Treeview(self.container, columns=cols, show="headings", height=5)
        
        for col in cols: 
            self.acc_mgr.tree.heading(col, text=col)
            self.acc_mgr.tree.column(col, width=50) # Keep it narrow for sidebar
        self.acc_mgr.tree.pack(fill="x", padx=10, pady=5)

        # 2. Add the Dropdown
        ctk.CTkLabel(self.container, text="Select to Dispatch:", font=("Arial", 11)).pack(pady=(10,0))
        self.acc_mgr.acc_dropdown = ctk.CTkComboBox(
            self.container, 
            values=["Select Accident..."],
            command=self.acc_mgr.on_accident_selected, 
            width=250
        )
        self.acc_mgr.acc_dropdown.pack(pady=5, padx=10)
        
        # 3. Trigger initial data load so the list appears immediately
        self.acc_mgr.refresh_table()

    def create_input(self, label_text):
        """Helper to create labeled entry fields"""
        ctk.CTkLabel(self.container, text=label_text).pack(anchor="w", padx=10)
        entry = ctk.CTkEntry(self.container)
        entry.pack(fill="x", padx=10, pady=(0, 10))
        return entry

    def toggle_accident_visibility(self):
        """Hides or shows the red X markers on the map."""
        visible = self.show_acc_var.get()
        
        # If the list is empty, try to redraw them first
        if not self.acc_mgr.acc_plots:
            self.acc_mgr.draw_accidents_on_map()
            
        for plot in self.acc_mgr.acc_plots:
            plot.set_visible(visible)
            
        self.acc_mgr.fig.canvas.draw_idle()