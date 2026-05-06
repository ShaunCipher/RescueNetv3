import re
import customtkinter as ctk
from tkinter import ttk, messagebox
import numpy as np
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
        self._active_dispatch_keys = set()

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
        """Reload incident names from accidents.csv into the dropdown as 'Name (ID:X)'."""
        if self.am is None:
            return
        acc_file = getattr(self.am, 'acc_file', 'data/accidents.csv')
        if os.path.exists(acc_file):
            try:
                df = pd.read_csv(acc_file)
                dropdown_values = [
                    f"{row['name']} (ID:{int(row['id'])})"
                    for _, row in df.iterrows()
                ]
                self.acc_dropdown.configure(values=dropdown_values)
            except Exception:
                pass

    # ── Priority scoring helpers (mirrors AccidentManager exactly) ────────

    def _get_facility_load(self):
        """
        Return a dict mapping str(facility_id) -> count of active dispatches.
        Scans self._active_dispatch_keys (format: "acc_id__fac_id").
        """
        load = {}
        for key in self._active_dispatch_keys:
            parts = key.split('__')
            if len(parts) == 2:
                fac_id = parts[1]
                load[fac_id] = load.get(fac_id, 0) + 1
        return load

    def _compute_priority_score(self, dist, severity, num_victims, fac_id, facility_load):
        """
        Compute a composite dispatch priority score (lower = better).

        Formula:
            score = (dist / severity_weight) * urgency_damper + load_penalty

        severity_weight : Critical=3, Moderate=2, Minor=1
        urgency_damper  : 1 / (1 + log1p(victims))
        load_penalty    : 2.0 * active_dispatches_to_this_facility
        """
        severity_weight = {'Critical': 3, 'Moderate': 2, 'Minor': 1}.get(str(severity).strip(), 1)
        victims = max(0, int(num_victims) if str(num_victims).isdigit() else 0)
        urgency_damper = 1.0 / (1.0 + np.log1p(victims))
        load_penalty = 2.0 * facility_load.get(str(fac_id), 0)
        return (dist / severity_weight) * urgency_damper + load_penalty

    def _refresh_scores_in_table(self, table, acc_row, _old_load):
        """
        After a new dispatch, re-compute priority scores for all non-dispatched
        rows in the given Treeview and update the Score column in-place.
        """
        updated_load = self._get_facility_load()
        severity    = acc_row.get('severity', 'Minor')
        num_victims = acc_row.get('num_victims', 0)
        for row_id in table.get_children():
            vals = table.item(row_id)['values']
            if "DISPATCHED" in str(vals[1]):
                continue
            try:
                fac_id = int(table.item(row_id)['tags'][0])
                dist   = float(str(vals[1]).replace(' km', '').strip())
                new_score = round(
                    self._compute_priority_score(dist, severity, num_victims, fac_id, updated_load),
                    4
                )
                table.item(row_id, values=(vals[0], vals[1], new_score))
            except Exception:
                pass

    # ── Facility Dispatcher logic ─────────────────────────────────────────

    def on_accident_selected(self, selection):
        """Populate the rankings container for the chosen incident."""
        # Clear routes drawn for the PREVIOUS accident before switching
        router = getattr(self.am, 'router', None) if self.am else None
        if router:
            for rk in list(self._active_dispatch_keys):
                router.clear_route_by_key(rk, redraw=False)
            if self.fig:
                self.fig.canvas.draw_idle()
        self._active_dispatch_keys = set()

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

        # Parse accident ID from "Name (ID:123)" — handles duplicate names correctly
        id_match = re.search(r'\(ID:(\d+)\)$', str(selection).strip())
        if id_match:
            acc_id = int(id_match.group(1))
            match = df[df['id'] == acc_id]
        else:
            # Fallback for plain-name callers
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

        def _needs(val):
            """Return True for any truthy representation pandas might produce."""
            return str(val).strip().lower() in ('1', '1.0', 'true', 'yes', 'checked')

        for col, (file_or_list, label) in resource_map.items():
            if _needs(acc.get(col, '')):
                self._create_ranking_table(acc, file_or_list, label)

    def _create_ranking_table(self, acc_row, facility_file, label):
        """Build a top-5 priority-ranked facility table inside rankings_container."""
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

        # Snapshot facility load and incident attributes once for consistent scoring
        facility_load = self._get_facility_load()
        severity    = acc_row.get('severity', 'Minor')
        num_victims = acc_row.get('num_victims', 0)

        rankings = []
        for _, fac in f_df.iterrows():
            try:
                dist = nx.shortest_path_length(
                    router.G,
                    source=int(acc_row['id']),
                    target=int(fac['id']),
                    weight='weight'
                )
                score = self._compute_priority_score(
                    dist, severity, num_victims, int(fac['id']), facility_load
                )
                rankings.append({
                    'name':  fac['name'],
                    'dist':  round(dist, 2),
                    'score': round(score, 4),
                    'id':    int(fac['id']),
                })
            except Exception:
                continue

        if not rankings:
            return

        # Sort by composite priority score (ascending = best first)
        sorted_ranks = sorted(rankings, key=lambda x: x['score'])[:5]

        try:
            frame = ctk.CTkFrame(self.rankings_container)
            frame.pack(fill="x", pady=8, padx=5)

            ctk.CTkLabel(
                frame,
                text=f"Top 5 Recommended {label}s",
                font=("Arial", 12, "bold"),
                text_color="#3498db"
            ).pack(pady=2)

            # Legend describing the ranking basis (colour-coded by severity)
            severity_str = str(severity).strip()
            legend_color = {
                "Critical": "#e74c3c",
                "Moderate": "#e67e22",
                "Minor":    "#2ecc71"
            }.get(severity_str, "#aaaaaa")
            ctk.CTkLabel(
                frame,
                text=f"Ranked by: distance · severity ({severity_str}) · victim count · facility load",
                font=("Arial", 9, "italic"),
                text_color=legend_color
            ).pack()

            table = ttk.Treeview(
                frame,
                columns=("Name", "Distance", "Score"),
                show="headings",
                height=5
            )
            table.heading("Name",     text="Facility Name")
            table.heading("Distance", text="Distance (km)")
            table.heading("Score",    text="Priority Score")
            table.column("Distance", width=95, anchor="center")
            table.column("Score",    width=95, anchor="center")
            table.pack(fill="x", padx=5)

            for rank, item in enumerate(sorted_ranks, start=1):
                badge = "⭐ " if rank == 1 else ""
                # Store both facility id AND original distance in tags so
                # cancelling a dispatch can always restore the distance value.
                table.insert(
                    "", "end",
                    values=(f"{badge}{item['name']}", f"{item['dist']} km", item['score']),
                    tags=(str(item['id']), f"dist:{item['dist']}")
                )

            def _clean_name(raw):
                """Strip dispatch badge and star prefix from a display name."""
                return str(raw).lstrip("✅ ").lstrip("⭐ ").strip()

            def on_dispatch():
                selected = table.selection()
                if not selected:
                    return
                row_id   = selected[0]
                raw_name = table.item(row_id)['values'][0]
                f_name   = _clean_name(raw_name)
                f_id     = int(table.item(row_id)['tags'][0])
                route_key = f"{int(acc_row['id'])}__{f_id}"

                success = router.calculate_and_draw_keyed(
                    int(acc_row['id']), f_id,
                    str(acc_row['name']), f_name,
                    route_key
                )
                if success:
                    cur_score = table.item(row_id)['values'][2]
                    table.item(row_id, values=(f"✅ {f_name}", "DISPATCHED", cur_score))
                    self._active_dispatch_keys.add(route_key)
                    # Re-score remaining rows with updated load
                    self._refresh_scores_in_table(table, acc_row, facility_load)

            def on_facility_double_click(event, tbl=table, acc=acc_row):
                """Double-clicking a dispatched row cancels and removes its route."""
                row_id = tbl.identify_row(event.y)
                if not row_id:
                    return
                if "DISPATCHED" not in str(tbl.item(row_id)['values'][1]):
                    return
                raw_name = tbl.item(row_id)['values'][0]
                f_name   = _clean_name(raw_name)
                f_id     = int(tbl.item(row_id)['tags'][0])
                route_key = f"{int(acc['id'])}__{f_id}"
                router.clear_route_by_key(route_key)

                # Restore the original distance from the "dist:X.XX" tag
                orig_dist = "—"
                for tag in tbl.item(row_id)['tags']:
                    if str(tag).startswith("dist:"):
                        orig_dist = f"{str(tag)[5:]} km"
                        break

                cur_score = tbl.item(row_id)['values'][2]
                tbl.item(row_id, values=(f_name, orig_dist, cur_score))
                self._active_dispatch_keys.discard(route_key)

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