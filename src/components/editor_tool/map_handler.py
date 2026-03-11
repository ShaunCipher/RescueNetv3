import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.image as mpimg
import os

class MapHandler:
    def __init__(self, container):
        # Create a figure with a dark background to match your UI
        self.fig, self.ax = plt.subplots(figsize=(8, 6), dpi=100)
        self.fig.patch.set_facecolor('#1a1a1a')
        self.ax.set_facecolor('#1a1a1a')
        
        # Load the map image
        # Assuming your structure is: project_root/img/map.png
        img_path = os.path.join("img", "map.png")
        if os.path.exists(img_path):
            img = mpimg.imread(img_path)
            self.ax.imshow(img)
        else:
            self.ax.text(0.5, 0.5, f"Map not found at:\n{img_path}", 
                         color='white', ha='center', va='center')

        # Style the axes/coordinates
        self.ax.tick_params(colors='white', labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#444444')

        # Embed Matplotlib into the CustomTkinter container
        self.canvas = FigureCanvasTkAgg(self.fig, master=container)
        
        # Initialize the hidden toolbar (we'll use this for your custom buttons later)
        self.toolbar = NavigationToolbar2Tk(self.canvas, container)
        self.toolbar.pack_forget()

    def get_canvas_widget(self):
        return self.canvas.get_tk_widget()