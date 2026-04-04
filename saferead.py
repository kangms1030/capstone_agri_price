import pandas as pd
df = pd.read_excel(r'c:\Users\minsoo\Desktop\capstone\backend\data\cabbage.xlsx')
cols = df.columns.tolist()
print("Columns:", [c.encode('unicode_escape').decode() for c in cols])
print(df.head(10).to_string(index=False))
