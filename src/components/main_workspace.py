import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt 
import matplotlib.image as mpimg
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .terminal_panel import TerminalPanel
from src.components.core.data_manager import DataManager 
from src.components.core.map_utils import get_colors, get_category_order
from src.components.core.filter_logic import FilterLogic
from src.components.core.inspect_node import NodeInspector
from src.components.core.routing_manager import RoutingManager

class MainWorkspace(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=0, fg_color="transparent", **kwargs)

        # 1. Load Data
        self.data_engine = DataManager()
        # Ensure your load_and_clean_data now also loads edges_df
        self.nodes, self.all_data, self.master_registry = self.data_engine.load_and_clean_data()
        self.plots = {} 

        # 2. Layout (Vertical Paned Window for Map + Terminal)
        self.v_paned = tk.PanedWindow(self, orient=tk.VERTICAL, bg="#1a1a1a", sashwidth=4, borderwidth=0)
        self.v_paned.pack(fill="both", expand=True)

        self.work_area = ctk.CTkFrame(self.v_paned, corner_radius=0, fg_color="#212121")
        self.terminal = TerminalPanel(self.v_paned)

        self.v_paned.add(self.work_area, stretch="always")
        self.v_paned.add(self.terminal, height=180, stretch="never")

        # 3. Setup Map and Plots
        self.setup_map()
        self.plot_facilities()

        # 4. Initialize Engines (Order is important)
        
        # Filter Logic for the Left Panel checkboxes
        self.filter_engine = FilterLogic(
            categories=get_category_order(),
            plots=self.plots,
            canvas=self.canvas
        )

        # Routing Engine for Dijkstra pathfinding
        # We pass the edges_df directly from the data engine
        self.routing_engine = RoutingManager(
            self.fig, 
            self.ax, 
            self.nodes, 
            self.data_engine.edges_df 
        )

        # Node Inspector for clicking nodes and seeing info
        self.inspector = NodeInspector(
            self.fig, 
            self.ax, 
            self.plots, 
            self.all_data, 
            self.master_registry,
            workspace=self # Pass workspace reference so inspector can call routing
        )

    def setup_custom_controls(self):
        # Container for our custom buttons
        self.button_frame = ctk.CTkFrame(self.work_area, fg_color="transparent")
        self.button_frame.place(relx=0.02, rely=0.02, anchor="nw") # Top left corner

        # Custom Zoom Button
        self.zoom_btn = ctk.CTkButton(
            self.button_frame, text="🔍 Zoom", width=80, height=32,
            fg_color="#333333", hover_color="#444444",
            command=self.toolbar.zoom
        )
        self.zoom_btn.pack(side="left", padx=5)

        # Custom Pan Button
        self.pan_btn = ctk.CTkButton(
            self.button_frame, text="✋ Pan", width=80, height=32,
            fg_color="#333333", hover_color="#444444",
            command=self.toolbar.pan
        )
        self.pan_btn.pack(side="left", padx=5)

        # Custom Reset (Home) Button
        self.home_btn = ctk.CTkButton(
            self.button_frame, text="🏠 Reset", width=80, height=32,
            fg_color="#333333", hover_color="#444444",
            command=self.toolbar.home
        )
        self.home_btn.pack(side="left", padx=5)

    def setup_map(self):
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(10, 8), dpi=100)
        self.fig.patch.set_facecolor('#212121')
        self.ax.set_facecolor('#212121')

        try:
            map_path = os.path.join('img', 'map.png')
            img = mpimg.imread(map_path)
            self.ax.imshow(img)
            self.ax.axis('on') 
        except FileNotFoundError:
            self.terminal.log("ERROR: map.png not found.")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.work_area)
        self.canvas_widget = self.canvas.get_tk_widget()
        
        # Create it, but DO NOT pack it. This keeps it invisible.
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.work_area)
        self.toolbar.pack_forget() 

        # Now pack just the canvas
        self.canvas_widget.pack(fill="both", expand=True)
        
        # Add your custom dark buttons
        self.setup_custom_controls()


    def plot_facilities(self):
        color_map = get_colors()
        for cat in get_category_order():
            cat_lower = cat.lower()
            group = self.all_data[self.all_data['category'] == cat_lower]
            
            if not group.empty:
                # picker=True allows the NodeInspector to detect the click
                self.plots[cat_lower] = self.ax.scatter(
                    group['x'], group['y'], 
                    c=color_map.get(cat_lower, 'white'), 
                    s=80, edgecolors='white', linewidth=0.5, zorder=5,
                    picker=True, 
                    pickradius=5
                )
        self.canvas.draw()

    def log_analysis(self, message):
        """Allows other components to print to the bottom terminal"""
        self.terminal.log(message)