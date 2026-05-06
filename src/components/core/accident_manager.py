import customtkinter as ctk 
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import os
import networkx as nx
from datetime import datetime
from src.components.core.routing_manager import RoutingManager

class AccidentManager:
    def __init__(self, fig, ax, master_nodes, all_data, master_registry, plots, workspace):
        self.fig = fig
        self.ax = ax
        self.master_nodes = master_nodes
        self.all_data = all_data
        self.master_registry = master_registry
        self.plots = plots
        self.workspace = workspace
        
        # File path definitions
        self.acc_file = 'data/accidents.csv'
        self.node_file = 'data/nodes.csv'
        self.edge_file = 'data/edges.csv'
        self.hist_file = 'data/accident_history.csv'
        
        # Initialize Router with current edge data
        if os.path.exists(self.edge_file):
            edges_df = pd.read_csv(self.edge_file)
        else:
            edges_df = pd.DataFrame(columns=['from', 'to', 'weight'])
            
        self.router = RoutingManager(fig, ax, master_nodes, edges_df)
        
        self.report_window = None
        self.selected_coords = None
        self.cid = None
        self.acc_plots = [] 
        self.active_paths = {}
        self.right_panel_ref = None   # linked by gui.py after both panels are created

    def _sync_right_panel(self):
        """Refresh the right panel summary if it is linked."""
        if self.right_panel_ref is not None:
            try:
                self.right_panel_ref.refresh()
            except Exception:
                pass

    def open_report_window(self):
        if self.report_window and self.report_window.winfo_exists():
            self.report_window.lift()
            self.report_window.attributes("-topmost", True)
            return

        self.report_window = ctk.CTkToplevel()
        self.report_window.title("RescueNet Command & Dispatch")
        self.report_window.geometry("1550x850")
        self.report_window.attributes("-topmost", True)
        self.report_window.focus_force()
        
        # Main Layout Panels
        self.left_panel = ctk.CTkFrame(self.report_window, width=320)
        self.left_panel.pack(side="left", fill="y", padx=5, pady=5)
        self.left_panel.pack_propagate(False)

        self.right_panel = ctk.CTkFrame(self.report_window, width=480)
        self.right_panel.pack(side="right", fill="y", padx=5, pady=5)
        self.right_panel.pack_propagate(False)

        self.main_panel = ctk.CTkFrame(self.report_window)
        self.main_panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.setup_left_panel()
        self.setup_main_panel()
        self.setup_right_panel()
        self.refresh_all_data()

        # Clear all routes from the map when the report window is closed
        self.report_window.protocol("WM_DELETE_WINDOW", self._on_report_window_close)

    def _on_report_window_close(self):
        """Clear all drawn routes from the map, then close the report window."""
        self.router.clear_all_routes()
        self.fig.canvas.draw_idle()
        self.report_window.destroy()

    def setup_left_panel(self):
        ctk.CTkLabel(self.left_panel, text="🚨 Report Incident", font=("Arial", 20, "bold")).pack(pady=15)
        
        ctk.CTkButton(self.left_panel, text="📍 Pick Map Location", fg_color="#e67e22", hover_color="#d35400", command=self.activate_map_picker).pack(pady=5, fill="x", padx=20)
        self.loc_label = ctk.CTkLabel(self.left_panel, text="Location: None", font=("Arial", 11, "italic"))
        self.loc_label.pack()

        self.name_entry = self.create_label_entry("Incident Name:")
        self.victims_entry = self.create_label_entry("Number of Victims:")

        ctk.CTkLabel(self.left_panel, text="Severity Level:").pack(anchor="w", padx=20, pady=(10, 0))
        self.severity_var = ctk.StringVar(value="Minor")
        self.seg_btn = ctk.CTkSegmentedButton(self.left_panel, values=["Minor", "Moderate", "Critical"], variable=self.severity_var)
        self.seg_btn.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.left_panel, text="Resources Required:").pack(anchor="w", padx=20, pady=(5, 0))
        self.need_medical = ctk.CTkCheckBox(self.left_panel, text="Medical (Hospital)")
        self.need_police = ctk.CTkCheckBox(self.left_panel, text="Police Assistance")
        self.need_firestation = ctk.CTkCheckBox(self.left_panel, text="Fire Station")
        self.need_evac = ctk.CTkCheckBox(self.left_panel, text="Evacuation (DRRM)")
        
        self.checkboxes = [self.need_medical, self.need_police, self.need_firestation, self.need_evac]
        for cb in self.checkboxes:
            cb.pack(anchor="w", padx=30, pady=2)

        ctk.CTkButton(self.left_panel, text="Submit Report", fg_color="#27ae60", hover_color="#219150", command=self.process_submission).pack(pady=15, fill="x", padx=20)
        
        # Action Buttons Frame
        btn_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(btn_frame, text="🔄 Refresh", width=135, command=self.refresh_all_data).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="🧹 Clear Map", width=135, command=self.clear_map_graphics).pack(side="right", padx=2)
        
        ctk.CTkButton(self.left_panel, text="📜 View History Archive", command=self.open_history_window).pack(pady=10, fill="x", padx=20)

    def create_label_entry(self, text):
        ctk.CTkLabel(self.left_panel, text=text).pack(anchor="w", padx=20, pady=(10, 0))
        entry = ctk.CTkEntry(self.left_panel)
        entry.pack(fill="x", padx=20, pady=5)
        return entry

    def setup_main_panel(self):
        # Sort controls toolbar
        sort_frame = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        sort_frame.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(sort_frame, text="Sort by:", font=("Arial", 12)).pack(side="left", padx=(0, 8))

        self.sort_var = ctk.StringVar(value="Date Added")
        sort_options = ["Date Added", "Severity", "Victims", "ID", "Name"]
        self.sort_menu = ctk.CTkOptionMenu(sort_frame, values=sort_options, variable=self.sort_var, width=140, command=lambda _: self.refresh_table())
        self.sort_menu.pack(side="left", padx=4)

        self.sort_asc_var = ctk.BooleanVar(value=False)
        self.sort_dir_btn = ctk.CTkButton(sort_frame, text="⬇ Desc", width=80,
                                          command=self._toggle_sort_dir)
        self.sort_dir_btn.pack(side="left", padx=4)

        cols = ("ID", "Name", "Severity", "Victims", "Status", "Date Added", "Facilities Needed")
        self.tree = ttk.Treeview(self.main_panel, columns=cols, show="headings")

        col_widths = {"ID": 45, "Name": 140, "Severity": 80, "Victims": 65,
                      "Status": 90, "Date Added": 130, "Facilities Needed": 200}
        for col in cols:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_by_column(c))
            self.tree.column(col, width=col_widths.get(col, 100), anchor="center")

        # Severity colour tags
        self.tree.tag_configure("Critical", foreground="#e74c3c")
        self.tree.tag_configure("Moderate", foreground="#e67e22")
        self.tree.tag_configure("Minor",    foreground="#2ecc71")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Right-click context menu
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="🔍 Search Facilities", command=self.search_from_table)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="✅ Mark Completed", command=lambda: self.archive_incident("COMPLETED"))
        self.context_menu.add_command(label="🗑️ Delete Permanently", command=lambda: self.archive_incident("DELETED"))

        self.tree.bind("<Button-3>", self.show_context_menu)

    def _toggle_sort_dir(self):
        self.sort_asc_var.set(not self.sort_asc_var.get())
        self.sort_dir_btn.configure(text="⬆ Asc" if self.sort_asc_var.get() else "⬇ Desc")
        self.refresh_table()

    def _sort_by_column(self, col):
        """Allow clicking a column header to sort by that column."""
        mapping = {"ID": "ID", "Name": "Name", "Severity": "Severity",
                   "Victims": "Victims", "Date Added": "Date Added"}
        if col in mapping:
            if self.sort_var.get() == mapping[col]:
                self._toggle_sort_dir()
            else:
                self.sort_var.set(mapping[col])
                self.refresh_table()

    def show_context_menu(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self.context_menu.post(event.x_root, event.y_root)

    def setup_right_panel(self):
        ctk.CTkLabel(self.right_panel, text="Facility Dispatcher", font=("Arial", 18, "bold")).pack(pady=10)
        
        self.acc_dropdown = ctk.CTkComboBox(self.right_panel, width=350, command=self.on_accident_selected)
        self.acc_dropdown.pack(pady=10)
        
        self.rankings_container = ctk.CTkScrollableFrame(self.right_panel, label_text="Nearby Resources")
        self.rankings_container.pack(fill="both", expand=True, padx=10, pady=10)

    def search_from_table(self):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])['values']
            acc_id   = int(values[0])
            acc_name = str(values[1])
            label = f"{acc_name} (ID:{acc_id})"
            self.acc_dropdown.set(label)
            self.on_accident_selected(label)

    def refresh_all_data(self):
        if os.path.exists(self.node_file):
            self.router.refresh_coords(pd.read_csv(self.node_file))
        if os.path.exists(self.edge_file):
            self.router.edges_df = pd.read_csv(self.edge_file)
            self.router.refresh_graph()
        self.refresh_table()
        self.draw_accidents_on_map()
        self._sync_right_panel()

    def draw_accidents_on_map(self):
    # If the right panel's visibility logic is available, delegate to it.
    # This ensures the toggle switch stays in sync.
        if self.right_panel_ref is not None and hasattr(self.right_panel_ref, 'vis_logic') and self.right_panel_ref.vis_logic:
            self.right_panel_ref.refresh_from_csv()
            return

    # Fallback: draw directly if right panel isn't linked yet
        for plot in self.acc_plots:
            try: plot.remove()
            except: pass
        self.acc_plots = []

        if os.path.exists(self.node_file):
            nodes_df = pd.read_csv(self.node_file)
            if os.path.exists(self.acc_file):
                active_ids = pd.read_csv(self.acc_file)['id'].unique()
            else:
                active_ids = []
            accidents = nodes_df[
                (nodes_df['type'] == 'accident') &
                (nodes_df['id'].isin(active_ids))
            ]
            for _, row in accidents.iterrows():
                p, = self.ax.plot(row['x'], row['y'], 'rx', markersize=12, markeredgewidth=3, zorder=100)
                self.acc_plots.append(p)
        self.fig.canvas.draw_idle()

    def process_submission(self):
        name = self.name_entry.get()
        if not self.selected_coords or not name:
            return messagebox.showerror("Error", "Please provide an incident name and select a location on the map.")

        # Warn if no resource type has been selected
        if not any([self.need_medical.get(), self.need_police.get(),
                    self.need_firestation.get(), self.need_evac.get()]):
            if not messagebox.askyesno(
                "No Resources Selected",
                "⚠️ No resources have been selected for this incident.\n\n"
                "The system will be unable to dispatch any facilities.\n\n"
                "Do you want to submit anyway?"
            ):
                return
            
        try:
            # 1. Update nodes.csv
            nodes_df = pd.read_csv(self.node_file)
            new_id = int(nodes_df['id'].max() + 1)
            x, y = self.selected_coords
            
            new_node = pd.DataFrame([[new_id, x, y, 'accident']], columns=['id', 'x', 'y', 'type'])
            new_node.to_csv(self.node_file, mode='a', header=False, index=False)
            
            # 2. Update accidents.csv
            acc_data = {
                "id": new_id, "name": name, "num_victims": self.victims_entry.get() or 0,
                "severity": self.severity_var.get(), "status": "REPORTED",
                "need_medical": int(self.need_medical.get()), "need_police": int(self.need_police.get()),
                "need_firestation": int(self.need_firestation.get()), "need_evac": int(self.need_evac.get()),
                "date_added": datetime.now().strftime("%Y-%m-%d %H:%M"),
                # Keep sent_* columns in sync with the CSV header so pandas reads correctly
                "sent_medical": 0, "sent_police": 0, "sent_firestation": 0, "sent_evac": 0,
            }
            new_row_df = pd.DataFrame([acc_data])
            if os.path.exists(self.acc_file):
                # Align columns to whatever the existing CSV already has
                existing_cols = pd.read_csv(self.acc_file, nrows=0).columns.tolist()
                for col in existing_cols:
                    if col not in new_row_df.columns:
                        new_row_df[col] = 0
                new_row_df = new_row_df[existing_cols]
            new_row_df.to_csv(self.acc_file, mode='a', header=not os.path.exists(self.acc_file), index=False)
            
            # 3. Create Road Connection (Edges)
            road_nodes = nodes_df[nodes_df['type'] == 'road'].copy()
            if road_nodes.empty:
                road_nodes = nodes_df[nodes_df['type'] != 'accident'].copy()
                
            road_nodes['dist'] = np.sqrt((road_nodes['x'] - x)**2 + (road_nodes['y'] - y)**2)
            closest_road = road_nodes.loc[road_nodes['dist'].idxmin()]
            
            edge_dist = round(closest_road['dist'], 2)
            new_edges = pd.DataFrame([
                [new_id, int(closest_road['id']), edge_dist],
                [int(closest_road['id']), new_id, edge_dist]
            ], columns=['from', 'to', 'weight'])
            new_edges.to_csv(self.edge_file, mode='a', header=False, index=False)
            
            # Reload edges so the new accident node is in the router graph
            if os.path.exists(self.edge_file):
                self.router.refresh_coords(pd.read_csv(self.node_file))
                self.router.edges_df = pd.read_csv(self.edge_file)
                self.router.refresh_graph()
            self.refresh_all_data()
            self.clear_form()
            messagebox.showinfo("Reported", f"Incident '{name}' has been successfully logged.")
            
        except Exception as e:
            messagebox.showerror("Submission Error", f"Failed to save incident: {e}")

    # ------------------------------------------------------------------ #
    #  Dynamic Priority Dispatch Algorithm                                #
    # ------------------------------------------------------------------ #

    def _refresh_scores_in_table(self, table, acc_row, _old_load):
        """
        After a new dispatch, re-compute priority scores for all rows in the
        given Treeview and update the Score column in-place.
        Already-dispatched rows are left unchanged.
        """
        updated_load = self._get_facility_load()
        severity    = acc_row.get('severity', 'Minor')
        num_victims = acc_row.get('num_victims', 0)
        for row_id in table.get_children():
            vals = table.item(row_id)['values']
            # Skip rows that have already been dispatched
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

    def _get_facility_load(self):
        """
        Return a dict mapping facility_id -> count of active dispatches.
        Scans self._active_dispatch_keys (format: "acc_id__fac_id") to count
        how many routes are currently assigned to each facility node.
        """
        load = {}
        for key in getattr(self, '_active_dispatch_keys', set()):
            parts = key.split('__')
            if len(parts) == 2:
                fac_id = parts[1]
                load[fac_id] = load.get(fac_id, 0) + 1
        return load

    def _compute_priority_score(self, dist, severity, num_victims, fac_id, facility_load):
        """
        Compute a composite dispatch priority score for a candidate facility.
        A LOWER score means a BETTER / more appropriate dispatch choice.

        Formula:
            score = (dist / severity_weight) * urgency_damper + load_penalty

        Parameters
        ----------
        dist           : float  – shortest-path distance (km) from incident to facility
        severity       : str    – 'Critical', 'Moderate', or 'Minor'
        num_victims    : int    – number of victims reported
        fac_id         : int    – candidate facility node ID
        facility_load  : dict   – {str(fac_id): active_dispatch_count}

        Score components
        ----------------
        severity_weight : Critical=3, Moderate=2, Minor=1
            Divides the raw distance so that for severe incidents, a
            facility 3 km away scores the same base as one 1 km away for
            a minor incident — pushing the algorithm to prefer the closest
            facility more aggressively when lives are at greater risk.

        urgency_damper : 1 / (1 + log1p(victims))
            Logarithmically shrinks the distance penalty as victim count
            rises, rewarding proximity even more for mass-casualty events.

        load_penalty : 2.0 * active_dispatches_to_this_facility
            Adds a flat cost per already-active route to this facility to
            spread the dispatch load and avoid overloading a single resource.
        """
        severity_weight = {'Critical': 3, 'Moderate': 2, 'Minor': 1}.get(str(severity).strip(), 1)
        victims = max(0, int(num_victims) if str(num_victims).isdigit() else 0)
        urgency_damper = 1.0 / (1.0 + np.log1p(victims))
        load_penalty = 2.0 * facility_load.get(str(fac_id), 0)
        return (dist / severity_weight) * urgency_damper + load_penalty

    # ------------------------------------------------------------------ #

    def create_ranking_table(self, acc_row, facility_file, label):
        # facility_file may be a single filename string OR a list of filenames to concat
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
            if not os.path.exists(path): return
            f_df = pd.read_csv(path)
            f_df.columns = f_df.columns.str.strip().str.lower()
        
        # Ensure graph is current
        self.router.refresh_graph()

        # Snapshot current facility load once for consistent scoring
        facility_load = self._get_facility_load()
        severity    = acc_row.get('severity', 'Minor')
        num_victims = acc_row.get('num_victims', 0)
        
        rankings = []
        for _, fac in f_df.iterrows():
            try:
                # NetworkX shortest-path distance
                dist = nx.shortest_path_length(
                    self.router.G,
                    source=int(acc_row['id']),
                    target=int(fac['id']),
                    weight='weight'
                )
                # Dynamic priority score (lower = better)
                score = self._compute_priority_score(
                    dist, severity, num_victims, int(fac['id']), facility_load
                )
                rankings.append({
                    'name':  fac['name'],
                    'dist':  round(dist, 2),
                    'score': round(score, 4),
                    'id':    int(fac['id']),
                })
            except:
                continue
                
        if not rankings: return

        # Sort by composite priority score (ascending = best first)
        sorted_ranks = sorted(rankings, key=lambda x: x['score'])[:5]
        
        try:
            # UI Construction
            frame = ctk.CTkFrame(self.rankings_container)
            frame.pack(fill="x", pady=8, padx=5)
            
            ctk.CTkLabel(
                frame,
                text=f"Top 5 Recommended {label}s",
                font=("Arial", 12, "bold"),
                text_color="#3498db"
            ).pack(pady=2)

            # Show a small legend describing the ranking basis
            severity_str = str(severity).strip()
            legend_color = {"Critical": "#e74c3c", "Moderate": "#e67e22", "Minor": "#2ecc71"}.get(severity_str, "#aaaaaa")
            ctk.CTkLabel(
                frame,
                text=f"Ranked by: distance · severity ({severity_str}) · victim count · facility load",
                font=("Arial", 9, "italic"),
                text_color=legend_color
            ).pack()
            
            table = ttk.Treeview(frame, columns=("Name", "Distance", "Score"), show="headings", height=5)
            table.heading("Name",     text="Facility Name")
            table.heading("Distance", text="Distance (km)")
            table.heading("Score",    text="Priority Score")
            table.column("Distance", width=95,  anchor="center")
            table.column("Score",    width=95,  anchor="center")
            table.pack(fill="x", padx=5)
            
            for rank, item in enumerate(sorted_ranks, start=1):
                badge = "⭐ " if rank == 1 else ""
                # Store both the facility id AND the original distance in tags
                # so cancelling a dispatch can always restore the distance value.
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
                if not selected: return

                row_id = selected[0]
                raw_name = table.item(row_id)['values'][0]
                f_name = _clean_name(raw_name)
                f_id = int(table.item(row_id)['tags'][0])
                route_key = f"{int(acc_row['id'])}__{f_id}"

                success = self.router.calculate_and_draw_keyed(
                    int(acc_row['id']), f_id, str(acc_row['name']), f_name, route_key
                )
                if success:
                    # Update distance cell to DISPATCHED; keep score cell intact
                    cur_score = table.item(row_id)['values'][2]
                    table.item(row_id, values=(f"✅ {f_name}", "DISPATCHED", cur_score))
                    # Track so we can clear when the user switches accidents
                    if not hasattr(self, '_active_dispatch_keys'):
                        self._active_dispatch_keys = set()
                    self._active_dispatch_keys.add(route_key)
                    # Re-score remaining rows with updated load
                    self._refresh_scores_in_table(
                        table, acc_row, facility_load
                    )

            def on_facility_double_click(event, tbl=table, acc=acc_row):
                """Double-clicking a dispatched row cancels and removes its route."""
                row_id = tbl.identify_row(event.y)
                if not row_id:
                    return
                if "DISPATCHED" not in str(tbl.item(row_id)['values'][1]):
                    return
                raw_name = tbl.item(row_id)['values'][0]
                f_name = _clean_name(raw_name)
                f_id = int(tbl.item(row_id)['tags'][0])
                route_key = f"{int(acc['id'])}__{f_id}"
                self.router.clear_route_by_key(route_key)

                # Restore the original distance from the "dist:X.XX" tag
                orig_dist = "—"
                for tag in tbl.item(row_id)['tags']:
                    if str(tag).startswith("dist:"):
                        orig_dist = f"{str(tag)[5:]} km"
                        break

                cur_score = tbl.item(row_id)['values'][2]
                tbl.item(row_id, values=(f_name, orig_dist, cur_score))
                if hasattr(self, '_active_dispatch_keys'):
                    self._active_dispatch_keys.discard(route_key)

            table.bind("<Double-1>", on_facility_double_click)

            ctk.CTkButton(frame, text=f"Dispatch {label}", height=28, fg_color="#2980b9", command=on_dispatch).pack(pady=8)
        except:
            pass

    def on_accident_selected(self, selection):
        # Clear routes drawn for the PREVIOUS accident selection before switching
        for rk in list(getattr(self, '_active_dispatch_keys', set())):
            self.router.clear_route_by_key(rk, redraw=False)
        self._active_dispatch_keys = set()
        self.fig.canvas.draw_idle()

        # Clear existing ranking frames
        for child in self.rankings_container.winfo_children():
            try: child.destroy()
            except: pass

        if not os.path.exists(self.acc_file): return
        df = pd.read_csv(self.acc_file)

        # Parse the accident ID from the dropdown label "Name (ID:123)"
        # This correctly handles duplicate accident names.
        import re
        id_match = re.search(r'\(ID:(\d+)\)$', str(selection).strip())
        if id_match:
            acc_id = int(id_match.group(1))
            match = df[df['id'] == acc_id]
        else:
            # Fallback for legacy callers that pass a plain name
            match = df[df['name'] == selection]

        if match.empty: return

        acc = match.iloc[0]
        
        # Configuration for resource checks
        # need_evac uses a list so schools.csv and churches.csv are concatenated
        # in-memory alongside drrm.csv — no extra CSV file is created
        resource_map = {
            'need_medical':     ('hospitals.csv',                               'Hospital'),
            'need_police':      ('policestations.csv',                          'Police Station'),
            'need_firestation': ('firestations.csv',                            'Fire Station'),
            'need_evac':        (['drrm.csv', 'schools.csv', 'churches.csv'],   'Evacuation Facility'),
        }

        def _needs(val):
            """Return True for any truthy representation pandas might produce."""
            return str(val).strip().lower() in ('1', '1.0', 'true', 'yes', 'checked')

        for col, (file_or_list, label) in resource_map.items():
            if _needs(acc.get(col, '')):
                self.create_ranking_table(acc, file_or_list, label)

    def archive_incident(self, outcome):
        selected = self.tree.selection()
        if not selected: return
        
        acc_id = int(self.tree.item(selected[0])['values'][0])
        df_acc = pd.read_csv(self.acc_file)
        df_nodes = pd.read_csv(self.node_file)
        
        match = df_acc[df_acc['id'] == acc_id]
        if match.empty: return
        row = match.iloc[0]

        # Log to history
        # Build a human-readable resources string from boolean columns
        res_parts = []
        if str(row.get('need_medical',    '')).lower() in ['true', '1', '1.0']: res_parts.append("Medical")
        if str(row.get('need_police',     '')).lower() in ['true', '1', '1.0']: res_parts.append("Police")
        if str(row.get('need_firestation','')).lower() in ['true', '1', '1.0']: res_parts.append("Fire Station")
        if str(row.get('need_evac',       '')).lower() in ['true', '1', '1.0']: res_parts.append("Evacuation")

        # Try to pull x/y coords from nodes.csv for location column
        try:
            n_match = df_nodes[df_nodes['id'] == acc_id]
            loc_str = f"({round(n_match.iloc[0]['x'],2)}, {round(n_match.iloc[0]['y'],2)})" if not n_match.empty else "N/A"
        except Exception:
            loc_str = "N/A"

        history_entry = {
            "id":        acc_id,
            "name":      row['name'],
            "severity":  row['severity'],
            "victims":   row.get('num_victims', 'N/A'),
            "location":  loc_str,
            "resources": ", ".join(res_parts) if res_parts else "None",
            "outcome":   outcome,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        
        pd.DataFrame([history_entry]).to_csv(self.hist_file, mode='a', header=not os.path.exists(self.hist_file), index=False)
        
        # Remove from active files
        df_acc[df_acc['id'] != acc_id].to_csv(self.acc_file, index=False)
        df_nodes[df_nodes['id'] != acc_id].to_csv(self.node_file, index=False)

        # Also remove any edges connected to this incident node
        if os.path.exists(self.edge_file):
            df_edges = pd.read_csv(self.edge_file)
            df_edges = df_edges[(df_edges['from'] != acc_id) & (df_edges['to'] != acc_id)]
            df_edges.to_csv(self.edge_file, index=False)
        
        self.refresh_all_data()
        messagebox.showinfo("Archive", f"Incident {acc_id} has been marked as {outcome}.")
        self._sync_right_panel()

    def open_history_window(self):
        h_win = ctk.CTkToplevel()
        h_win.title("RescueNet History Archive")
        h_win.geometry("1280x650")
        h_win.attributes("-topmost", True)

        head_frame = ctk.CTkFrame(h_win, fg_color="transparent")
        head_frame.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(head_frame, text="ARCHIVED INCIDENT LOGS", font=("Arial", 18, "bold")).pack(side="left")
        
        cols = ("ID", "Incident Name", "Severity", "Victims", "Location", "Resources", "Final Status", "Date/Time")
        h_tree = ttk.Treeview(h_win, columns=cols, show="headings")
        col_widths = {"ID": 50, "Incident Name": 160, "Severity": 80,
                      "Victims": 65, "Location": 130, "Resources": 170,
                      "Final Status": 110, "Date/Time": 130}
        for c in cols:
            h_tree.heading(c, text=c)
            h_tree.column(c, width=col_widths.get(c, 110), anchor="center")
        h_tree.pack(fill="both", expand=True, padx=20, pady=10)

        # Severity colour tags
        h_tree.tag_configure("Critical", foreground="#e74c3c")
        h_tree.tag_configure("Moderate", foreground="#e67e22")
        h_tree.tag_configure("Minor",    foreground="#2ecc71")
        
        ctk.CTkButton(head_frame, text="🗑️ Clear Entire History", fg_color="#c0392b", hover_color="#a93226", 
                     command=lambda: self.reset_history_file(h_tree)).pack(side="right")

        if os.path.exists(self.hist_file):
            h_df = pd.read_csv(self.hist_file)
            # Back-fill columns that may be absent in older history files
            for col in ('victims', 'location', 'resources'):
                if col not in h_df.columns:
                    h_df[col] = 'N/A'
            for _, r in h_df.sort_values(by='timestamp', ascending=False).iterrows():
                sev = r.get('severity', '')
                h_tree.insert("", "end", tags=(sev,),
                              values=(r.get('id', ''), r.get('name', ''), sev,
                                      r.get('victims', 'N/A'), r.get('location', 'N/A'),
                                      r.get('resources', 'N/A'), r.get('outcome', ''),
                                      r.get('timestamp', '')))

    def reset_history_file(self, tree_widget):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to permanently delete ALL history records?"):
            if os.path.exists(self.hist_file):
                os.remove(self.hist_file)
            for item in tree_widget.get_children():
                tree_widget.delete(item)

    # ------------------------------------------------------------------ #
    #  Helpers to normalise legacy / messy accidents.csv rows             #
    # ------------------------------------------------------------------ #

    def _is_valid_date(self, val):
        """Return True if val looks like a YYYY-MM-DD HH:MM timestamp."""
        try:
            datetime.strptime(str(val).strip()[:16], "%Y-%m-%d %H:%M")
            return True
        except Exception:
            return False

    def _derive_facilities(self, row):
        """Build a readable facilities string from need_* boolean columns."""
        parts = []
        if str(row.get('need_medical',     '')).strip() in ('1', '1.0', 'True', 'true'): parts.append('Medical')
        if str(row.get('need_police',      '')).strip() in ('1', '1.0', 'True', 'true'): parts.append('Police')
        if str(row.get('need_firestation', '')).strip() in ('1', '1.0', 'True', 'true'): parts.append('Fire Station')
        if str(row.get('need_evac',        '')).strip() in ('1', '1.0', 'True', 'true'): parts.append('Evacuation')
        return ', '.join(parts) if parts else 'None'

    def _clean_accidents_df(self, df):
        """
        Normalise date_added only — does NOT write facilities_needed to the df.
        facilities_needed is derived on-the-fly in refresh_table for display only.
        """
        if 'date_added' not in df.columns:
            df['date_added'] = ''

        df['date_added'] = df['date_added'].apply(
            lambda v: str(v).strip() if self._is_valid_date(v) else 'N/A'
        )

        return df

    # ------------------------------------------------------------------ #

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(self.acc_file): return

        df = pd.read_csv(self.acc_file)
        df = self._clean_accidents_df(df)

        # --- Sorting ---
        severity_order = {"Critical": 0, "Moderate": 1, "Minor": 2}
        sort_key = getattr(self, 'sort_var', None)
        sort_asc = getattr(self, 'sort_asc_var', None)
        ascending = sort_asc.get() if sort_asc else False

        sort_col = sort_key.get() if sort_key else "Date Added"
        if sort_col == "Severity":
            df['_sev_order'] = df['severity'].map(severity_order).fillna(3)
            df = df.sort_values('_sev_order', ascending=ascending).drop(columns=['_sev_order'])
        elif sort_col == "Victims":
            df = df.sort_values(
                'num_victims', ascending=ascending,
                key=lambda s: pd.to_numeric(s, errors='coerce').fillna(0)
            )
        elif sort_col == "Name":
            df = df.sort_values('name', ascending=ascending)
        elif sort_col == "ID":
            df = df.sort_values('id', ascending=ascending)
        else:  # Date Added (default)
            df = df.sort_values('date_added', ascending=ascending, na_position='last')

        for _, row in df.iterrows():
            sev      = str(row.get('severity', '')).strip()
            date_val = str(row.get('date_added', 'N/A')).strip()
            # Derive facilities on-the-fly from need_* columns — CSV is never modified
            fac_val  = self._derive_facilities(row)
            self.tree.insert("", "end", tags=(sev,),
                             values=(row['id'], row['name'], sev,
                                     row['num_victims'], row['status'],
                                     date_val, fac_val))

        # Format each entry as "Name (ID:123)" so duplicate names remain selectable
        dropdown_values = [
            f"{row['name']} (ID:{int(row['id'])})"
            for _, row in df.iterrows()
        ]
        self.acc_dropdown.configure(values=dropdown_values)

    def activate_map_picker(self):
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_map_click)
        messagebox.showinfo("Map Picker", "Click on the map to set the incident location.")

    def on_map_click(self, event):
        if event.xdata is not None and event.ydata is not None:
            self.selected_coords = (round(event.xdata, 2), round(event.ydata, 2))
            self.loc_label.configure(text=f"Coordinates: {self.selected_coords}", text_color="#2ecc71")
            self.fig.canvas.mpl_disconnect(self.cid)

    def clear_map_graphics(self):
        self.router.clear_all_routes()
        self.draw_accidents_on_map()
        self.fig.canvas.draw_idle()

    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.victims_entry.delete(0, tk.END)
        self.severity_var.set("Minor")
        for cb in self.checkboxes:
            cb.deselect()
        self.selected_coords = None
        self.loc_label.configure(text="Location: None", text_color="white")     