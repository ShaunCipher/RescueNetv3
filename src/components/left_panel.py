import sys
import os

# Fix import path for src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

from src.components.core.binary_search import find_by_distance
from src.components.core.merge_sort import sort_facilities_by_distance


class LeftPanel(ctk.CTkFrame):

    def __init__(self, master, toggle_cmd, workspace=None, **kwargs):
        super().__init__(master, width=250, corner_radius=0, fg_color="#2b2b2b", **kwargs)

        self.workspace = workspace

        # --- CLOSE BUTTON ---
        self.close_btn = ctk.CTkButton(
            self,
            text="<",
            width=20,
            height=60,
            fg_color="#3d3d3d",
            command=toggle_cmd
        )
        self.close_btn.place(relx=1.0, rely=0.5, anchor="e")

        # ---------------------------
        # FACILITY VISIBILITY
        # ---------------------------

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

        self.facility_dropdown_container = ctk.CTkFrame(
            self.facility_section,
            fg_color="#333333"
        )
        self.facility_dropdown_container.pack(fill="x", pady=(5, 0))

        self.is_facility_open = True

        # ---------------------------
        # STATUS SECTION
        # ---------------------------

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

        self.status_dropdown_container = ctk.CTkFrame(
            self.status_section,
            fg_color="#333333"
        )

        self.is_status_open = False

        # ---------------------------
        # ACTION BUTTONS
        # ---------------------------

        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=10, pady=20)

        # NEW BUTTON (Binary Search)
        self.binary_btn = ctk.CTkButton(
            self.action_frame,
            text="Sort Facilities (Binary Search)",
            height=40,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self.open_binary_search
        )
        self.binary_btn.pack(fill="x", padx=10, pady=(0, 10))

        # Merge Sort Button
        self.sort_btn = ctk.CTkButton(
            self.action_frame,
            text="Sort Facilities (Merge Sort)",
            height=40,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self.open_merge_sort
        )
        self.sort_btn.pack(fill="x", padx=10, pady=(0, 10))

        # Routing Button
        self.route_btn = ctk.CTkButton(
            self.action_frame,
            text="Route Facilities",
            height=40,
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.open_routing
        )
        self.route_btn.pack(fill="x", padx=10)

    # ---------------------------
    # DROPDOWN TOGGLES
    # ---------------------------

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

    # ---------------------------
    # SETUP FILTERS
    # ---------------------------

    def setup_filters(self):

        if self.workspace and hasattr(self.workspace, "filter_engine"):
            self.workspace.filter_engine.build_dropdown_ui(
                self.facility_dropdown_container
            )

        if self.workspace and hasattr(self.workspace, "status_manager"):

            status_cats = [
                "churches",
                "drrm",
                "firestations",
                "hospitals",
                "schools",
                "policestations"
            ]

            self.workspace.status_manager.build_dropdown_ui(
                self.status_dropdown_container,
                status_cats
            )

    # ---------------------------
    # ROUTING
    # ---------------------------

    def open_routing(self):

        if self.workspace and hasattr(self.workspace, "routing_engine"):

            self.workspace.routing_engine.open_route_window(
                self.workspace.all_data
            )

    # ---------------------------
    # BINARY SEARCH POPUP
    # ---------------------------

    def open_binary_search(self):

        popup = ctk.CTkToplevel(self)
        popup.title("Binary Search Facility")
        popup.geometry("400x250")

        label = ctk.CTkLabel(
            popup,
            text="Enter distance (km) to search:"
        )
        label.pack(pady=10)

        entry = ctk.CTkEntry(popup)
        entry.pack(pady=10)

        result_label = ctk.CTkLabel(popup, text="")
        result_label.pack(pady=10)

        search_btn = ctk.CTkButton(
            popup,
            text="Search",
            command=lambda: self.run_binary_search(entry.get(), result_label)
        )
        search_btn.pack(pady=10)

    def run_binary_search(self, value, result_label):

        accident_coords = None

        if self.workspace and hasattr(self.workspace, "report_manager"):
            accident_coords = getattr(
                self.workspace.report_manager,
                "selected_coords",
                None
            )

        if not accident_coords:

            messagebox.showwarning(
                "Missing Location",
                "Please pick an accident location on the map first."
            )
            return

        try:
            target_distance = float(value)

        except ValueError:
            result_label.configure(text="Invalid distance")
            return

        facility, sorted_list = find_by_distance(
            self.workspace.master_registry,
            self.workspace.nodes,
            accident_coords,
            round(target_distance, 2)
        )

        if facility:

            result_label.configure(
                text=f"Found: {facility.get('name','Unknown')} ({facility.get('distance')} km)"
            )

        else:

            result_label.configure(
                text="No facility found for that distance."
            )

    # ---------------------------
    # MERGE SORT DISPLAY
    # ---------------------------

    def open_merge_sort(self):

        accident_coords = None

        if self.workspace and hasattr(self.workspace, "report_manager"):
            accident_coords = getattr(
                self.workspace.report_manager,
                "selected_coords",
                None
            )

        if not accident_coords:

            messagebox.showwarning(
                "Missing Location",
                "Please pick an accident location first."
            )
            return

        if not (
            self.workspace
            and hasattr(self.workspace, "master_registry")
            and hasattr(self.workspace, "nodes")
        ):

            messagebox.showwarning(
                "Workspace Error",
                "Workspace data is not ready."
            )
            return

        sorted_by_category = sort_facilities_by_distance(
            self.workspace.master_registry,
            self.workspace.nodes,
            accident_coords
        )

        popup = ctk.CTkToplevel(self)
        popup.title("Sorted Facilities by Distance")
        popup.geometry("520x520")

        out_text = ctk.CTkTextbox(popup, width=500, height=480)
        out_text.pack(padx=10, pady=10)

        out_text.configure(state="normal")

        for cat, facs in sorted_by_category.items():

            out_text.insert(
                "end",
                f"== {cat.upper()} (count={len(facs)}) ==\n"
            )

            for f in facs[:15]:

                out_text.insert(
                    "end",
                    f"{f.get('name','Unknown')} — {f.get('distance')} km\n"
                )

            out_text.insert("end", "\n")

        out_text.configure(state="disabled")