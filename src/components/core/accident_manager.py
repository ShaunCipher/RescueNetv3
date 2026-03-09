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
        cols = ("ID", "Name", "Severity", "Victims", "Status")
        self.tree = ttk.Treeview(self.main_panel, columns=cols, show="headings")
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
            
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Right-click context menu
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="🔍 Search Facilities", command=self.search_from_table)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="✅ Mark Completed", command=lambda: self.archive_incident("COMPLETED"))
        self.context_menu.add_command(label="🗑️ Delete Permanently", command=lambda: self.archive_incident("DELETED"))
        
        self.tree.bind("<Button-3>", self.show_context_menu)

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

    def draw_accidents_on_map(self):
        for plot in self.acc_plots:
            try: plot.remove()
            except: pass
        self.acc_plots = []
        
        if os.path.exists(self.node_file):
            nodes_df = pd.read_csv(self.node_file)
            accidents = nodes_df[nodes_df['type'] == 'accident']
            for _, row in accidents.iterrows():
                p, = self.ax.plot(row['x'], row['y'], 'rx', markersize=12, markeredgewidth=3, zorder=100)
                self.acc_plots.append(p)
        self.fig.canvas.draw_idle()

    def process_submission(self):
        name = self.name_entry.get()
        if not self.selected_coords or not name:
            return messagebox.showerror("Error", "Please provide an incident name and select a location on the map.")
            
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
                "need_firestation": self.need_firestation.get(), "need_evac": self.need_evac.get()
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
        resource_map = {
            'need_medical': ('hospitals.csv', 'Hospital'),
            'need_police': ('policestations.csv', 'Police Station'),
            'need_firestation': ('firestations.csv', 'Fire Station'),
            'need_evac': ('drrm.csv', 'DRRM/Evacuation Center')
        }
        
        for col, (file, label) in resource_map.items():
            if str(acc.get(col, '')).lower() in ['true', '1', '1.0', 'checked']:
                self.create_ranking_table(acc, file, label)

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
        history_entry = {
            "id": acc_id,
            "name": row['name'],
            "severity": row['severity'],
            "outcome": outcome,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        pd.DataFrame([history_entry]).to_csv(self.hist_file, mode='a', header=not os.path.exists(self.hist_file), index=False)
        
        # Remove from active files
        df_acc[df_acc['id'] != acc_id].to_csv(self.acc_file, index=False)
        df_nodes[df_nodes['id'] != acc_id].to_csv(self.node_file, index=False)
        
        self.refresh_all_data()
        messagebox.showinfo("Archive", f"Incident {acc_id} has been marked as {outcome}.")

    def open_history_window(self):
        h_win = ctk.CTkToplevel()
        h_win.title("RescueNet History Archive")
        h_win.geometry("1100x650")
        h_win.attributes("-topmost", True)

        head_frame = ctk.CTkFrame(h_win, fg_color="transparent")
        head_frame.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(head_frame, text="ARCHIVED INCIDENT LOGS", font=("Arial", 18, "bold")).pack(side="left")
        
        cols = ("ID", "Incident Name", "Severity", "Final Status", "Date/Time")
        h_tree = ttk.Treeview(h_win, columns=cols, show="headings")
        for c in cols:
            h_tree.heading(c, text=c)
            h_tree.column(c, width=160, anchor="center")
        h_tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkButton(head_frame, text="🗑️ Clear Entire History", fg_color="#c0392b", hover_color="#a93226", 
                     command=lambda: self.reset_history_file(h_tree)).pack(side="right")

        if os.path.exists(self.hist_file):
            h_df = pd.read_csv(self.hist_file)
            for _, r in h_df.sort_values(by='timestamp', ascending=False).iterrows():
                h_tree.insert("", "end", values=(r.get('id',''), r.get('name',''), r.get('severity',''), r.get('outcome',''), r.get('timestamp','')))

    def reset_history_file(self, tree_widget):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to permanently delete ALL history records?"):
            if os.path.exists(self.hist_file):
                os.remove(self.hist_file)
            for item in tree_widget.get_children():
                tree_widget.delete(item)

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if not os.path.exists(self.acc_file): return
        
        df = pd.read_csv(self.acc_file)
        for _, row in df.iterrows():
            self.tree.insert("", "end", values=(row['id'], row['name'], row['severity'], row['num_victims'], row['status']))
            
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