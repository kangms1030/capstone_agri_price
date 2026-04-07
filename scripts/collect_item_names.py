import os
import glob

# Try to decode the filenames in the dataset directory
dataset_dir = 'data/dataset'
files = glob.glob(os.path.join(dataset_dir, '*.csv'))

decoded_names = []
for f in files:
    basename = os.path.basename(f).replace('.csv', '')
    # The basename we got from os.listdir or glob might be corrupted if misinterpreted.
    # Python's os.listdir on Windows usually returns the correct Unicode string.
    # If it's already Unicode but looks "broken", it might be a double-encoding issue.
    # Let's just print it and try to find its "clean" representation.
    decoded_names.append(basename)

# Print unique names to see what we have
unique_names = sorted(list(set(decoded_names)))
for name in unique_names:
    print(name)
