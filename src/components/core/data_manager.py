import pandas as pd
import os

class DataManager:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        # These keys MUST match the keys in map_utils.get_colors()
        self.files = {
            'hospital': 'hospitals.csv',
            'policestation': 'policestations.csv',
            'firestation': 'firestations.csv',
            'church': 'churches.csv',
            'school': 'schools.csv',
            'drrm': 'drrm.csv'
        }

    def load_and_clean_data(self):
        nodes_path = os.path.join(self.data_dir, 'nodes.csv')
        nodes = pd.read_csv(nodes_path)
        nodes.columns = nodes.columns.str.strip().str.lower()
        
        master_registry = {}
        all_facility_dfs = []

        for category, filename in self.files.items():
            path = os.path.join(self.data_dir, filename)
            if os.path.exists(path):
                df = pd.read_csv(path)
                df.columns = df.columns.str.strip().str.lower()
                
                # Merge with nodes to get x, y
                df_coords = pd.merge(df, nodes[['id', 'x', 'y']], on='id', how='inner')
                df_coords['category'] = category
                all_facility_dfs.append(df_coords)
                
                for _, row in df_coords.iterrows():
                    master_registry[int(row['id'])] = row.to_dict()

        all_data = pd.concat(all_facility_dfs, ignore_index=True) if all_facility_dfs else pd.DataFrame()
        return nodes, all_data, master_registry