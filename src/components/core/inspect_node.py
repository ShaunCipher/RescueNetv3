import matplotlib.colors as mcolors
from src.components.core import map_utils
import __main__

class DraggableAnnotation:
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

class NodeInspector:
    def __init__(self, fig, ax, plots, all_data, master_registry):
        self.fig = fig
        self.ax = ax
        self.plots = plots
        self.all_data = all_data
        self.master_registry = master_registry
        
        self.active_popups = {}
        self.draggable_instances = {}
        self.color_map = map_utils.get_colors()

        # Connect the Matplotlib pick event to this class
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)

    def _lighten_color(self, color, amount=0.4):
        try:
            c = mcolors.to_rgb(color)
            return mcolors.to_hex([1 - amount * (1 - x) for x in c])
        except:
            return "#ffffff"

    def on_pick(self, event):
        artist = event.artist
        # Find which category plot was clicked
        category = next((cat for cat, p in self.plots.items() if p == artist), None)
        
        if not category:
            return

        index = event.ind[0]
        
        # Handle Accident category vs Static Facilities
        if category.lower() == 'accident':
            try:
                row = __main__.rep_mgr.current_accidents_df.iloc[index]
                node_id = int(row.get('id', 0))
                data = row.to_dict()
            except (AttributeError, IndexError):
                return
        else:
            category_group = self.all_data[self.all_data['category'] == category.lower()]
            if index >= len(category_group): 
                return
            row = category_group.iloc[index]
            node_id = int(row.get('id', 0))
            data = self.master_registry.get(node_id, row.to_dict())

        # Toggle Logic: Click once to open, click again to close
        if node_id in self.active_popups:
            self.active_popups[node_id].remove()
            if node_id in self.draggable_instances:
                self.draggable_instances[node_id].disconnect()
                del self.draggable_instances[node_id]
            del self.active_popups[node_id]
        else:
            self._create_popup(node_id, category, data)
        
        self.fig.canvas.draw_idle()

    def _create_popup(self, node_id, category, data):
        name = data.get('name', 'Unknown')
        status = str(data.get('status', 'Available')).upper()
        x, y = float(data['x']), float(data['y'])
        
        info_lines = [
            f"NAME:   {name}",
            f"TYPE:   {category.upper()}",
            f"STATUS: {status}"
        ]

        # Add logic for specific types
        if category.lower() == 'hospital':
            info_lines.append(f"BEDS:   {data.get('occupants', 0)}/{data.get('capacity', 0)}")
        elif category.lower() == 'accident':
            info_lines.append(f"VICTIMS: {data.get('num_victims', 0)}")
            
        info_text = "\n".join(info_lines)
        base_color = self.color_map.get(category.lower(), 'grey')
        
        # Create the visual bubble
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