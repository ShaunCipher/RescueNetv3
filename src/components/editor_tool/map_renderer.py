import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.image as mpimg
import os

class MapRenderer:
    def __init__(self, canvas_frame):
        self.fig, self.ax = plt.subplots(figsize=(10, 8), facecolor='#1a1a1a')
        self.ax.set_facecolor('#1a1a1a')
        
        # Setup the axes (the rulers)
        self.ax.tick_params(axis='both', colors='white', labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color('#555555')

        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def draw_background(self):
        img_path = os.path.abspath(os.path.join(os.getcwd(), 'img', 'map.png'))
        if os.path.exists(img_path):
            img = mpimg.imread(img_path)
            self.ax.imshow(img, zorder=0)
            self.ax.set_aspect('equal')
        self.canvas.draw()

    def clear_all(self):
        self.ax.clear()
        self.draw_background()