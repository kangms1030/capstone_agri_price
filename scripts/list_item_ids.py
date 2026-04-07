import pandas as pd
import os

df = pd.read_csv('data/final_dataset/chronos2_final_dataset.csv')
unique_ids = df['item_id'].unique().tolist()
print(unique_ids)
