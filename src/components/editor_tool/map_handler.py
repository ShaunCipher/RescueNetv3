import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.image as mpimg
import pandas as pd
import os
from .map_utils import get_colors, get_category_order

class MapHandler:
    def __init__(self, container):
        # 1. Setup Figure and Axis
        self.fig, self.ax = plt.subplots(figsize=(8, 6), dpi=100)
        self.fig.patch.set_facecolor('#1a1a1a')
        self.ax.set_facecolor('#1a1a1a')
        
        # 2. Load Map Background
        img_path = os.path.join("img", "map.png")
        if os.path.exists(img_path):
            img = mpimg.imread(img_path)
            self.ax.imshow(img)
        
        # Style Ticks and Spines
        self.ax.tick_params(colors='white', labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#444444')

        # Dictionary to store scatter plot objects for visibility toggling
        # Format: { 'hospital': <PathCollection>, 'school': <PathCollection>, ... }
        self.facility_scatter_plots = {}

        # 3. Canvas & Toolbar Setup
        self.canvas = FigureCanvasTkAgg(self.fig, master=container)
        self.toolbar = NavigationToolbar2Tk(self.canvas, container)
        self.toolbar.pack_forget() 

    def get_canvas_widget(self):
        return self.canvas.get_tk_widget()

    def load_and_plot_facilities(self):
        """Initial load: Joins nodes.csv with facility data and plots them (hidden)."""
        data_dir = "data"
        nodes_path = os.path.join(data_dir, "nodes.csv")
        
        if not os.path.exists(nodes_path):
            print(f"DEBUG: nodes.csv not found at {nodes_path}")
            return

        nodes_df = pd.read_csv(nodes_path)
        colors = get_colors()
        categories = get_category_order()

        file_mapping = {
            'DRRM': 'drrm.csv', 'Hospital': 'hospitals.csv',
            'Policestation': 'policestations.csv', 'Firestation': 'firestations.csv',
            'Church': 'churches.csv', 'School': 'schools.csv'
        }

        # Clear old plots if reloading
        for scatter in self.facility_scatter_plots.values():
            scatter.remove()
        self.facility_scatter_plots.clear()

        for cat_name in categories:
            filename = file_mapping.get(cat_name)
            path = os.path.join(data_dir, filename)
            
            if os.path.exists(path):
                fac_df = pd.read_csv(path)
                
                # Merge facility IDs with coordinate master list
                merged = pd.merge(fac_df, nodes_df[['id', 'x', 'y']], on='id')
                
                if not merged.empty:
                    color = colors.get(cat_name.lower(), 'white')
                    
                    # Create the scatter plot
                    scatter = self.ax.scatter(
                        merged['x'], merged['y'], 
                        c=color, s=80, edgecolors='white', 
                        linewidths=1.2, zorder=20
                    )
                    
                    # Store reference and set initial visibility to False
                    self.facility_scatter_plots[cat_name.lower()] = scatter
                    scatter.set_visible(False)

        self.canvas.draw_idle()

    def update_facility_visibility(self, master_show, category_choice):
        """Updates Matplotlib visibility based on Switch and Dropdown states."""
        # Normalize choice (e.g., 'Hospitals' -> 'hospital', 'Show All' -> 'all')
        choice = category_choice.lower().strip()
        
        if choice == "show all":
            choice = "all"
        elif choice.endswith('s') and choice != "none":
            choice = choice[:-1] # Remove the 's' for 'hospitals', 'firestations', etc.

        for cat_key, scatter in self.facility_scatter_plots.items():
            if not master_show or choice == "none":
                # Master switch is OFF or "None" selected: Hide all
                scatter.set_visible(False)
            elif choice == "all":
                # Master ON and "Show All": Show everything
                scatter.set_visible(True)
            else:
                # Master ON and specific category selected
                scatter.set_visible(cat_key == choice)
        
        self.canvas.draw_idle()