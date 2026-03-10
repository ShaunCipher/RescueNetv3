import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import networkx as nx
import matplotlib.colors as mcolors

class DraggableAnnotation:
    """Handles the click-and-drag functionality for map popups."""
    def __init__(self, annotation):
        self.annotation = annotation
        self.got_artist = False
        self.canvas = annotation.figure.canvas
        
        self.cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):
        if event.inaxes != self.annotation.axes: return
        contains, _ = self.annotation.contains(event)
        if not contains: return
        self.got_artist = True
        self.press_xy = self.annotation.xyann
        self.press_mouse = event.x, event.y

    def on_motion(self, event):
        if not self.got_artist or event.inaxes != self.annotation.axes: return
        dx = event.x - self.press_mouse[0]
        dy = event.y - self.press_mouse[1]
        self.annotation.set_anncoords('offset points')
        self.annotation.xyann = (self.press_xy[0] + dx, self.press_xy[1] + dy)
        self.canvas.draw_idle()

    def on_release(self, event):
        self.got_artist = False

    def disconnect(self):
        self.canvas.mpl_disconnect(self.cid_press)
        self.canvas.mpl_disconnect(self.cid_release)
        self.canvas.mpl_disconnect(self.cid_motion)

class RoutingManager:
    def __init__(self, fig, ax, master_nodes_df, edges_df):
        self.fig = fig
        self.ax = ax
        self.master_nodes = master_nodes_df
        self.edges_df = edges_df
        
        self.active_route_lines = {}
        self.route_data = {}         
        self.active_popups = {}      
        self.draggable_instances = {}
        
        self.data_dir = os.path.join(os.getcwd(), 'data')
        self.coords_map = self.master_nodes.set_index('id')[['x', 'y']].T.to_dict('list')
        
        self.G = nx.Graph()
        self.refresh_graph()
        
        self.fig.canvas.mpl_connect('pick_event', self.on_pick_route)

    def refresh_graph(self):
        self.G.clear()
        for _, row in self.edges_df.iterrows():
            self.G.add_edge(int(row['from']), int(row['to']), weight=float(row['weight']))

    def load_facility_nodes(self):
        file_list = ['hospitals.csv', 'firestations.csv', 'policestations.csv', 
                     'drrm.csv', 'churches.csv', 'schools.csv']
        combined = []
        for f_name in file_list:
            path = os.path.join(self.data_dir, f_name)
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    df.columns = df.columns.str.strip().str.lower()
                    if 'name' in df.columns and 'id' in df.columns:
                        combined.append(df[['id', 'name']])
                except: continue
        return pd.concat(combined).drop_duplicates().dropna(subset=['name']) if combined else pd.DataFrame()

    def calculate_and_draw(self, start_id, end_id, name_a, name_b):
        try:
            path = nx.shortest_path(self.G, source=int(start_id), target=int(end_id), weight='weight')
            dist = nx.shortest_path_length(self.G, source=int(start_id), target=int(end_id), weight='weight')
            
            self.clear_all_routes()
            
            path_x = [self.coords_map[node][0] for node in path]
            path_y = [self.coords_map[node][1] for node in path]
            
            line, = self.ax.plot(path_x, path_y, color='#f1c40f', linewidth=5, alpha=0.9, zorder=20, picker=5)
            
            self.active_route_lines['manual'] = line
            self.route_data[line] = {'from': name_a, 'to': name_b, 'dist': dist, 'mid_x': path_x[len(path_x)//2], 'mid_y': path_y[len(path_y)//2]}
            
            self.fig.canvas.draw_idle()
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            messagebox.showerror("Error", "No road path found.")
        except Exception:
            pass

    def on_pick_route(self, event):
        artist = event.artist
        if artist not in self.route_data: return
        
        data = self.route_data[artist]
        route_key = "manual_popup"

        if route_key in self.active_popups:
            self.active_popups[route_key].remove()
            if route_key in self.draggable_instances:
                self.draggable_instances[route_key].disconnect()
                del self.draggable_instances[route_key]
            del self.active_popups[route_key]
        else:
            info_text = (f"ROUTE DETAILS\n"
                         f"FROM: {data['from']}\n"
                         f"TO:   {data['to']}\n"
                         f"DIST: {data['dist']:.2f} km")
            
            border_color = "#f39c12" 
            
            ann = self.ax.annotate(
                info_text, xy=(data['mid_x'], data['mid_y']), xytext=(50, 50),
                textcoords="offset points", 
                fontsize=9, 
                fontweight='bold', 
                family='monospace',
                color='black',  # <--- SET FONT COLOR TO BLACK
                zorder=105, 
                bbox=dict(
                    boxstyle="round,pad=0.5", 
                    fc="white",   # <--- SET BACKGROUND TO SOLID WHITE
                    ec=border_color, 
                    alpha=1.0, 
                    lw=2.5
                ),
                arrowprops=dict(arrowstyle="->", color=border_color)
            )
            
            self.active_popups[route_key] = ann
            self.draggable_instances[route_key] = DraggableAnnotation(ann)
            
        self.fig.canvas.draw_idle()

    def clear_all_routes(self):
        for line in list(self.active_route_lines.values()):
            line.remove()
        self.active_route_lines.clear()
        self.route_data.clear()
        
        for key in list(self.active_popups.keys()):
            self.active_popups[key].remove()
            if key in self.draggable_instances:
                self.draggable_instances[key].disconnect()
                del self.draggable_instances[key]
            del self.active_popups[key]
        
        self.fig.canvas.draw_idle()

    def open_route_window(self, *args):
        root = tk.Toplevel()
        root.title("Manual Route Planner")
        root.geometry("350x300")
        root.attributes("-topmost", True)
        
        df = self.load_facility_nodes()
        if df.empty:
            messagebox.showerror("Data Error", f"No facility data found in {self.data_dir}")
            root.destroy()
            return None
        
        f_names = sorted(df['name'].unique().tolist())
        name_to_id = df.set_index('name')['id'].to_dict()
        
        ttk.Label(root, text="Origin (Point A):", font=('Arial', 10, 'bold')).pack(pady=10)
        combo_a = ttk.Combobox(root, values=f_names, state="readonly", width=35)
        combo_a.pack(pady=5)
        
        ttk.Label(root, text="Destination (Point B):", font=('Arial', 10, 'bold')).pack(pady=10)
        combo_b = ttk.Combobox(root, values=f_names, state="readonly", width=35)
        combo_b.pack(pady=5)
        
        def submit():
            name_a = combo_a.get()
            name_b = combo_b.get()
            if name_a and name_b:
                self.calculate_and_draw(name_to_id[name_a], name_to_id[name_b], name_a, name_b)
                root.destroy()
            else:
                messagebox.showwarning("Selection", "Please select both points.")
        
        ttk.Button(root, text="Draw Route", command=submit).pack(pady=20)
        ttk.Button(root, text="Clear Map", command=self.clear_all_routes).pack()

        return root