import os

files = os.listdir('data/dataset')
for f in files[:10]: # Just first 10
    print(f"{f}: {f.encode('cp949', errors='replace').hex()}")
    try:
        # Try decoding as CP949 if it was read as Latin-1 or something
        print(f"Decoded (CP949): {f.encode('latin1').decode('cp949')}")
    except:
        pass
