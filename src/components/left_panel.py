import customtkinter as ctk
import os
import csv
from src.components.core.merge_sort import merge_sort, sort_facilities_by_distance
from .network_editor import NetworkEditor
from src.components.core.binary_search import find_by_distance  # New Import

class LeftPanel(ctk.CTkFrame):
    def __init__(self, master, toggle_cmd, workspace=None, **kwargs):
        super().__init__(master, width=250, corner_radius=0, fg_color="#2b2b2b", **kwargs)
        self.workspace = workspace
        
        # Use relative path from project root
        self.base_dir = self.get_root_path()
        self.data_dir = os.path.join(self.base_dir, "data")
        
        print(f"DEBUG: Looking for CSVs in: {self.data_dir}")
        
        self.node_map = self.load_nodes("nodes.csv")
        self.accident_data = self.load_accidents("accidents.csv")

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

        # Existing Sort Button
        self.sort_btn = ctk.CTkButton(
            self.action_frame, text="🔍 Find Nearest Facilities", 
            height=40, fg_color="#28a745", hover_color="#218838",
            command=self.open_sorted_view
        )
        self.sort_btn.pack(fill="x", padx=10, pady=(0, 10))

        # NEW: Binary Search Button
        self.search_btn = ctk.CTkButton(
            self.action_frame,
            text="🔍 Target Search",
            height=40,
            fg_color="#6f42c1",
            hover_color="#59359a",
            command=self.open_binary_search_view
        )
        self.search_btn.pack(fill="x", padx=10, pady=(0, 10))

        # Existing Route Button
        self.route_btn = ctk.CTkButton(
            self.action_frame,
            text="Route Facilities",
            height=40,
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.open_routing
        )
        self.route_btn.pack(fill="x", padx=10, pady=(0, 10))

        # Existing Road Network Editor Button
        self.editor_btn = ctk.CTkButton(
            self.action_frame,
            text="🛠️ Edit Road Network",
            height=40,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a",
            command=self.open_network_editor
        )
        self.editor_btn.pack(fill="x", padx=10)

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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(current_dir, '..', '..'))

    def load_nodes(self, filename):
        """Loads nodes.csv and forces the ID to be a string."""
        coords = {}
        file_path = os.path.join(self.data_dir, filename)
        
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    node_id = str(row['id']).strip() 
                    coords[node_id] = (float(row['x']), float(row['y']))
        except FileNotFoundError:
            print(f"CRITICAL: Cannot find {filename} at {file_path}")
        return coords

    def load_accidents(self, filename):
        """Loads accidents.csv and returns a dict keyed by ID."""
        accidents = {}
        file_path = os.path.join(self.data_dir, filename)
        
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    acc_id = str(row['id']).strip()
                    accidents[acc_id] = row
        except FileNotFoundError:
            print(f"CRITICAL: Cannot find {filename} at {file_path}")
        return accidents

    def get_accident_coordinates(self):
        """Helper to get coordinates of the currently selected accident."""
        active_id = getattr(self.workspace, 'current_accident_id', None)
        if active_id and str(active_id) in self.node_map:
            return self.node_map[str(active_id)]
        return (0, 0)

    def open_accident_selection(self, parent_popup):
        """Opens a window to select an accident from accidents.csv."""
        selector = ctk.CTkToplevel(parent_popup)
        selector.title("Pick an Accident")
        selector.geometry("300x400")

        selector.transient(parent_popup)
        selector.grab_set()
        selector.attributes("-topmost", True)
        selector.focus_force()
        selector.lift()

        scroll = ctk.CTkScrollableFrame(selector, width=260, height=300)
        scroll.pack(padx=10, pady=10)

        file_path = os.path.join(self.data_dir, "accidents.csv")
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    btn = ctk.CTkButton(
                        scroll, text=f"ID: {row['id']} - {row['name']}",
                        command=lambda r=row: (self.perform_sort(r['id']), selector.destroy())
                    )
                    btn.pack(fill="x", pady=2)
        except FileNotFoundError:
            ctk.CTkLabel(scroll, text="accidents.csv not found").pack()

    def perform_sort(self, acc_id, selector_popup=None):
        if not acc_id:
            return
        self.workspace.current_accident_id = acc_id

        if not hasattr(self, 'results_scroll'):
            print("Error: Results window not initialized.")
            return

        accident_coords = self.get_accident_coordinates()
        edges_df = None
        if self.workspace and hasattr(self.workspace, 'data_engine'):
            edges_df = self.workspace.data_engine.edges_df
        
        facilities_by_category = sort_facilities_by_distance(
            self.workspace.master_registry,
            self.node_map,
            accident_coords,
            edges_df,
            accident_node_id=acc_id
        )

        if "Unknown" in facilities_by_category:
            del facilities_by_category["Unknown"]

        self.current_categorized_facilities = facilities_by_category
        self.current_flattened_facilities = self._flatten_and_sort_facilities(facilities_by_category)
        self.current_accident_id = acc_id
        self.current_accident_data = self.accident_data.get(str(acc_id), {})

        self._update_filter_dropdown(facilities_by_category)
        self._update_results_display()

    def _flatten_and_sort_facilities(self, facilities_by_category):
        flattened = []
        for category, facilities in facilities_by_category.items():
            flattened.extend(facilities)
        flattened.sort(key=lambda f: float(f.get('distance', 0)))
        return flattened

    def _update_filter_dropdown(self, facilities_by_category):
        categories = sorted(facilities_by_category.keys())
        filter_options = ["All (Categorized)", "All (Uncategorized)"] + categories
        self.filter_dropdown.configure(values=filter_options)
        self.filter_dropdown.set("All (Categorized)")
        self.current_filter_mode = "All"

    def _update_results_display(self):
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        filter_mode = getattr(self, 'current_filter_mode', 'All')
        acc_row = self.current_accident_data
        accident_name = acc_row.get('name', 'Unknown Accident')
        acc_id = self.current_accident_id

        needs = []
        if acc_row.get('need_medical') in ('1', 'True', 'true'): needs.append('Medical')
        if acc_row.get('need_police') in ('1', 'True', 'true'): needs.append('Police')
        if acc_row.get('need_firestation') in ('1', 'True', 'true'): needs.append('Firestation')
        if acc_row.get('need_evac') in ('1', 'True', 'true'): needs.append('Evacuation')
        needs_text = ', '.join(needs) if needs else 'None'

        header_label = ctk.CTkLabel(
            self.results_scroll,
            text=f"Accident: {accident_name} (ID {acc_id}) | Needs: {needs_text}",
            text_color="#e74c3c",
            font=("Arial", 14, "bold"),
            anchor="w"
        )
        header_label.pack(fill="x", padx=10, pady=(5, 10))

        if filter_mode == 'All':
            for category in sorted(self.current_categorized_facilities.keys()):
                sorted_facilities = self.current_categorized_facilities[category]
                header = ctk.CTkLabel(self.results_scroll, text=f"━━ {category.upper()} ━━", text_color="#d35400", font=("Arial", 12, "bold"), anchor="w")
                header.pack(fill="x", padx=10, pady=(15, 5))
                for i, facility in enumerate(sorted_facilities):
                    info = f"  {i+1}. {facility.get('name', 'Unknown')} — {facility.get('distance', 0)} km"
                    ctk.CTkLabel(self.results_scroll, text=info, anchor="w").pack(fill="x", padx=10, pady=2)
        elif filter_mode == 'Uncategorized':
            for i, facility in enumerate(self.current_flattened_facilities):
                info = f"{i+1}. {facility.get('name', 'Unknown')} — {facility.get('distance', 0)} km"
                ctk.CTkLabel(self.results_scroll, text=info, anchor="w").pack(fill="x", padx=10, pady=2)
        else:
            if filter_mode in self.current_categorized_facilities:
                sorted_facilities = self.current_categorized_facilities[filter_mode]
                header = ctk.CTkLabel(self.results_scroll, text=f"━━ {filter_mode.upper()} ━━", text_color="#d35400", font=("Arial", 12, "bold"), anchor="w")
                header.pack(fill="x", padx=10, pady=(15, 5))
                for i, facility in enumerate(sorted_facilities):
                    info = f"  {i+1}. {facility.get('name', '')} — {facility.get('distance', 0)} km"
                    ctk.CTkLabel(self.results_scroll, text=info, anchor="w").pack(fill="x", padx=10, pady=2)

    def set_accident(self, acc_id, popup):
        if self.workspace:
            self.workspace.current_accident_id = acc_id
        popup.destroy()

    def open_sorted_view(self):
        if not self.workspace or not hasattr(self.workspace, 'master_registry'):
            return

        if hasattr(self, 'sorted_view_window') and self.sorted_view_window.winfo_exists():
            self.sorted_view_window.focus_force()
            self.sorted_view_window.lift()
            return

        popup = ctk.CTkToplevel(self)
        popup.title("Facilities Sorted by Distance")
        popup.geometry("500x550")
        popup.attributes("-topmost", True)
        popup.focus_force()
        popup.lift()
        
        self.sorted_view_window = popup
        
        ctk.CTkLabel(popup, text="Sort Facilities (Merge Sort)", font=("Arial", 18, "bold")).pack(pady=10)

        self.dropdown_map = {}
        display_values = []
        for aid, row in self.accident_data.items():
            label = f"{aid} - {row.get('name','') }"
            display_values.append(label)
            self.dropdown_map[label] = aid

        self.accident_dropdown = ctk.CTkComboBox(
            popup,
            values=display_values,
            width=350,
            command=lambda sel: self.perform_sort(self.dropdown_map.get(sel, ''))
        )
        self.accident_dropdown.set("") 
        self.accident_dropdown.pack(pady=10)

        filter_label = ctk.CTkLabel(popup, text="Filter View:", font=("Arial", 12))
        filter_label.pack(pady=(10, 5))

        self.current_filter_mode = "All"
        self.filter_dropdown = ctk.CTkComboBox(
            popup,
            values=["All (Categorized)", "All (Uncategorized)"],
            width=350,
            command=self._on_filter_change
        )
        self.filter_dropdown.set("") 
        self.filter_dropdown.pack(pady=(5, 10))

        self.results_scroll = ctk.CTkScrollableFrame(popup, width=460, height=400)
        self.results_scroll.pack(padx=20, pady=10, fill="both", expand=True)

    def _on_filter_change(self, selection):
        if selection == "All (Categorized)":
            self.current_filter_mode = "All"
        elif selection == "All (Uncategorized)":
            self.current_filter_mode = "Uncategorized"
        else:
            self.current_filter_mode = selection
        
        if hasattr(self, 'current_categorized_facilities'):
            self._update_results_display()

    def open_routing(self):
        if self.workspace and hasattr(self.workspace, 'routing_engine'):
            if hasattr(self, 'routing_window') and self.routing_window.winfo_exists():
                self.routing_window.focus_force()
                self.routing_window.lift()
                return
            self.routing_window = self.workspace.routing_engine.open_route_window(self.workspace.all_data)

    def open_network_editor(self):
        if hasattr(self, 'editor_window') and self.editor_window.winfo_exists():
            self.editor_window.focus_force()
        else:
            self.editor_window = NetworkEditor(self.master, workspace=self.workspace)
            self.editor_window.grab_set()

    # --- BINARY SEARCH IMPLEMENTATION ---

    def open_binary_search_view(self):
        """Opens a window to perform binary search for a specific distance."""
        if not self.workspace: return

        popup = ctk.CTkToplevel(self)
        popup.title("Binary Search: Find by Distance")
        popup.geometry("450x500")
        popup.attributes("-topmost", True)
        
        ctk.CTkLabel(popup, text="Binary Search Facility", font=("Arial", 18, "bold")).pack(pady=10)

        # 1. Accident Selection
        ctk.CTkLabel(popup, text="1. Select Accident Location:").pack(pady=(10, 0))
        display_values = [f"{aid} - {row.get('name','')}" for aid, row in self.accident_data.items()]
        acc_dropdown = ctk.CTkComboBox(popup, values=display_values, width=300)
        acc_dropdown.pack(pady=5)

        # 2. Distance Input
        ctk.CTkLabel(popup, text="2. Enter Target Distance (km):").pack(pady=(10, 0))
        dist_entry = ctk.CTkEntry(popup, placeholder_text="e.g. 1.45", width=200)
        dist_entry.pack(pady=5)

        # 3. Results Area
        res_frame = ctk.CTkScrollableFrame(popup, width=400, height=200)
        
        def run_search():
            for widget in res_frame.winfo_children(): widget.destroy()
            try:
                selection = acc_dropdown.get()
                if not selection: return
                acc_id = selection.split(" - ")[0]
                target_dist = float(dist_entry.get())
                acc_coords = self.node_map.get(str(acc_id))
                
                match, all_sorted = find_by_distance(
                    self.workspace.master_registry,
                    self.node_map,
                    acc_coords,
                    target_dist
                )

                if match:
                    ctk.CTkLabel(res_frame, text="MATCH FOUND!", text_color="#28a745", font=("Arial", 12, "bold")).pack()
                    info = f"Name: {match.get('name')}\nCategory: {match.get('category', 'N/A')}\nDistance: {match.get('distance')} km"
                    ctk.CTkLabel(res_frame, text=info, justify="left").pack(pady=10)
                else:
                    ctk.CTkLabel(res_frame, text="No exact match found.", text_color="#e74c3c").pack()
                    ctk.CTkLabel(res_frame, text="Closest facilities:", font=("Arial", 11, "italic")).pack(pady=5)
                    for f in all_sorted[:5]:
                        ctk.CTkLabel(res_frame, text=f"{f.get('name')} ({f.get('distance')} km)", font=("Arial", 10)).pack()
            except ValueError:
                ctk.CTkLabel(res_frame, text="Error: Please enter a valid number", text_color="red").pack()

        ctk.CTkButton(popup, text="Execute Binary Search", command=run_search).pack(pady=15)
        res_frame.pack(padx=20, pady=10, fill="both", expand=True)