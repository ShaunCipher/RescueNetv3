import pandas as pd
import os

class AccidentVisibility:
    def __init__(self, ax, fig, nodes_path='data/nodes.csv', acc_path='data/accidents.csv'):
        self.ax = ax
        self.fig = fig
        self.nodes_path = nodes_path
        self.acc_path = acc_path
        self.markers = [] # Keep track of the 'rx' plots

    def clear_markers(self):
        """Removes existing accident markers from the map."""
        for marker in self.markers:
            try:
                marker.remove()
            except:
                pass
        self.markers = []

    def update_map(self):
        """Reads CSVs and plots active accidents."""
        self.clear_markers()

        if not os.path.exists(self.nodes_path) or not os.path.exists(self.acc_path):
            return

        try:
            # Load Data
            nodes_df = pd.read_csv(self.nodes_path)
            acc_df = pd.read_csv(self.acc_path)

            # 1. Get IDs of all active accidents from accidents.csv
            active_ids = acc_df['id'].unique()

            # 2. Filter nodes.csv to only those IDs
            # This ensures we get the (x, y) coordinates for the accidents
            active_nodes = nodes_df[nodes_df['id'].isin(active_ids)]

            # 3. Plot them
            for _, row in active_nodes.iterrows():
                # Plot as Red X
                p, = self.ax.plot(
                    row['x'], 
                    row['y'], 
                    'rx', 
                    markersize=12, 
                    markeredgewidth=3, 
                    zorder=100
                )
                self.markers.append(p)

            self.fig.canvas.draw_idle()
            
        except Exception as e:
            print(f"Visibility Error: {e}")

    def toggle_visibility(self, show):
        """Quickly show/hide markers without re-reading CSVs."""
        for marker in self.markers:
            marker.set_visible(show)
        self.fig.canvas.draw_idle()