import pandas as pd
import os

class AccidentVisibility:
    def __init__(self, ax, fig, nodes_path='data/nodes.csv', acc_path='data/accidents.csv'):
        self.ax = ax
        self.fig = fig
        self.nodes_path = nodes_path
        self.acc_path = acc_path
        self.accident_plot = None  # Reference for the Inspector to use

    def clear_markers(self):
        """Removes existing accident markers from the map."""
        if self.accident_plot:
            try:
                self.accident_plot.remove()
            except:
                pass
            self.accident_plot = None

    def update_map(self):
        """Reads CSVs and plots active accidents as clickable scatter points."""
        self.clear_markers()

        if not os.path.exists(self.nodes_path) or not os.path.exists(self.acc_path):
            return

        try:
            nodes_df = pd.read_csv(self.nodes_path)
            acc_df = pd.read_csv(self.acc_path)

            active_ids = acc_df['id'].unique()
            active_nodes = nodes_df[nodes_df['id'].isin(active_ids)]

            if not active_nodes.empty:
                # Plot as a Scatter collection to enable 'picking'
                self.accident_plot = self.ax.scatter(
                    active_nodes['x'], 
                    active_nodes['y'], 
                    color='#e74c3c', 
                    marker='x', 
                    s=120, 
                    linewidths=3, 
                    zorder=100,
                    picker=True,     # Makes the points clickable
                    label='Accidents'
                )

            self.fig.canvas.draw_idle()
            
        except Exception as e:
            print(f"Visibility Error: {e}")

    def toggle_visibility(self, show):
        """Quickly show/hide markers without re-reading CSVs."""
        if self.accident_plot:
            self.accident_plot.set_visible(show)
        self.fig.canvas.draw_idle()