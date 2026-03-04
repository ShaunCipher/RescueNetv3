import pandas as pd
import os

def process_nodes(file_path):
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    # 1. Load the node data
    df = pd.read_csv(file_path)
    
    # 2. Identify target columns
    target_cols = ['x', 'y']
    
    # Verify columns exist
    if all(col in df.columns for col in target_cols):
        # 3. Round to 2 decimal places
        # Use .round(2) and ensure they stay as floats
        df[target_cols] = df[target_cols].round(2)
        
        # 4. Save the result
        # We'll overwrite or save as a 'cleaned' version
        output_path = file_path.replace('.csv', '_formatted.csv')
        df.to_csv(output_path, index=False)
        
        print(f"--- Process Complete ---")
        print(f"Input: {file_path}")
        print(f"Output: {output_path}")
        print("\nPreview of formatted data:")
        print(df[target_cols].head())
    else:
        print(f"Error: Columns 'x' and 'y' not found. Available: {list(df.columns)}")

# Execute for your specific file
process_nodes('data/nodes.csv')