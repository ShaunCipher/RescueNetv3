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
                self.entries[header] = entry

            elif header == "operating_hours":

                entry = ctk.CTkComboBox(
                    self.field_container,
                    values=["00:00-23:59","06:00-21:00","08:00-17:00"]
                )
                self.entries[header] = entry

            elif header == "status":

                entry = ctk.CTkComboBox(
                    self.field_container,
                    values=["Available","Unavailable"]
                )
                self.entries[header] = entry

            elif header == "is_open":

                entry = ctk.CTkComboBox(
                    self.field_container,
                    values=["TRUE","FALSE"]
                )
                self.entries[header] = entry

            else:

                entry = ctk.CTkEntry(self.field_container)
                self.entries[header] = entry

            entry.pack(fill="x", pady=(0,5))

    def save(self):

        category = self.category_var.get()
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)

        new_id = self.get_next_id(data_dir)

        rx, ry = round(float(self.coords[0]),2), round(float(self.coords[1]),2)

        # -------- SAVE NODE --------

        nodes_path = os.path.join(data_dir,"new_nodes.csv")
        nodes_exists = os.path.isfile(nodes_path)

        with open(nodes_path,'a',newline='') as f:

            writer = csv.writer(f)

            if not nodes_exists or os.path.getsize(nodes_path) == 0:
                writer.writerow(['id','x','y','type'])

            writer.writerow([new_id,rx,ry,'facility'])

        # -------- SAVE FACILITY STAGING --------

        fac_path = os.path.join(data_dir,"new_facilities.csv")

        if category in ["DRRM","Firestation","Policestation"]:

            fieldnames = [
                'id','name','category',
                'number_of_staff','staff_present',
                'status','is_open'
            ]

        else:

            fieldnames = [
                'id','name','category',
                'capacity','occupants',
                'operating_hours','status','is_open'
            ]

        row = {'id': new_id}

        for field in fieldnames:
            if field == 'id':
                continue

            val = str(self.entries[field].get()).strip()
            row[field] = val

        print("DEBUG Final Dictionary to Write:", row)

        write_header = True

        if os.path.exists(fac_path) and os.path.getsize(fac_path) > 0:

            with open(fac_path,'r',newline='') as f:
                reader = csv.reader(f)
                existing_header = next(reader,None)

                if existing_header == fieldnames:
                    write_header = False
                else:
                    os.remove(fac_path)
                    write_header = True

        # Ensure header order is always respected
        if not os.path.exists(fac_path) or os.path.getsize(fac_path) == 0:
            with open(fac_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(fieldnames)

        # Always write rows in header order
        with open(fac_path, "a", newline="") as f:
            writer = csv.writer(f)
            ordered_row = [row.get(col, "") for col in fieldnames]
            writer.writerow(ordered_row)

        if self.map_handler:
            self.map_handler.load_and_plot_facilities()

        self.destroy()

    def get_next_id(self,data_dir):

        max_id = 0

        for f in ["nodes.csv","new_nodes.csv"]:

            path = os.path.join(data_dir,f)

            if os.path.exists(path):

                try:
                    df = pd.read_csv(path)

                    if not df.empty:

                        m = pd.to_numeric(df['id'],errors='coerce').max()

                        if m > max_id:
                            max_id = m

                except:
                    continue

        return int(max_id + 1)