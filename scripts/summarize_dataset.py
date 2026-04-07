import pandas as pd
import numpy as np

def summarize():
    data_path = 'data/final_dataset/chronos2_preprocessed_v2.csv'
    if not os.path.exists(data_path):
        print("Data not found.")
        return

    df = pd.read_csv(data_path)
    
    print(f"Total Rows: {len(df)}")
    print(f"Unique Items: {df['item_id'].nunique()}")
    print(f"Date Range: {df['date'].min()} to {df['date'].max()}")
    print(f"Target Statistics (arcsinh-transformed):")
    print(df['target'].describe())
    
    # List all columns for the dictionary
    print("\nColumns:")
    print(df.columns.tolist())

if __name__ == "__main__":
    import os
    summarize()
