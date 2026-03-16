import customtkinter as ctk
import csv
import os
import pandas as pd
from tkinter import messagebox
from .path_utils import get_data_dir


CATEGORY_OPTIONS = ["Hospital", "DRRM", "Firestation", "Policestation", "Church", "School"]
CATEGORY_PLACEHOLDER = "Select Category"


FACILITY_FILE_MAP = {
    "Hospital": "hospitals.csv",
    "DRRM": "drrm.csv",
    "Firestation": "firestations.csv",
    "Policestation": "policestations.csv",
    "Church": "churches.csv",
    "School": "schools.csv",
}

FACILITY_FIELD_MAP = {
    "Hospital": ['id', 'name', 'category', 'capacity', 'occupants', 'operating_hours', 'status', 'is_open'],
    "Church": ['id', 'name', 'category', 'capacity', 'occupants', 'operating_hours', 'status', 'is_open'],
    "School": ['id', 'name', 'category', 'capacity', 'occupants', 'operating_hours', 'status', 'is_open'],
    "DRRM": ['id', 'name', 'category', 'number_of_staff', 'staff_present', 'status', 'is_open'],
    "Firestation": ['id', 'name', 'category', 'number_of_staff', 'staff_present', 'status', 'is_open'],
    "Policestation": ['id', 'name', 'category', 'number_of_staff', 'staff_present', 'status', 'is_open'],
}

DEFAULT_OPERATING_HOURS = {
    "Hospital": "00:00-23:59",
    "School": "06:00-21:00",
    "Church": "06:00-21:00",
}

DEFAULT_FIELD_VALUES = {
    "capacity": "0",
    "occupants": "0",
    "number_of_staff": "0",
    "staff_present": "0",
    "status": "Available",
    "is_open": "TRUE",
}

