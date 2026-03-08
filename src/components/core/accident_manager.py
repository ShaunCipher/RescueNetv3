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
        
        # File Paths
        self.acc_file = 'data/accidents.csv'
        self.node_file = 'data/nodes.csv'
        self.edge_file = 'data/accidents_edge.csv'
        self.hist_file = 'data/accident_history.csv'
        
        # Initialize Routing Logic
        self.router = RoutingManager(fig, ax, master_nodes, pd.read_csv('data/edges.csv'))
        
        self.report_window = None
        self.selected_coords = None
        self.cid = None
        self.acc_plots = [] # Stores the red X markers
        self.active_paths = {} # Track paths: {(acc_id, fac_id): plot_obj}

    def open_report_window(self):
        if self.report_window and self.report_window.winfo_exists():
            self.report_window.lift()
            return

        self.report_window = ctk.CTkToplevel()
        self.report_window.title("RescueNet Command & Dispatch")
        self.report_window.geometry("1550x850")
        
        # PANELS
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
        self.refresh_table()
        self.draw_accidents_on_map()

    def setup_left_panel(self):
        ctk.CTkLabel(self.left_panel, text="🚨 Report Incident", font=("Arial", 20, "bold")).pack(pady=15)
        
        ctk.CTkButton(self.left_panel, text="📍 Pick Map Location", fg_color="#e67e22", command=self.activate_map_picker).pack(pady=5, fill="x", padx=20)
        self.loc_label = ctk.CTkLabel(self.left_panel, text="Location: None", font=("Arial", 11, "italic"))
        self.loc_label.pack()

        self.name_entry = self.create_label_entry("Incident Name:")
        self.victims_entry = self.create_label_entry("Number of Victims:")

        self.severity_var = ctk.StringVar(value="Minor")
        ctk.CTkSegmentedButton(self.left_panel, values=["Minor", "Moderate", "Critical"], variable=self.severity_var).pack(fill="x", padx=20, pady=10)

        self.need_medical = ctk.CTkCheckBox(self.left_panel, text="Hospital")
        self.need_police = ctk.CTkCheckBox(self.left_panel, text="Police")
        self.need_firestation = ctk.CTkCheckBox(self.left_panel, text="Fire Station")
        self.need_evac = ctk.CTkCheckBox(self.left_panel, text="Evacuation")
        self.checkboxes = [self.need_medical, self.need_police, self.need_firestation, self.need_evac]
        for cb in self.checkboxes: cb.pack(anchor="w", padx=30, pady=2)

        ctk.CTkButton(self.left_panel, text="Submit Report", fg_color="#27ae60", command=self.process_submission).pack(pady=15, fill="x", padx=20)
        ctk.CTkButton(self.left_panel, text="🧹 Clear Map Graphics", fg_color="#7f8c8d", command=self.clear_map_graphics).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(self.left_panel, text="📜 View History", command=self.open_history_window).pack(pady=5, fill="x", padx=20)

    def create_label_entry(self, text):
        ctk.CTkLabel(self.left_panel, text=text).pack(anchor="w", padx=20, pady=(10, 0))
        entry = ctk.CTkEntry(self.left_panel); entry.pack(fill="x", padx=20, pady=5)
        return entry

    def setup_main_panel(self):
        cols = ("ID", "Name", "Severity", "Victims", "Status", "Needs")
        self.tree = ttk.Treeview(self.main_panel, columns=cols, show="headings")
        for col in cols: self.tree.heading(col, text=col); self.tree.column(col, width=90, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="🔍 Search Facilities", command=self.search_from_table)
        self.context_menu.add_command(label="✅ Complete Incident", command=lambda: self.archive_incident("COMPLETED"))
        self.context_menu.add_command(label="🗑️ Delete Incident", command=lambda: self.archive_incident("DELETED"))
        self.tree.bind("<Button-3>", lambda e: self.tree.identify_row(e.y) and (self.tree.selection_set(self.tree.identify_row(e.y)), self.context_menu.post(e.x_root, e.y_root)))

    def setup_right_panel(self):
        ctk.CTkLabel(self.right_panel, text="Facility Dispatcher", font=("Arial", 18, "bold")).pack(pady=10)
        self.acc_dropdown = ctk.CTkComboBox(self.right_panel, command=self.on_accident_selected, width=300)
        self.acc_dropdown.pack(pady=10)
        self.rankings_container = ctk.CTkScrollableFrame(self.right_panel, label_text="Resource Rankings")
        self.rankings_container.pack(fill="both", expand=True, padx=10, pady=10)

    # --- MAP & DATA LOGIC ---

    def draw_accidents_on_map(self):
        for p in self.acc_plots: p.remove()
        self.acc_plots = []
        if os.path.exists(self.node_file):
            nodes = pd.read_csv(self.node_file)
            acc_nodes = nodes[nodes['type'] == 'accident']
            for _, r in acc_nodes.iterrows():
                p, = self.ax.plot(r['x'], r['y'], 'rx', markersize=12, markeredgewidth=3)
                self.acc_plots.append(p)
        self.fig.canvas.draw_idle()

    def process_submission(self):
        name = self.name_entry.get()
        if not self.selected_coords or not name: return messagebox.showerror("Error", "Missing Name or Location")

        n_df = pd.read_csv(self.node_file)
        new_id = int(n_df['id'].max() + 1)
        x, y = self.selected_coords

        pd.DataFrame([[new_id, x, y, 'accident']], columns=['id','x','y','type']).to_csv(self.node_file, mode='a', header=False, index=False)

        acc_data = {
            "id": new_id, "name": name, "num_victims": self.victims_entry.get() or 0,
            "severity": self.severity_var.get(), "status": "REPORTED",
            "need_medical": self.need_medical.get(), "need_police": self.need_police.get(),
            "need_firestation": self.need_firestation.get(), "need_evac": self.need_evac.get(),
            "sent_medical": "", "sent_police": "", "sent_firestation": "", "sent_evac": ""
        }
        pd.DataFrame([acc_data]).to_csv(self.acc_file, mode='a', header=not os.path.exists(self.acc_file), index=False)

        self.create_network_connection(new_id, x, y)
        self.draw_accidents_on_map()
        self.clear_form()
        self.refresh_table()

    def create_network_connection(self, acc_id, x, y):
        road_nodes = pd.read_csv(self.node_file)
        road_nodes = road_nodes[road_nodes['type'] != 'accident']
        dist = np.sqrt((road_nodes['x'] - x)**2 + (road_nodes['y'] - y)**2)
        nearest_id = int(road_nodes.iloc[dist.argmin()]['id'])
        dist_val = round(dist.min(), 2)

        edge_data = pd.DataFrame([[acc_id, nearest_id, dist_val], [nearest_id, acc_id, dist_val]], columns=['from','to','weight'])
        edge_data.to_csv(self.edge_file, mode='a', header=not os.path.exists(self.edge_file), index=False)
        edge_data.to_csv('data/edges.csv', mode='a', header=False, index=False)
        self.router.refresh_graph()

    def create_ranking_table(self, acc, file, label):
        path = os.path.join('data', file)
        if not os.path.exists(path): return
        f_df = pd.read_csv(path); ranks = []
        for _, f in f_df.iterrows():
            try:
                d = nx.shortest_path_length(self.router.G, source=int(acc['id']), target=int(f['id']), weight='weight')
                ranks.append({'Name': f['name'], 'Dist': round(d, 2), 'ID': f['id']})
            except: continue
        
        ranks = sorted(ranks, key=lambda x: x['Dist'])[:5]
        fr = ctk.CTkFrame(self.rankings_container); fr.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(fr, text=f"Top 5 {label}s", font=("Arial", 12, "bold")).pack()
        
        t = ttk.Treeview(fr, columns=("Name", "Dist"), show="headings", height=5)
        t.heading("Name", text="Name"); t.heading("Dist", text="Km"); t.column("Dist", width=70); t.pack(fill="x")
        for r in ranks: t.insert("", "end", values=(r['Name'], f"{r['Dist']} km"), tags=(r['ID'],))

        c_menu = tk.Menu(t, tearoff=0)
        c_menu.add_command(label="❌ Cancel Routing", command=lambda: self.cancel_route(acc['id'], t))
        t.bind("<Button-3>", lambda e: t.identify_row(e.y) and (t.selection_set(t.identify_row(e.y)), c_menu.post(e.x_root, e.y_root)))

        def dispatch():
            if not t.selection(): return
            item = t.selection()[0]
            fac_name = t.item(item)['values'][0]
            fac_id = t.item(item)['tags'][0]
            
            df = pd.read_csv(self.acc_file)
            col = {"Hospital": "sent_medical", "Police": "sent_police", "Fire": "sent_firestation", "Evacuation": "sent_evac"}.get(label)
            df[col] = df[col].astype(object)
            current = str(df.loc[df['id'] == int(acc['id']), col].values[0])
            new_val = fac_name if current in ['nan', ''] else f"{current}, {fac_name}"
            df.loc[df['id'] == int(acc['id']), col] = new_val
            df.to_csv(self.acc_file, index=False)
            
            path_plot = self.router.calculate_and_draw(int(acc['id']), int(fac_id), acc['name'], fac_name)
            self.active_paths[(int(acc['id']), int(fac_id))] = path_plot
            t.item(item, values=(f"✅ {fac_name}", "DISPATCHED"))

        ctk.CTkButton(fr, text=f"Dispatch {label}", command=dispatch, height=24).pack(pady=5)

    def cancel_route(self, acc_id, tree_widget):
        sel = tree_widget.selection()
        if not sel: return
        
        # 1. Get Facility Info
        item = tree_widget.item(sel[0])
        fac_name = item['values'][0].replace("✅ ", "") # Clean the checkmark if present
        fac_id = int(item['tags'][0])
        
        # 2. Remove from Map
        key = (int(acc_id), fac_id)
        if key in self.active_paths:
            path_obj = self.active_paths[key]
            if isinstance(path_obj, list):
                for seg in path_obj: 
                    try: seg.remove()
                    except: pass
            else: 
                try: path_obj.remove()
                except: pass
            del self.active_paths[key]
            self.fig.canvas.draw_idle()

        # 3. Remove from CSV Data (So it won't show in History)
        df = pd.read_csv(self.acc_file)
        # Check all possible sent columns
        sent_cols = ['sent_medical', 'sent_police', 'sent_firestation', 'sent_evac']
        for col in sent_cols:
            if col in df.columns:
                val = str(df.loc[df['id'] == int(acc_id), col].values[0])
                if fac_name in val:
                    # Remove the name and clean up commas
                    new_val = val.replace(fac_name, "").replace(", ,", ",").strip(", ")
                    df.loc[df['id'] == int(acc_id), col] = new_val
        
        df.to_csv(self.acc_file, index=False)
        tree_widget.item(sel[0], values=(fac_name, "CANCELLED"))
        messagebox.showinfo("Cancelled", f"Route to {fac_name} removed.")


    def archive_incident(self, outcome):
        sel = self.tree.selection()
        if not sel: return
        acc_id = int(self.tree.item(sel[0])['values'][0])
        
        df_acc = pd.read_csv(self.acc_file)
        df_nodes = pd.read_csv(self.node_file)
        
        # Get the specific rows
        row = df_acc[df_acc['id'] == acc_id].iloc[0]
        node = df_nodes[df_nodes['id'] == acc_id].iloc[0]

        # Explicitly mapping the 'sent' columns to the history
        hist = {
            "id": acc_id, 
            "name": row['name'], 
            "x": node['x'], 
            "y": node['y'],
            "severity": row['severity'], 
            "num_victims": row['num_victims'],
            "sent_medical": row.get('sent_medical', ""), 
            "sent_police": row.get('sent_police', ""),
            "sent_firestation": row.get('sent_firestation', ""), 
            "sent_evac": row.get('sent_evac', ""),
            "outcome": outcome, 
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        # Save to history
        pd.DataFrame([hist]).to_csv(self.hist_file, mode='a', header=not os.path.exists(self.hist_file), index=False)
        
        # Remove from active files
        df_acc[df_acc['id'] != acc_id].to_csv(self.acc_file, index=False)
        df_nodes[df_nodes['id'] != acc_id].to_csv(self.node_file, index=False)
        
        self.draw_accidents_on_map()
        self.refresh_table()
        messagebox.showinfo("Success", f"Incident {acc_id} archived as {outcome}")


    def refresh_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if not os.path.exists(self.acc_file): return
        df = pd.read_csv(self.acc_file)
        names = []
        for _, r in df.iterrows():
            icons = []
            if str(r.get('need_medical')).lower() in ['true', '1']: icons.append("🚑")
            if str(r.get('need_police')).lower() in ['true', '1']: icons.append("👮")
            if str(r.get('need_firestation')).lower() in ['true', '1']: icons.append("🔥")
            if str(r.get('need_evac')).lower() in ['true', '1']: icons.append("🏠")
            self.tree.insert("", "end", values=(r['id'], r['name'], r['severity'], r['num_victims'], r['status'], " ".join(icons)))
            names.append(str(r['name']))
        
        # This keeps the dropdown unique and up to date
        self.acc_dropdown.configure(values=list(dict.fromkeys(names)))

    def on_accident_selected(self, choice):
        # Clear the ranking container to prevent stacking UI elements
        for w in self.rankings_container.winfo_children(): w.destroy()
        
        df = pd.read_csv(self.acc_file)
        match = df[df['name'] == choice]
        if match.empty: return
        acc = match.iloc[0]
        
        map_conf = {'need_medical': ('hospitals.csv', 'Hospital'), 'need_police': ('policestations.csv', 'Police'),
                    'need_firestation': ('firestations.csv', 'Fire'), 'need_evac': ('drrm.csv', 'Evacuation')}
        for key, (file, lbl) in map_conf.items():
            if str(acc.get(key)).lower() in ['true', '1', '1.0']:
                self.create_ranking_table(acc, file, lbl)

    def open_history_window(self):
        h_win = ctk.CTkToplevel(); h_win.title("Incident History"); h_win.geometry("1100x500")
        h_win.attributes("-topmost", True)
        cols = ("ID", "Name", "Severity", "Outcome", "Med", "Police", "Fire", "Evac", "Time")
        tree = ttk.Treeview(h_win, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c); tree.column(c, width=110)
        tree.pack(fill="both", expand=True, padx=20, pady=20)
        if os.path.exists(self.hist_file):
            for _, r in pd.read_csv(self.hist_file).iterrows():
                tree.insert("", "end", values=(r['id'], r['name'], r['severity'], r['outcome'], r.get('sent_medical',''), r.get('sent_police',''), r.get('sent_firestation',''), r.get('sent_evac',''), r['timestamp']))

    def clear_form(self):
        self.name_entry.delete(0, tk.END); self.victims_entry.delete(0, tk.END)
        for cb in self.checkboxes: cb.deselect()
        self.selected_coords = None; self.loc_label.configure(text="Location: None", text_color="white")

    def activate_map_picker(self): self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_map_click)
    
    def on_map_click(self, event):
        if event.xdata: 
            self.selected_coords = (round(event.xdata, 2), round(event.ydata, 2))
            self.loc_label.configure(text=f"Selected: {self.selected_coords}", text_color="#2ecc71")
            self.fig.canvas.mpl_disconnect(self.cid)

    def search_from_table(self):
        sel = self.tree.selection()
        if sel: 
            name = self.tree.item(sel[0])['values'][1]
            self.acc_dropdown.set(name)
            self.on_accident_selected(name)

    def clear_map_graphics(self):
        # 1. Clear all active path lines
        for key in list(self.active_paths.keys()):
            path_obj = self.active_paths[key]
            if isinstance(path_obj, list):
                for seg in path_obj:
                    try: seg.remove()
                    except: pass
            else:
                try: path_obj.remove()
                except: pass
        
        # 2. Reset the dictionary
        self.active_paths = {}
        
        # 3. Redraw the basic accident markers
        self.draw_accidents_on_map()
        self.fig.canvas.draw_idle()