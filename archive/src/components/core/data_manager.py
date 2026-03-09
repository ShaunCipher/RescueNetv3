import pandas as pd
import os

class DataManager:
    def __init__(self):
        # Determine the base directory (adjusting for src/components/core structure)
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.data_dir = os.path.join(self.base_dir, 'data')
        
        self.nodes_df = pd.DataFrame()
        self.edges_df = pd.DataFrame()
        self.all_data = pd.DataFrame()
        self.master_registry = {}

    def load_and_clean_data(self):
        # 1. Load Core Infrastructure
        self.nodes_df = pd.read_csv(os.path.join(self.data_dir, 'nodes.csv'))
        self.edges_df = pd.read_csv(os.path.join(self.data_dir, 'edges.csv'))
        
        # Standardize node/edge headers
        self.nodes_df.columns = self.nodes_df.columns.str.strip()
        self.edges_df.columns = self.edges_df.columns.str.strip()

        # Ensure ID keys are consistent (avoid int/str mismatches on merge)
        if 'id' in self.nodes_df.columns:
            self.nodes_df['id'] = self.nodes_df['id'].astype(str).str.strip()
        if 'id' in self.edges_df.columns:
            self.edges_df['id'] = self.edges_df['id'].astype(str).str.strip()

        # 2. Define Modular Facility Files
        facility_files = [
            'hospitals.csv', 'firestations.csv', 'policestations.csv', 
            'drrm.csv', 'schools.csv', 'churches.csv'
        ]

        frames = []
        for filename in facility_files:
            path = os.path.join(self.data_dir, filename)
            if os.path.exists(path):
                df = pd.read_csv(path)
                # Clean headers (fixes "occupants " vs "occupants")
                df.columns = df.columns.str.strip()

                # Normalize IDs to match nodes_df (avoid int/str mismatch on merge)
                if 'id' in df.columns:
                    df['id'] = df['id'].astype(str).str.strip()

                # Merge with nodes_df to get X, Y coordinates based on ID
                df = df.merge(self.nodes_df[['id', 'x', 'y']], on='id', how='left')
                
                frames.append(df)
                
                # Store in registry for the Inspector to use
                for _, row in df.iterrows():
                    try:
                        key = int(row['id'])
                    except (ValueError, TypeError):
                        # Skip invalid/missing IDs
                        continue
                    self.master_registry[key] = row.to_dict()

        # 3. Create the master dataframe for plotting/filtering
        if frames:
            self.all_data = pd.concat(frames, ignore_index=True)
            # Ensure category is lowercase for logic consistency
            self.all_data['category'] = self.all_data['category'].str.lower()
        else:
            self.all_data = pd.DataFrame(columns=['id', 'name', 'category', 'x', 'y'])

        return self.nodes_df, self.all_data, self.master_registry