class EventHandler:
    def __init__(self, renderer, manager):
        self.renderer = renderer
        self.manager = manager
        # Connect the click event
        self.renderer.fig.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        if event.inaxes != self.renderer.ax:
            return
        
        x, y = event.xdata, event.ydata
        if x is not None and y is not None:
            self.manager.handle_map_interaction(x, y)