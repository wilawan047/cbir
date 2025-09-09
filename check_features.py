import numpy as np
import os

# Paths
features_path = os.path.join('static', 'features', 'house_features.npy')
filenames_path = os.path.join('static', 'features', 'filenames.npy')

def check_file(path, name):
    print(f"\n--- {name} ---")
    if not os.path.exists(path):
        print(f"File does not exist: {path}")
        return None
    
    try:
        data = np.load(path, allow_pickle=True)
        print(f"File loaded successfully")
        print(f"Type: {type(data)}")
        if hasattr(data, 'shape'):
            print(f"Shape: {data.shape}")
        print(f"Size: {len(data) if hasattr(data, '__len__') else 'N/A'}")
        if len(data) > 0:
            print(f"First item type: {type(data[0])}")
            print(f"First item value: {data[0]}")
        return data
    except Exception as e:
        print(f"Error loading {name}: {str(e)}")
        return None

print("Checking feature files...")
features = check_file(features_path, "Features")
filenames = check_file(filenames_path, "Filenames")

if features is not None and filenames is not None:
    print("\n--- Data Consistency Check ---")
    if len(features) == len(filenames):
        print(f"[OK] Features and filenames have matching lengths: {len(features)}")
    else:
        print(f"[ERROR] Mismatch in data lengths - Features: {len(features)}, Filenames: {len(filenames)}")

print("\nTest complete.")
