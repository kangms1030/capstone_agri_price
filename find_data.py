import os
import glob
import pandas as pd

base = r"c:\Users\minsoo\Desktop\capstone"
files = glob.glob(os.path.join(base, "**", "data", "**", "*.*"), recursive=True)
files = [f for f in files if "ari_price" in f or f.endswith(".csv") or f.endswith(".xls") or f.endswith(".xlsx")]
print("Found data files:")
for f in files:
    print(f)
    print("--- First 5 rows ---")
    try:
        if f.endswith('.csv'):
            df = pd.read_csv(f)
        else:
            df = pd.read_excel(f)
        print(df.head())
        print("\nColumns:", df.columns.tolist())
    except Exception as e:
        print("Error reading:", e)
    print("\n")
