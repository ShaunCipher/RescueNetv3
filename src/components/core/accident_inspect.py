import matplotlib.colors as mcolors
from src.components.core.inspect_node import DraggableAnnotation
import os
import pandas as pd

class AccidentInspector:
    """Handles click events and popups for Accident nodes with corrected indexing."""
    def __init__(self, fig, ax, plots, workspace=None):
        self.fig, self.ax = fig, ax
        self.plots = plots
        self.workspace = workspace
        self.active_popups = {}
        self.draggable_instances = {}
        
        # Connect to the Matplotlib pick event
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)

    def on_pick(self, event):
        # Only trigger if the specific accident scatter plot was clicked
        if event.artist != self.plots.get('accident'):
            return

        # 'index' is the position in the scatter plot collection
        index = event.ind[0]
        
        try:
            # 1. Load Data
            df_acc = pd.read_csv(os.path.join('data', 'accidents.csv'))
            df_nodes = pd.read_csv(os.path.join('data', 'nodes.csv'))
            
            # 2. Replicate the filtering used in Visibility to align indexes
            active_ids = df_acc['id'].unique()
            active_nodes = df_nodes[df_nodes['id'].isin(active_ids)]
            
            # 3. Get the actual node data based on click index
            clicked_node = active_nodes.iloc[index]
            actual_node_id = clicked_node['id']
            
            # 4. Get the matching accident details
            acc_match = df_acc[df_acc['id'] == actual_node_id]
            if acc_match.empty:
                return
            acc_info = acc_match.iloc[0]

            # Prepare data dictionary for the popup
            data = acc_info.to_dict()
            data['x'] = float(clicked_node['x'])
            data['y'] = float(clicked_node['y'])
            
            node_id_str = str(actual_node_id).strip()
            
            # Toggle Popup behavior
            if node_id_str in self.active_popups:
                self._close_popup(node_id_str)
            else:
                self._create_popup(node_id_str, data)
                
                # Automatically trigger routing if workspace is available
                if self.workspace and hasattr(self.workspace, 'routing_engine'):
                    self.workspace.routing_engine.find_nearest(actual_node_id, 'hospital')
                    self.workspace.routing_engine.find_nearest(actual_node_id, 'firestation')
            
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
        # Clean text formatting as requested (no emojis to avoid Glyph errors)
        info_lines = [
            f"Accident: {str(data.get('name', 'Unknown')).upper()}",
            f"ID: {node_id}",
            f"Number of victims: {data.get('num_victims', 0)}",
            f"Response needed: {str(data.get('status', 'REQUIRED')).upper()}",
            f"Severity: {str(data.get('severity', 'HIGH')).upper()}"
        ]

        base_color = "#e74c3c" # Emergency Red
        ann = self.ax.annotate(
            "\n".join(info_lines), 
            xy=(data['x'], data['y']), 
            xytext=(40, -40),
            textcoords="offset points", 
            fontsize=10, 
            fontweight='bold', 
            family='monospace', 
            color='white', 
            zorder=2000,
            bbox=dict(boxstyle="round,pad=0.5", fc=base_color, ec="white", alpha=0.9, lw=2),
            arrowprops=dict(arrowstyle="->", color=base_color, lw=1.5)
        )
        
        self.active_popups[node_id] = ann
        self.draggable_instances[node_id] = DraggableAnnotation(ann)