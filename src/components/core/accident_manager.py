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
            acc_name = self.tree.item(selected[0])['values'][1]
            self.acc_dropdown.set(acc_name)
            self.on_accident_selected(acc_name)

    def refresh_all_data(self):
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
                "need_medical": self.need_medical.get(), "need_police": self.need_police.get(),
                "need_firestation": self.need_firestation.get(), "need_evac": self.need_evac.get(),
                "date_added": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            pd.DataFrame([acc_data]).to_csv(self.acc_file, mode='a', header=not os.path.exists(self.acc_file), index=False)
            
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
            
            self.refresh_all_data()
            self.clear_form()
            messagebox.showinfo("Reported", f"Incident '{name}' has been successfully logged.")
            
        except Exception as e:
            messagebox.showerror("Submission Error", f"Failed to save incident: {e}")

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
        
        rankings = []
        for _, fac in f_df.iterrows():
            try:
                # NetworkX path calculation
                dist = nx.shortest_path_length(self.router.G, source=int(acc_row['id']), target=int(fac['id']), weight='weight')
                rankings.append({'name': fac['name'], 'dist': round(dist, 2), 'id': int(fac['id'])})
            except:
                continue
                
        if not rankings: return

        sorted_ranks = sorted(rankings, key=lambda x: x['dist'])[:5]
        
        try:
            # UI Construction
            frame = ctk.CTkFrame(self.rankings_container)
            frame.pack(fill="x", pady=8, padx=5)
            
            ctk.CTkLabel(frame, text=f"Top 5 Closest {label}s", font=("Arial", 12, "bold"), text_color="#3498db").pack(pady=2)
            
            table = ttk.Treeview(frame, columns=("Name", "Distance"), show="headings", height=5)
            table.heading("Name", text="Facility Name")
            table.heading("Distance", text="Distance (km)")
            table.column("Distance", width=100, anchor="center")
            table.pack(fill="x", padx=5)
            
            for item in sorted_ranks:
                table.insert("", "end", values=(item['name'], f"{item['dist']} km"), tags=(str(item['id']),))

            def on_dispatch():
                selected = table.selection()
                if not selected: return
                
                f_name = table.item(selected[0])['values'][0]
                f_id = int(table.item(selected[0])['tags'][0])
                
                try:
                    self.router.calculate_and_draw(int(acc_row['id']), f_id, str(acc_row['name']), str(f_name))
                    self.fig.canvas.draw_idle()
                    table.item(selected[0], values=(f"✅ {f_name}", "DISPATCHED"))
                except Exception as e:
                    messagebox.showerror("Routing Error", f"Could not generate path: {e}")

            ctk.CTkButton(frame, text=f"Dispatch {label}", height=28, fg_color="#2980b9", command=on_dispatch).pack(pady=8)
        except:
            pass

    def on_accident_selected(self, selection):
        # Clear existing ranking frames
        for child in self.rankings_container.winfo_children():
            try: child.destroy()
            except: pass
            
        if not os.path.exists(self.acc_file): return
        df = pd.read_csv(self.acc_file)
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

        for col, (file_or_list, label) in resource_map.items():
            if str(acc.get(col, '')).lower() in ['true', '1', '1.0', 'checked']:
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

        self.acc_dropdown.configure(values=list(dict.fromkeys(df['name'].astype(str).tolist())))

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