import matplotlib.colors as mcolors
from src.components.core import map_utils
import __main__
import os
import pandas as pd

class DraggableAnnotation:
    """Handles the click-and-drag functionality for map popups."""
    def __init__(self, annotation):
        self.annotation = annotation
        self.got_artist = False
        self.canvas = annotation.figure.canvas
        
        # Connect events
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
        """Clean up connections to prevent memory leaks."""
        self.canvas.mpl_disconnect(self.cid_press)
        self.canvas.mpl_disconnect(self.cid_release)
        self.canvas.mpl_disconnect(self.cid_motion)

class NodeInspector:
    """Manages clicking on map nodes to show detailed facility/accident information."""
    def __init__(self, fig, ax, plots, all_data, master_registry, workspace=None):
        self.fig = fig
        self.ax = ax
        self.plots = plots
        self.all_data = all_data
        self.master_registry = master_registry
        self.workspace = workspace
        
        self.active_popups = {}
        self.draggable_instances = {}
        self.color_map = map_utils.get_colors()

        self.fig.canvas.mpl_connect('pick_event', self.on_pick)

    def _lighten_color(self, color, amount=0.4):
        try:
            c = mcolors.to_rgb(color)
            return mcolors.to_hex([1 - amount * (1 - x) for x in c])
        except Exception:
            return "#ffffff"

    def on_pick(self, event):
        artist = event.artist
        category = next((cat for cat, p in self.plots.items() if p == artist), None)
        
        if not category:
            return

        index = event.ind[0]
        
        if category.lower() == 'accident':
            try:
                acc_path = os.path.join('data', 'accidents.csv')
                df = pd.read_csv(acc_path)
                row = df.iloc[index]
                node_id = int(row.get('id', 0))
                data = row.to_dict()
            except Exception as e:
                print(f"Inspector Error: {e}")
                return
        else:
            category_group = self.all_data[self.all_data['category'] == category.lower()]
            if index >= len(category_group): return
            row = category_group.iloc[index]
            node_id = int(row.get('id', 0))
            data = self.master_registry.get(node_id, row.to_dict())

        if node_id in self.active_popups:
            self._close_popup(node_id)
        else:
            self._create_popup(node_id, category, data)
            if category.lower() == 'accident' and self.workspace:
                self.workspace.routing_engine.find_nearest(node_id, 'hospital')
                self.workspace.routing_engine.find_nearest(node_id, 'firestation')

        self.fig.canvas.draw_idle()

    def _close_popup(self, node_id):
        if node_id in self.active_popups:
            self.active_popups[node_id].remove()
            if node_id in self.draggable_instances:
                self.draggable_instances[node_id].disconnect()
                del self.draggable_instances[node_id]
            del self.active_popups[node_id]

    def _create_popup(self, node_id, category, data):
        name = data.get('name', 'Unknown')
        status = str(data.get('status', 'Available')).upper()
        x, y = float(data['x']), float(data['y'])
        
        info_lines = [
            f"NAME:   {name}",
            f"TYPE:   {category.upper()}",
            f"ID:     {node_id}",
            f"STATUS: {status}"
        ]

        if 'capacity' in data:
            occ = data.get('occupants', data.get('occupants ', 0)) 
            cap = data.get('capacity', 0)
            info_lines.append(f"LOAD:   {occ} / {cap}")

        if 'number_of_staff' in data:
            present = data.get('staff_present', 0)
            total = data.get('number_of_staff', 0)
            info_lines.append(f"STAFF:  {present} / {total}")

        if category.lower() == 'accident':
            info_lines.append(f"VICTIMS: {data.get('num_victims', 0)}")

        info_text = "\n".join(info_lines)
        base_color = self.color_map.get(category.lower(), 'grey')
        
        ann = self.ax.annotate(
            info_text, xy=(x, y), xytext=(40, 40),
            textcoords="offset points", fontsize=9, fontweight='bold', family='monospace',
            zorder=100,
            bbox=dict(boxstyle="round,pad=0.5", fc=self._lighten_color(base_color),
                      ec=base_color, alpha=0.9, lw=2),
            arrowprops=dict(arrowstyle="->", color=base_color)
        )
        
        self.active_popups[node_id] = ann
        self.draggable_instances[node_id] = DraggableAnnotation(ann)