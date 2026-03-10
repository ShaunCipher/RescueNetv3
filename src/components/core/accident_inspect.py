import matplotlib.colors as mcolors
from src.components.core import map_utils
from src.components.core.inspect_node import DraggableAnnotation
import os
import pandas as pd

class AccidentInspector:
    """Specialized inspector for Accident nodes only."""
    def __init__(self, fig, ax, plots, workspace=None):
        self.fig, self.ax = fig, ax
        self.plots = plots
        self.workspace = workspace
        self.active_popups = {}
        self.draggable_instances = {}
        
        # Connect to the pick event
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)

    def _lighten_color(self, color, amount=0.5):
        try:
            c = mcolors.to_rgb(color)
            return mcolors.to_hex([1 - amount * (1 - x) for x in c])
        except: return "#ffffff"

    def on_pick(self, event):
        # Only trigger if the 'accident' plot was clicked
        artist = event.artist
        if artist != self.plots.get('accident'):
            return

        index = event.ind[0]
        try:
            df = pd.read_csv(os.path.join('data', 'accidents.csv'))
            row = df.iloc[index]
            node_id = int(row['id'])
            
            if node_id in self.active_popups:
                self._close_popup(node_id)
            else:
                self._create_popup(node_id, row.to_dict())
                # Trigger emergency routing automatically
                if self.workspace:
                    self.workspace.routing_engine.find_nearest(node_id, 'hospital')
                    self.workspace.routing_engine.find_nearest(node_id, 'firestation')
            
            self.fig.canvas.draw_idle()
        except Exception as e:
            print(f"Accident Inspector Error: {e}")

    def _close_popup(self, node_id):
        if node_id in self.active_popups:
            self.active_popups[node_id].remove()
            if node_id in self.draggable_instances:
                self.draggable_instances[node_id].disconnect()
                del self.draggable_instances[node_id]
            del self.active_popups[node_id]

    def _create_popup(self, node_id, data):
        # Specific formatting for emergency data
        info_lines = [
            f"⚠️ ALERT: {data.get('name', 'Unknown').upper()}",
            f"ID:      {node_id}",
            f"SEVERITY: {data.get('severity', 'HIGH')}",
            f"VICTIMS:  {data.get('num_victims', 0)}",
            f"STATUS:   {str(data.get('status', 'REPORTED')).upper()}"
        ]

        base_color = "#e74c3c" # Emergency Red
        ann = self.ax.annotate(
            "\n".join(info_lines), xy=(data['x'], data['y']), xytext=(50, -50),
            textcoords="offset points", fontsize=10, fontweight='bold', 
            family='monospace', color='white', zorder=2000,
            bbox=dict(boxstyle="round,pad=0.6", fc=base_color, ec="white", alpha=0.95, lw=2),
            arrowprops=dict(arrowstyle="->", color="white", lw=1.5)
        )
        
        self.active_popups[node_id] = ann
        self.draggable_instances[node_id] = DraggableAnnotation(ann)