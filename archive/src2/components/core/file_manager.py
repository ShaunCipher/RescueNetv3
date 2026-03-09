import pandas as pd
import os

class FileManager:
    def __init__(self, data_folder="data"):
        self.data_folder = data_folder
        # Map the category name in your Detail CSVs to the filter keys we use
        self.category_map = {
            "DRRM": "drrm",
            "Church": "churches",
            "Firestation": "firestations",
            "Hospital": "hospitals",
            "Policestation": "policestations",
            "School": "schools"
        }

    def load_all_data(self):
        master_registry = {}
        
        # 1. Load the coordinates from nodes.csv
        nodes_path = os.path.join(self.data_folder, "nodes.csv")
        if not os.path.exists(nodes_path):
            print("Error: nodes.csv not found!")
            return {}

        nodes_df = pd.read_csv(nodes_path)

        # 2. Load all Detail CSVs into a temporary dictionary for quick lookup
        details = {}
        detail_files = ["drrm.csv", "churches.csv", "firestations.csv", 
                        "hospitals.csv", "policestations.csv", "schools.csv"]
        
        for f in detail_files:
            path = os.path.join(self.data_folder, f)
            if os.path.exists(path):
                df = pd.read_csv(path)
                # Convert ID to string to ensure matching works
                for _, row in df.iterrows():
                    details[str(row['id'])] = row.to_dict()

        # 3. Merge coordinates with details
        for _, node in nodes_df.iterrows():
            node_id = str(node['id'])
            
            # Default values from nodes.csv
            entry = {
                'x': float(node['x']),
                'y': float(node['y']),
                'type': node['type'],
                'status': 'Available',  # Default
                'category': 'road'      # Default
            }

            # If this node has extra info in a detail CSV, merge it
            if node_id in details:
                detail_row = details[node_id]
                raw_cat = detail_row.get('category', 'road')
                
                entry['status'] = detail_row.get('status', 'Available')
                entry['name'] = detail_row.get('name', 'Unknown')
                # Standardize category name for the StatusManager buttons
                entry['category'] = self.category_map.get(raw_cat, raw_cat.lower())

            master_registry[node_id] = entry
            
        return master_registry