class FacilityFormWindow(ctk.CTkToplevel):
    def __init__(self, parent, x, y, map_handler):
        super().__init__(parent)
        self.title("Add New Facility")
        self.geometry("450x850")

        self.map_handler = map_handler
        self.coords = (x, y)

        self.attributes("-topmost", True)
        self.grab_set()

        ctk.CTkLabel(self, text="Facility Registration", font=("Arial", 18, "bold")).pack(pady=10)

        # Category selection
        ctk.CTkLabel(self, text="Select Category Layout:", font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(15, 0))
        self.category_var = ctk.StringVar(value=CATEGORY_PLACEHOLDER)

        self.category_dropdown = ctk.CTkComboBox(
            self,
            values=CATEGORY_OPTIONS,
            variable=self.category_var,
            command=self.render_fields,
            state="readonly"
        )
        self.category_dropdown.pack(fill="x", padx=20, pady=5)
        self.category_dropdown.set(CATEGORY_PLACEHOLDER)

        # Field container
        self.field_container = ctk.CTkFrame(self, fg_color="transparent")
        self.field_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Save button
        self.save_button = ctk.CTkButton(
            self,
            text="Save Facility",
            fg_color="#2fa572",
            hover_color="#23855a",
            height=45,
            font=("Arial", 13, "bold"),
            command=self.save
        )
        self.save_button.pack(pady=20)

        self.entries = {}
        self.render_fields()

    def render_fields(self, _=None):
        for widget in self.field_container.winfo_children():
            widget.destroy()

        self.entries = {}
        category = self.get_selected_category()

        if not category:
            self.save_button.configure(state="disabled")
            ctk.CTkLabel(
                self.field_container,
                text="Choose a facility category before entering details.",
                text_color="#cfcfcf"
            ).pack(anchor="w", pady=(10, 0))
            return

        self.save_button.configure(state="normal")

        # Define headers based on category
        headers = [field for field in FACILITY_FIELD_MAP[category] if field != "id"]

        for header in headers:
            ctk.CTkLabel(
                self.field_container,
                text=f"{header.replace('_',' ').title()}:"
            ).pack(anchor="w", pady=(5,0))

            if header == "category":
                entry = ctk.CTkEntry(self.field_container)
                entry.insert(0, category)
                entry.configure(state="disabled")
            elif header == "operating_hours":
                entry = ctk.CTkComboBox(self.field_container, values=["00:00-23:59","06:00-21:00","08:00-17:00"])
                entry.set(DEFAULT_OPERATING_HOURS.get(category, "00:00-23:59"))
            elif header == "status":
                entry = ctk.CTkComboBox(self.field_container, values=["Available","Unavailable"])
                entry.set("Available")
            elif header == "is_open":
                entry = ctk.CTkComboBox(self.field_container, values=["TRUE","FALSE"])
                entry.set("TRUE")
            else:
                entry = ctk.CTkEntry(self.field_container)

            entry.pack(fill="x", pady=(0,5))
            self.entries[header] = entry

    def save(self):
        node_written = False
        facility_written = False
        category = self.get_selected_category()
        if not category:
            messagebox.showerror("Save Error", "Please select a valid facility category before saving.")
            return
        data_dir = get_data_dir()
        os.makedirs(data_dir, exist_ok=True)
        new_id = self.get_next_id(data_dir)
        rx, ry = round(float(self.coords[0]), 2), round(float(self.coords[1]), 2)

        try:
            self.append_node_record(data_dir, new_id, rx, ry)
            node_written = True
            self.append_facility_record(data_dir, category, new_id)
            facility_written = True

            print(f"Successfully saved ID {new_id} to CSV.")

            if self.map_handler:
                self.map_handler.load_and_plot_facilities()

            self.destroy()
        except Exception as exc:
            if node_written and not facility_written:
                self.remove_last_row(os.path.join(data_dir, "nodes.csv"), str(new_id))
            messagebox.showerror("Save Error", f"Could not save facility: {exc}")

    def append_node_record(self, data_dir, new_id, rx, ry):
        nodes_path = os.path.join(data_dir, "nodes.csv")
        nodes_headers = ['id', 'x', 'y', 'type']
        file_empty = not os.path.exists(nodes_path) or os.path.getsize(nodes_path) == 0

        with open(nodes_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if file_empty:
                writer.writerow(nodes_headers)
            writer.writerow([new_id, rx, ry, 'facility'])

    def append_facility_record(self, data_dir, category, new_id):
        fac_path = os.path.join(data_dir, FACILITY_FILE_MAP[category])
        default_fields = FACILITY_FIELD_MAP[category]
        fieldnames = self.get_target_fieldnames(fac_path, default_fields)

        row_data = self.build_row_data(data_dir, category, new_id)

        normalized_row = {field: row_data.get(field, "") for field in fieldnames}
        file_empty = not os.path.exists(fac_path) or os.path.getsize(fac_path) == 0

        with open(fac_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if file_empty:
                writer.writeheader()
            writer.writerow(normalized_row)

    def get_existing_header(self, path):
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return None

        with open(path, 'r', newline='', encoding='utf-8-sig') as file:
            header = next(csv.reader(file), None)

        if not header:
            return None

        return [column.lstrip('\ufeff').strip() for column in header]

    def get_target_fieldnames(self, path, default_fields):
        existing_header = self.get_existing_header(path)
        if not existing_header:
            return default_fields
        if 'id' not in existing_header:
            return default_fields
        return existing_header

    def get_selected_category(self):
        selected = self.category_dropdown.get().strip()
        if selected in FACILITY_FILE_MAP:
            return selected
        return None

    def build_default_name(self, data_dir, category):
        path = os.path.join(data_dir, FACILITY_FILE_MAP[category])
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return f"{category}_1"

        try:
            df = pd.read_csv(path)
            return f"{category}_{len(df.index) + 1}"
        except Exception:
            return f"{category}_1"

    def build_row_data(self, data_dir, category, new_id):
        row_data = {'id': new_id}

        for field in FACILITY_FIELD_MAP[category]:
            if field == 'id':
                continue

            value = str(self.entries[field].get()).strip()
            if not value:
                value = self.get_default_field_value(data_dir, category, field)
            row_data[field] = value

        return row_data

    def get_default_field_value(self, data_dir, category, field):
        if field == "name":
            return self.build_default_name(data_dir, category)
        if field == "category":
            return category
        if field == "operating_hours":
            return DEFAULT_OPERATING_HOURS.get(category, "00:00-23:59")
        return DEFAULT_FIELD_VALUES.get(field, "")

    def get_next_id(self, data_dir):
        max_id = 0
        for f in ["nodes.csv", "new_nodes.csv"]:
            path = os.path.join(data_dir, f)
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    if not df.empty:
                        m = pd.to_numeric(df['id'], errors='coerce').max()
                        if m > max_id:
                            max_id = m
                except:
                    continue
        return int(max_id + 1)

    def remove_last_row(self, path, target_id):
        if not os.path.exists(path):
            return

        with open(path, 'r', newline='', encoding='utf-8') as file:
            rows = list(csv.reader(file))

        if len(rows) <= 1:
            return

        filtered_rows = [rows[0]]
        removed = False
        for row in rows[1:]:
            if not removed and row and row[0] == target_id:
                removed = True
                continue
            filtered_rows.append(row)

        with open(path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(filtered_rows)
