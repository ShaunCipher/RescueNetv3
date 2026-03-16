import customtkinter as ctk
from tkinter import messagebox
import os
import pandas as pd
from .edit_facilities import EditFacilities
from .path_utils import get_data_dir


class EditorExitButton(ctk.CTkFrame):
    def __init__(self, parent, exit_command, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.exit_btn = ctk.CTkButton(
            self,
            text="✕ Return to Dashboard",
            width=180,
            height=35,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a",
            command=exit_command
        )
        self.exit_btn.pack(padx=5, pady=10)


class EditorLeftPanel(ctk.CTkFrame):

    def __init__(self, master, toggle_cmd, **kwargs):

        super().__init__(master, width=250, corner_radius=0, fg_color="#2b2b2b", **kwargs)
        self.pack_propagate(False)

        # --- RESIZE HANDLE ---

        self.resizer = ctk.CTkFrame(self, width=8, fg_color="transparent", cursor="sb_h_double_arrow")
        self.resizer.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")
        self.resizer.bind("<B1-Motion>", self.do_resize)

        # --- TOGGLE BUTTON ---

        self.close_btn = ctk.CTkButton(
            self,
            text="<",
            width=20,
            height=60,
            fg_color="#3d3d3d",
            hover_color="#4d4d4d",
            command=toggle_cmd
        )

        self.close_btn.place(relx=1.0, rely=0.5, anchor="e")

        # --- BOTTOM SECTION (Commit + Exit) ---

        self.bottom_container = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_container.pack(side="bottom", fill="x", pady=10)

        self.commit_btn = ctk.CTkButton(
            self.bottom_container,
            text="Commit All Changes",
            width=180,
            height=40,
            fg_color="#1f538d",
            hover_color="#14375e",
            font=("Arial", 12, "bold"),
            command=self.confirm_global_save
        )

        self.commit_btn.pack(padx=5, pady=(0, 10))

        self.exit_section = EditorExitButton(
            self.bottom_container,
            exit_command=master.master.close_editor
        )

        self.exit_section.pack(fill="x")

        # --- EDIT FACILITIES DROPDOWN SECTION ---

        self.is_edit_open = False

        self.edit_menu_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.edit_menu_frame.pack(fill="x", padx=10, pady=(20, 5))

        self.edit_toggle_btn = ctk.CTkButton(
            self.edit_menu_frame,
            text="▶ Edit Facilities",
            height=35,
            fg_color="#3d3d3d",
            hover_color="#4d4d4d",
            anchor="w",
            command=self.toggle_edit_menu
        )

        self.edit_toggle_btn.pack(fill="x")

        self.edit_content = ctk.CTkFrame(self.edit_menu_frame, fg_color="#333333")

        self.facility_logic = EditFacilities(
            self.edit_content,
            map_handler=master.master.editor_workspace.map_handler
        )

        self.facility_logic.pack(fill="x", padx=5, pady=5)

    # ---------------------------------------------------
    # UI LOGIC
    # ---------------------------------------------------

    def toggle_edit_menu(self):

        if self.is_edit_open:

            self.edit_content.pack_forget()
            self.edit_toggle_btn.configure(text="▶ Edit Facilities")

        else:

            self.edit_content.pack(fill="x", pady=(2, 0))
            self.edit_toggle_btn.configure(text="▼ Edit Facilities")

        self.is_edit_open = not self.is_edit_open

    # ---------------------------------------------------
    # COMMIT LOGIC
    # ---------------------------------------------------

    def confirm_global_save(self):
        data_dir = get_data_dir()
        staged_nodes_path = os.path.join(data_dir, "new_nodes.csv")
        staged_facilities_path = os.path.join(data_dir, "new_facilities.csv")
        has_staged_nodes = os.path.exists(staged_nodes_path)
        has_staged_facilities = os.path.exists(staged_facilities_path)

        if not has_staged_nodes and not has_staged_facilities:
            messagebox.showinfo(
                "Already Saved",
                "Facilities added in the road network editor are now saved directly to the main CSV files. There are no staged changes to commit."
            )
            return

        response = messagebox.askyesno(
            "Confirm Commit",
            "This will merge any legacy staged nodes into the main database and clear the staging files.\n\nContinue?"
        )

        if response:
            self.merge_staging_data()

    # ---------------------------------------------------

    def merge_staging_data(self):

        try:

            data_dir = get_data_dir()

            # ----------------------------------------
            # MERGE NODE COORDINATES
            # ----------------------------------------

            nodes_staging = os.path.join(data_dir, "new_nodes.csv")

            if os.path.exists(nodes_staging):

                new_nodes = pd.read_csv(nodes_staging)

                prod_nodes = os.path.join(data_dir, "nodes.csv")

                new_nodes.to_csv(
                    prod_nodes,
                    mode='a',
                    index=False,
                    header=not os.path.exists(prod_nodes)
                )

            # ----------------------------------------
            # MERGE FACILITY DATA
            # ----------------------------------------

            staging_fac_path = os.path.join(data_dir, "new_facilities.csv")

            if os.path.exists(staging_fac_path):

                df_new = pd.read_csv(staging_fac_path)

                if 'category' not in df_new.columns:
                    raise ValueError("Staging CSV corrupted: missing 'category' column.")

                file_mapping = {
                    'Hospital': 'hospitals.csv',
                    'DRRM': 'drrm.csv',
                    'Firestation': 'firestations.csv',
                    'Policestation': 'policestations.csv',
                    'Church': 'churches.csv',
                    'School': 'schools.csv'
                }

                for category in df_new['category'].unique():

                    filename = file_mapping.get(category)

                    if not filename:
                        continue

                    cat_df = df_new[df_new['category'] == category].copy()

                    if category in ["DRRM", "Firestation", "Policestation"]:
                        cols = ["id", "name", "number_of_staff", "staff_present"]
                    else:
                        cols = ["id", "name", "capacity", "operating_hours"]

                    cols_existing = [c for c in cols if c in cat_df.columns]
                    cat_df = cat_df[cols_existing]

                    prod_path = os.path.join(data_dir, filename)

                    cat_df.to_csv(
                        prod_path,
                        mode='a',
                        index=False,
                        header=not os.path.exists(prod_path)
                    )

            # ----------------------------------------
            # CLEANUP STAGING FILES
            # ----------------------------------------

            if os.path.exists(nodes_staging):
                os.remove(nodes_staging)

            if os.path.exists(staging_fac_path):
                os.remove(staging_fac_path)

            messagebox.showinfo(
                "Success",
                "All facilities successfully merged into the database."
            )

            self.facility_logic.map_handler.load_and_plot_facilities()

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Merge failed: {str(e)}"
            )

    # ---------------------------------------------------
    # RESIZER
    # ---------------------------------------------------

    def do_resize(self, event):

        new_width = event.x_root - self.winfo_rootx()

        if 40 < new_width < 800:

            self.configure(width=new_width)
            self.master.master.current_width = new_width

    # ---------------------------------------------------

    def update_toggle_icon(self, is_open):

        self.close_btn.configure(text="<" if is_open else ">")
