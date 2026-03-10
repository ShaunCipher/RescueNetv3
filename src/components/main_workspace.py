import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt 
import matplotlib.image as mpimg
import os
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from time import perf_counter

from .terminal_panel import TerminalPanel
from src.components.core.data_manager import DataManager 
from src.components.core.map_utils import get_colors, get_category_order
from src.components.core.filter_logic import FilterLogic
from src.components.core.inspect_node import NodeInspector
from src.components.core.routing_manager import RoutingManager
from src.components.core.accident_manager import AccidentManager

class MainWorkspace(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        start = perf_counter()
        super().__init__(master, corner_radius=0, fg_color="transparent", **kwargs)

        # 1. Load Data
        self.data_engine = DataManager()
        self.nodes, self.all_data, self.master_registry = self.data_engine.load_and_clean_data()
        self.plots = {} 
        self.hover_ann = None 

        # 2. Layout
        self.v_paned = tk.PanedWindow(self, orient=tk.VERTICAL, bg="#1a1a1a", sashwidth=4, borderwidth=0)
        self.v_paned.pack(fill="both", expand=True)

        self.work_area = ctk.CTkFrame(self.v_paned, corner_radius=0, fg_color="#212121")
        self.terminal = TerminalPanel(self.v_paned)

        self.v_paned.add(self.work_area, stretch="always")
        self.v_paned.add(self.terminal, height=180, stretch="never")

        # 3. Setup Map
        self.setup_map()
            # At the end of MainWorkspace.setup_map
        self.canvas_widget.bind("<Button-1>", lambda e: self.canvas_widget.focus_set())
        self.canvas.mpl_connect('button_press_event', lambda e: self.canvas_widget.focus_set())
        
        # 4. Initialize Engines (In order)
        self.routing_engine = RoutingManager(
            self.fig, self.ax, self.nodes, self.data_engine.edges_df 
        )

        self.report_manager = AccidentManager(
            fig=self.fig, ax=self.ax, master_nodes=self.nodes,
            all_data=self.all_data, master_registry=self.master_registry,
            plots=self.plots, workspace=self
        )

        self.filter_engine = FilterLogic(
            categories=get_category_order(), plots=self.plots, canvas=self.canvas
        )

        # Initializing Inspector with workspace reference for routing/popups
        self.inspector = NodeInspector(
            self.fig, self.ax, self.plots, self.all_data, self.master_registry, workspace=self 
        )

        # 5. Plot Layers
        self.plot_facilities()        # Plots Roads, Hospitals, etc.
        self.refresh_accident_plot()  # Plots Accidents with Picking enabled
        
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_hover)
        
        end = perf_counter()
        self.terminal.log(f"MainWorkspace initialized in {end - start:.2f} seconds.")

    def setup_map(self):
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(10, 8), dpi=100)
        self.fig.patch.set_facecolor('#212121')
        self.ax.set_facecolor('#212121')

        try:
            map_path = os.path.join('img', 'map.png')
            img = mpimg.imread(map_path)
            self.ax.imshow(img)
            self.ax.axis('off')
        except FileNotFoundError:
            self.terminal.log("ERROR: img/map.png not found.")

        self.hover_ann = self.ax.annotate(
            "", xy=(0,0), xytext=(15,15), textcoords="offset points",
            bbox=dict(boxstyle="round", fc="#2c3e50", ec="white", alpha=0.9),
            fontsize=9, color="white", fontweight="bold", zorder=200
        )
        self.hover_ann.set_visible(False)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.work_area)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.work_area)
        self.toolbar.pack_forget() 

        self.canvas_widget.pack(fill="both", expand=True)
        self.setup_custom_controls()

    def setup_custom_controls(self):
        self.button_frame = ctk.CTkFrame(self.work_area, fg_color="transparent")
        self.button_frame.place(relx=0.02, rely=0.02, anchor="nw")
        btns = [
            ("🔍 Zoom", self.toolbar.zoom),
            ("✋ Pan", self.toolbar.pan),
            ("🏠 Reset", self.toolbar.home),
            ("🔄 Refresh", self.refresh_accident_plot)
        ]
        for text, cmd in btns:
            ctk.CTkButton(self.button_frame, text=text, width=80, height=32,
                          fg_color="#333333", hover_color="#444444", command=cmd).pack(side="left", padx=5)

    def plot_facilities(self):
        """Initial plot of infrastructure."""
        color_map = get_colors()
        for cat in get_category_order():
            cat_lower = cat.lower()
            if cat_lower == 'accident': 
                continue 
            
            group = self.all_data[self.all_data['category'] == cat_lower]
            if not group.empty:
                self.plots[cat_lower] = self.ax.scatter(
                    group['x'], group['y'], 
                    c=color_map.get(cat_lower, 'white'), 
                    s=80, edgecolors='white', linewidth=0.5, zorder=5,
                    picker=True, pickradius=5
                )
        self.canvas.draw()

    def refresh_accident_plot(self):
        """Clears and redraws Accidents. Now includes picker=True for inspection."""
        if 'accident' in self.plots:
            try:
                self.plots['accident'].remove()
            except:
                pass
            del self.plots['accident']

        acc_path = os.path.join('data', 'accidents.csv')
        if os.path.exists(acc_path):
            try:
                df = pd.read_csv(acc_path)
                if not df.empty:
                    self.plots['accident'] = self.ax.scatter(
                        df['x'], df['y'], 
                        c='#e74c3c', s=200, marker='X', 
                        edgecolors='white', linewidth=2, 
                        zorder=30, label='Accidents',
                        picker=True,     # Enabled for NodeInspector
                        pickradius=12    # Forgiving click area for the X
                    )
                self.canvas.draw_idle()
            except Exception as e:
                self.log_analysis(f"Error drawing accidents: {e}")

    def on_hover(self, event):
        if event.inaxes != self.ax: return

        # --- LIVE COORDINATE UPDATE ---
        # Reach up to the App instance via the PanedWindow to find the right_panel
        try:
            app = self.master.master 
            if hasattr(app, 'right_panel'):
                app.right_panel.update_coords(event.xdata, event.ydata)
        except:
            pass
        # ------------------------------

        vis = self.hover_ann.get_visible()
        found = False

        if 'accident' in self.plots:
            cont, ind = self.plots['accident'].contains(event)
            if cont:
                acc_path = os.path.join('data', 'accidents.csv')
                df = pd.read_csv(acc_path)
                idx = ind["ind"][0]
                if idx < len(df):
                    row = df.iloc[idx]
                    info = f"INCIDENT: {row['name']}\nSEVERITY: {row.get('severity','N/A')}\nVICTIMS: {row['num_victims']}"
                    self.hover_ann.xy = (row['x'], row['y'])
                    self.hover_ann.set_text(info)
                    self.hover_ann.set_visible(True)
                    found = True

        if not found and vis:
            self.hover_ann.set_visible(False)
        
        if found or (not found and vis):
            self.canvas.draw_idle()

    def log_analysis(self, message):
        self.terminal.log(message)
    
