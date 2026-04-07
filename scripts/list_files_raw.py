import os

files = os.listdir('data/dataset_refined')
# Try to decode if they are bytes, but os.listdir usually returns strings in Python 3.
# Let's just print them one by one.
for f in files:
    print(f)
