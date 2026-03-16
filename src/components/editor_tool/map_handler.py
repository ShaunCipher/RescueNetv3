import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.image as mpimg
import pandas as pd
import os
from .map_utils import get_colors, get_category_order
from .path_utils import get_data_dir

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

        # Storage for visibility toggling
        self.facility_scatter_plots = {}

        # 3. Canvas & Toolbar Setup
        self.canvas = FigureCanvasTkAgg(self.fig, master=container)
        self.toolbar = NavigationToolbar2Tk(self.canvas, container)
        self.toolbar.pack_forget() 

        self.click_callback = None
        self.cid = None # Connection ID for the Matplotlib event

    def get_canvas_widget(self):
        return self.canvas.get_tk_widget()

    # --- Click Handling Logic for Add Facility ---

    def enable_click_listener(self, callback):
        """Connects the map click event to a callback function."""
        self.click_callback = callback
        self.cid = self.canvas.mpl_connect('button_press_event', self._on_click)

    def disable_click_listener(self):
        """Disconnects the map click event."""
        if self.cid:
            self.canvas.mpl_disconnect(self.cid)
            self.cid = None
            self.click_callback = None

    def _on_click(self, event):
        # Only trigger if the click is inside the map axes and a callback exists
        if event.inaxes == self.ax and self.click_callback:
            # Pass the x and y coordinates back to the UI (EditFacilities)
            self.click_callback(event.xdata, event.ydata)

    # --- Plotting & Visibility Logic ---

    def load_and_plot_facilities(self):
        data_dir = get_data_dir()
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
        choice = category_choice.lower().strip()
        
        if choice == "show all":
            choice = "all"
        elif choice.endswith('s') and choice != "none":
            choice = choice[:-1] 

        for cat_key, scatter in self.facility_scatter_plots.items():
            if not master_show or choice == "none":
                scatter.set_visible(False)
            elif choice == "all":
                scatter.set_visible(True)
            else:
                scatter.set_visible(cat_key == choice)
        
        self.canvas.draw_idle()
