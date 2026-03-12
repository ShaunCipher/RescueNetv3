import customtkinter as ctk
import csv
import os
import pandas as pd

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
        self.category_var = ctk.StringVar(value="Hospital")

        self.category_dropdown = ctk.CTkComboBox(
            self,
            values=["Hospital", "DRRM", "Firestation", "Policestation", "Church", "School"],
            variable=self.category_var,
            command=self.render_fields
        )
        self.category_dropdown.pack(fill="x", padx=20, pady=5)

        # Field container
        self.field_container = ctk.CTkFrame(self, fg_color="transparent")
        self.field_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.entries = {}
        self.render_fields()

        # Save button
        ctk.CTkButton(
            self,
            text="Add to Staging",
            fg_color="#2fa572",
            hover_color="#23855a",
            height=45,
            font=("Arial", 13, "bold"),
            command=self.save
        ).pack(pady=20)

    def render_fields(self, _=None):
        for widget in self.field_container.winfo_children():
            widget.destroy()

        self.entries = {}
        category = self.category_var.get()

        # Define headers based on category
        if category in ["DRRM", "Firestation", "Policestation"]:
            headers = ["name", "category", "number_of_staff", "staff_present", "status", "is_open"]
        else:
            headers = ["name", "category", "capacity", "occupants", "operating_hours", "status", "is_open"]

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
                entry.set("00:00-23:59")
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
        category = self.category_var.get()
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)

        new_id = self.get_next_id(data_dir)
        rx, ry = round(float(self.coords[0]), 2), round(float(self.coords[1]), 2)

        # 1. SAVE TO NEW_NODES.CSV
        nodes_path = os.path.join(data_dir, "new_nodes.csv")
        nodes_headers = ['id', 'x', 'y', 'type']
        file_empty = not os.path.exists(nodes_path) or os.path.getsize(nodes_path) == 0

        with open(nodes_path, 'a', newline='') as f:
            writer = csv.writer(f)
            if file_empty:
                writer.writerow(nodes_headers)
            writer.writerow([new_id, rx, ry, 'facility'])

        # 2. SAVE TO NEW_FACILITIES.CSV
        fac_path = os.path.join(data_dir, "new_facilities.csv")
        
        # Determine current layout headers
        if category in ["DRRM", "Firestation", "Policestation"]:
            fieldnames = ['id', 'name', 'category', 'number_of_staff', 'staff_present', 'status', 'is_open']
        else:
            fieldnames = ['id', 'name', 'category', 'capacity', 'occupants', 'operating_hours', 'status', 'is_open']

        # Collect data from entries
        row_data = {'id': new_id}
        for field in fieldnames:
            if field == 'id': continue
            val = self.entries[field].get()
            row_data[field] = str(val).strip()

        file_exists = os.path.exists(fac_path) and os.path.getsize(fac_path) > 0
        
        if file_exists:
            with open(fac_path, 'r', newline='') as f:
                existing_header = next(csv.reader(f), None)
            
            if existing_header != fieldnames:
                print("Warning: Header mismatch. Starting new file structure.")
                mode = 'w'
            else:
                mode = 'a'
        else:
            mode = 'w'

        with open(fac_path, mode, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if mode == 'w':
                writer.writeheader()
            writer.writerow(row_data)

        print(f"Successfully saved ID {new_id} to CSV.")

        if self.map_handler:
            self.map_handler.load_and_plot_facilities()

        self.destroy()

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