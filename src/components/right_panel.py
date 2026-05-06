import customtkinter as ctk
from tkinter import ttk, messagebox
import pandas as pd
import os
import networkx as nx
from src.components.core.accident_visibility import AccidentVisibility
from src.components.core.accident_inspect import AccidentInspector

class RightPanel(ctk.CTkFrame):
    def __init__(self, master, accident_manager=None, ax=None, fig=None, workspace=None, **kwargs):
        self.toggle_cmd = kwargs.pop('toggle_cmd', None)
        super().__init__(master, **kwargs)
        
        self.ax = ax
        self.fig = fig
        self.workspace = workspace
        self.am = accident_manager
        self.vis_logic = AccidentVisibility(ax, fig) if ax and fig else None
        self.inspector = None

        self.setup_ui()

    def setup_ui(self):
        # ── Section: Accident Report ──────────────────────────────────────
        self.label = ctk.CTkLabel(self, text="Accident Report", font=("Arial", 14, "bold"))
        self.label.pack(pady=(20, 10), padx=20)

        self.show_acc_var = ctk.BooleanVar(value=True)
        self.vis_switch = ctk.CTkSwitch(
            self,
            text="Show Accident Location",
            variable=self.show_acc_var,
            command=self.handle_toggle,
            progress_color="#e74c3c"
        )
        self.vis_switch.pack(pady=10, padx=20)

        # ── Divider ───────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=2, fg_color="#444444").pack(fill="x", padx=15, pady=(5, 0))

        # ── Section: Facility Dispatcher ──────────────────────────────────
        ctk.CTkLabel(self, text="Facility Dispatcher", font=("Arial", 14, "bold")).pack(pady=(12, 6))

        self.acc_dropdown = ctk.CTkComboBox(self, width=220, command=self.on_accident_selected)
        self.acc_dropdown.pack(pady=(0, 8), padx=20)

        self.rankings_container = ctk.CTkScrollableFrame(self, label_text="Nearby Resources")
        self.rankings_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Populate both sections
        self.refresh_from_csv()

    # ── Visibility toggle ─────────────────────────────────────────────────

    def handle_toggle(self):
        if self.vis_logic:
            self.vis_logic.toggle_visibility(self.show_acc_var.get())

    # ── Map refresh (called externally via accident_manager._sync_right_panel) ──

    def refresh_from_csv(self):
        """Updates the map markers and refreshes the accident dropdown list."""
        if self.vis_logic:
            self.vis_logic.update_map()

            # Respect whatever the toggle switch is currently set to
            self.vis_logic.toggle_visibility(self.show_acc_var.get())

            acc_artist = getattr(self.vis_logic, 'accident_plot', None)
            if acc_artist:
                plots = {'accident': acc_artist}
                self.inspector = AccidentInspector(
                    self.fig,
                    self.ax,
                    plots,
                    workspace=self.workspace
                )

        self._refresh_dropdown()

    def refresh(self):
        """Public alias used by AccidentManager._sync_right_panel()."""
        self.refresh_from_csv()

    # ── Dropdown helpers ──────────────────────────────────────────────────

    def _refresh_dropdown(self):
        """Reload incident names from accidents.csv into the dropdown."""
        if self.am is None:
            return
        acc_file = getattr(self.am, 'acc_file', 'data/accidents.csv')
        if os.path.exists(acc_file):
            try:
                df = pd.read_csv(acc_file)
                names = list(dict.fromkeys(df['name'].astype(str).tolist()))
                self.acc_dropdown.configure(values=names)
            except Exception:
                pass

    # ── Facility Dispatcher logic (ported from AccidentManager) ──────────

    def on_accident_selected(self, selection):
        """Populate the rankings container for the chosen incident."""
        # Clear existing ranking frames
        for child in self.rankings_container.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

        if self.am is None:
            return

        acc_file = getattr(self.am, 'acc_file', 'data/accidents.csv')
        if not os.path.exists(acc_file):
            return

        df = pd.read_csv(acc_file)
        match = df[df['name'] == selection]
        if match.empty:
            return

        acc = match.iloc[0]

        resource_map = {
            'need_medical':     ('hospitals.csv',                             'Hospital'),
            'need_police':      ('policestations.csv',                        'Police Station'),
            'need_firestation': ('firestations.csv',                          'Fire Station'),
            'need_evac':        (['drrm.csv', 'schools.csv', 'churches.csv'], 'Evacuation Facility'),
        }

        for col, (file_or_list, label) in resource_map.items():
            if str(acc.get(col, '')).lower() in ['true', '1', '1.0', 'checked']:
                self._create_ranking_table(acc, file_or_list, label)

    def _create_ranking_table(self, acc_row, facility_file, label):
        """Build a top-5 facility ranking table inside rankings_container."""
        if self.am is None:
            return

        # Load facility data (single file or list of files)
        if isinstance(facility_file, list):
            frames = []
            for fname in facility_file:
                p = os.path.join('data', fname)
                if os.path.exists(p):
                    try:
                        tmp = pd.read_csv(p)
                        tmp.columns = tmp.columns.str.strip().str.lower()
                        frames.append(tmp)
                    except Exception:
                        continue
            if not frames:
                return
            f_df = pd.concat(frames, ignore_index=True)
        else:
            path = os.path.join('data', facility_file)
            if not os.path.exists(path):
                return
            f_df = pd.read_csv(path)
            f_df.columns = f_df.columns.str.strip().str.lower()

        # Ensure router graph is current
        router = getattr(self.am, 'router', None)
        if router is None:
            return
        router.refresh_graph()

        rankings = []
        for _, fac in f_df.iterrows():
            try:
                dist = nx.shortest_path_length(
                    router.G,
                    source=int(acc_row['id']),
                    target=int(fac['id']),
                    weight='weight'
                )
                rankings.append({'name': fac['name'], 'dist': round(dist, 2), 'id': int(fac['id'])})
            except Exception:
                continue

        if not rankings:
            return

        sorted_ranks = sorted(rankings, key=lambda x: x['dist'])[:5]

        try:
            frame = ctk.CTkFrame(self.rankings_container)
            frame.pack(fill="x", pady=8, padx=5)

            ctk.CTkLabel(
                frame,
                text=f"Top 5 Closest {label}s",
                font=("Arial", 12, "bold"),
                text_color="#3498db"
            ).pack(pady=2)

            table = ttk.Treeview(frame, columns=("Name", "Distance"), show="headings", height=5)
            table.heading("Name", text="Facility Name")
            table.heading("Distance", text="Distance (km)")
            table.column("Distance", width=100, anchor="center")
            table.pack(fill="x", padx=5)

            for item in sorted_ranks:
                table.insert("", "end", values=(item['name'], f"{item['dist']} km"), tags=(str(item['id']),))

            def on_dispatch():
                selected = table.selection()
                if not selected:
                    return
                row_id = selected[0]
                raw_name = table.item(row_id)['values'][0]
                f_name = str(raw_name).lstrip("✅ ").strip()
                f_id = int(table.item(row_id)['tags'][0])
                route_key = f"{int(acc_row['id'])}__{f_id}"
                success = router.calculate_and_draw_keyed(
                    int(acc_row['id']), f_id,
                    str(acc_row['name']), f_name,
                    route_key
                )
                if success:
                    table.item(row_id, values=(f"✅ {f_name}", "DISPATCHED"))

            def on_facility_double_click(event, tbl=table, acc=acc_row):
                """Double-clicking a dispatched row cancels and removes its route."""
                row_id = tbl.identify_row(event.y)
                if not row_id:
                    return
                if "DISPATCHED" not in str(tbl.item(row_id)['values'][1]):
                    return
                raw_name = tbl.item(row_id)['values'][0]
                f_name = str(raw_name).lstrip("✅ ").strip()
                f_id = int(tbl.item(row_id)['tags'][0])
                route_key = f"{int(acc['id'])}__{f_id}"
                router.clear_route_by_key(route_key)
                tbl.item(row_id, values=(f_name, "—"))

            table.bind("<Double-1>", on_facility_double_click)

            ctk.CTkButton(
                frame,
                text=f"Dispatch {label}",
                height=28,
                fg_color="#2980b9",
                command=on_dispatch
            ).pack(pady=8)

        except Exception:
            pass