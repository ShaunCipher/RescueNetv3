import customtkinter as ctk
import os
import csv
from src.components.core.merge_sort import merge_sort, sort_facilities_by_distance

class LeftPanel(ctk.CTkFrame):
    def __init__(self, master, toggle_cmd, workspace=None, **kwargs):
        super().__init__(master, width=250, corner_radius=0, fg_color="#2b2b2b", **kwargs)
        self.workspace = workspace
        
        # Use relative path from project root
        self.base_dir = self.get_root_path()
        self.data_dir = os.path.join(self.base_dir, "data")
        
        print(f"DEBUG: Looking for CSVs in: {self.data_dir}")
        
        self.node_map = self.load_nodes("nodes.csv")

        # --- 1. CLOSE BUTTON ---
        self.close_btn = ctk.CTkButton(
            self, text="<", width=20, height=60,
            fg_color="#3d3d3d", command=toggle_cmd
        )
        self.close_btn.place(relx=1.0, rely=0.5, anchor="e")

        # --- 2. FACILITY VISIBILITY SECTION ---
        self.facility_section = ctk.CTkFrame(self, fg_color="transparent")
        self.facility_section.pack(fill="x", padx=10, pady=(20, 5))

        self.facility_toggle_btn = ctk.CTkButton(
            self.facility_section, text="▼ Facility Visibility",
            height=35, fg_color="#3d3d3d", hover_color="#4d4d4d",
            anchor="w", command=self.toggle_facility_menu
        )
        self.facility_toggle_btn.pack(fill="x")

        self.facility_dropdown_container = ctk.CTkFrame(self.facility_section, fg_color="#333333")
        self.facility_dropdown_container.pack(fill="x", pady=(5, 0))
        self.is_facility_open = True

        # --- 3. STATUS OVERLAYS SECTION ---
        self.status_section = ctk.CTkFrame(self, fg_color="transparent")
        self.status_section.pack(fill="x", padx=10, pady=5)

        self.status_toggle_btn = ctk.CTkButton(
            self.status_section, text="▶ Check Facility Status",
            height=35, fg_color="#3d3d3d", hover_color="#4d4d4d",
            anchor="w", command=self.toggle_status_menu
        )
        self.status_toggle_btn.pack(fill="x")

        self.status_dropdown_container = ctk.CTkFrame(self.status_section, fg_color="#333333")
        self.is_status_open = False

        # --- 4. ACTIONS SECTION (Modified) ---
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=10, pady=20)

        
        # ---------------------------

        # Existing Sort Button
        self.sort_btn = ctk.CTkButton(
            self.action_frame, text="Sort Facilities (Merge Sort)", 
            height=40, fg_color="#28a745", hover_color="#218838",
            command=self.open_sorted_view
        )
        self.sort_btn.pack(fill="x", padx=10, pady=(0, 10))

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
        if self.is_facility_open:
            self.facility_dropdown_container.pack_forget()
            self.facility_toggle_btn.configure(text="▶ Facility Visibility")
        else:
            self.facility_dropdown_container.pack(fill="x", pady=(5, 0))
            self.facility_toggle_btn.configure(text="▼ Facility Visibility")

        self.is_facility_open = not self.is_facility_open



    def toggle_status_menu(self):
        if self.is_status_open:
            self.status_dropdown_container.pack_forget()
            self.status_toggle_btn.configure(text="▶ Check Facility Status")
        else:
            self.status_dropdown_container.pack(fill="x", pady=(5, 0))
            self.status_toggle_btn.configure(text="▼ Check Facility Status")
        self.is_status_open = not self.is_status_open



    # --- INITIALIZATION ---

    def setup_filters(self):
        if self.workspace and hasattr(self.workspace, 'filter_engine'):
            self.workspace.filter_engine.build_dropdown_ui(self.facility_dropdown_container)

        if self.workspace and hasattr(self.workspace, 'status_manager'):
            status_cats = ["churches", "drrm", "firestations", "hospitals", "schools", "policestations"]
            self.workspace.status_manager.build_dropdown_ui(self.status_dropdown_container, status_cats)



    def get_root_path(self):
        """Returns the root directory of your repository."""
        # This gets the directory of left_panel.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # This goes up two levels to reach the project root
        return os.path.abspath(os.path.join(current_dir, '..', '..'))

    def load_nodes(self, filename):
        """Loads nodes.csv and forces the ID to be a string."""
        coords = {}
        file_path = os.path.join(self.data_dir, filename)
        
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Explicitly convert the ID to a string to match registry keys
                    node_id = str(row['id']).strip() 
                    coords[node_id] = (float(row['x']), float(row['y']))
        except FileNotFoundError:
            print(f"CRITICAL: Cannot find {filename} at {file_path}")
        return coords

    def get_accident_coordinates(self):
        """Helper to get coordinates of the currently selected accident."""
        active_id = getattr(self.workspace, 'current_accident_id', None)
        if active_id and str(active_id) in self.node_map:
            return self.node_map[str(active_id)]
        return (0, 0)  # Default if no accident selected

    def open_accident_selection(self, parent_popup):
        """Opens a window to select an accident from accidents.csv."""
        selector = ctk.CTkToplevel(parent_popup)
        selector.title("Pick an Accident")
        selector.geometry("300x400")
        
        scroll = ctk.CTkScrollableFrame(selector, width=260, height=300)
        scroll.pack(padx=10, pady=10)

        # Uses the same base_path strategy
        file_path = os.path.join(self.data_dir, "accidents.csv")
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    btn = ctk.CTkButton(
                        scroll, text=f"ID: {row['id']} - {row['name']}",
                        command=lambda r=row: self.perform_sort(r['id'], selector)
                    )
                    btn.pack(fill="x", pady=2)
        except FileNotFoundError:
            ctk.CTkLabel(scroll, text="accidents.csv not found").pack()

    def perform_sort(self, acc_id, selector_popup):
        """Performs the merge sort and updates the results window, grouped by category."""
        self.workspace.current_accident_id = acc_id
        selector_popup.destroy()

        # 1. Double check that self.results_scroll exists
        if not hasattr(self, 'results_scroll'):
            print("Error: Results window not initialized.")
            return

        # 2. Clear previous results
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        # 3. Get the accident location and sort facilities
        accident_coords = self.get_accident_coordinates()
        facilities_by_category = sort_facilities_by_distance(
            self.workspace.master_registry,
            self.node_map,
            accident_coords
        )

        # 4. Display sorted facilities with headings
        for category in sorted(facilities_by_category.keys()):
            sorted_facilities = facilities_by_category[category]

            # Add category header
            header = ctk.CTkLabel(
                self.results_scroll,
                text=f"━━ {category.upper()} ━━",
                text_color="#d35400",
                font=("Arial", 12, "bold"),
                anchor="w"
            )
            header.pack(fill="x", padx=10, pady=(15, 5))

            # Add facilities under this category
            for i, facility in enumerate(sorted_facilities):
                name = facility.get('name', 'Unknown')
                distance = facility.get('distance', 0)
                info = f"  {i+1}. {name} — {distance} km"
                ctk.CTkLabel(self.results_scroll, text=info, anchor="w").pack(fill="x", padx=10, pady=2)

    def set_accident(self, acc_id, popup):
        """Saves selected accident ID to workspace and closes popup."""
        if self.workspace:
            self.workspace.current_accident_id = acc_id
            print(f"Selected Accident: {acc_id}")
        popup.destroy()

    def open_sorted_view(self):
        """Initializes the window with a selection button."""
        if not self.workspace or not hasattr(self.workspace, 'master_registry'):
            return

        popup = ctk.CTkToplevel(self)
        popup.title("Facilities Sorted by Distance")
        popup.geometry("500x550")
        
        ctk.CTkLabel(popup, text="Sort Facilities (Merge Sort)", font=("Arial", 18, "bold")).pack(pady=10)

        # Button to trigger the accident selection popup
        select_acc_btn = ctk.CTkButton(
            popup, text="Select Accident", height=35,
            fg_color="#d35400", hover_color="#a04000",
            command=lambda: self.open_accident_selection(popup)
        )
        select_acc_btn.pack(pady=10)

        # This will hold the results after the user picks an accident
        self.results_scroll = ctk.CTkScrollableFrame(popup, width=460, height=400)
        self.results_scroll.pack(padx=20, pady=10, fill="both", expand=True)



    def open_routing(self):

        if self.workspace and hasattr(self.workspace, 'routing_engine'):

            self.workspace.routing_engine.open_route_window(self.workspace.all_data)

