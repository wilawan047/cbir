import os
import numpy as np
from app import app, mysql

def clean_up_features():
    with app.app_context():
        # Load the current features and filenames
        features_file = 'static/features/house_features.npy'
        filenames_file = 'static/features/filenames.npy'
        
        if not os.path.exists(features_file) or not os.path.exists(filenames_file):
            print("Feature files not found. Please run feature extraction first.")
            return
        
        print("Loading feature files...")
        features = np.load(features_file, allow_pickle=True)
        filenames = np.load(filenames_file, allow_pickle=True)
        
        print(f"Found {len(filenames)} entries in feature database")
        
        # Get all valid image URLs from the database
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                SELECT image_url 
                FROM house_images 
                WHERE image_url IS NOT NULL 
                AND image_url != ''
            """)
            db_images = cur.fetchall()
            valid_urls = set()
            
            for row in db_images:
                if not row[0]:
                    continue
                # Extract just the filename
                filename = os.path.basename(str(row[0]).split('/')[-1])
                # Check if file exists on disk
                possible_paths = [
                    os.path.join('static', 'uploads', filename),
                    os.path.join('static', 'uploads', os.path.basename(filename)),
                    filename
                ]
                if any(os.path.exists(path) for path in possible_paths):
                    valid_urls.add(filename)
            
            print(f"Found {len(valid_urls)} valid images in database")
            
            # Find which features to keep
            keep_indices = []
            for i, filename in enumerate(filenames):
                img_filename = os.path.basename(str(filename))
                if img_filename in valid_urls:
                    keep_indices.append(i)
            
            print(f"Keeping {len(keep_indices)} out of {len(filenames)} entries")
            
            if not keep_indices:
                print("No valid entries to keep!")
                return
            
            # Filter the arrays
            features = features[keep_indices]
            filenames = filenames[keep_indices]
            
            # Backup old files
            if os.path.exists(features_file):
                os.rename(features_file, f"{features_file}.bak")
            if os.path.exists(filenames_file):
                os.rename(filenames_file, f"{filenames_file}.bak")
            
            # Save the cleaned data
            np.save(features_file, features)
            np.save(filenames_file, filenames)
            
            print(f"Successfully updated feature database with {len(features)} entries")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            # Restore backup if exists
            if os.path.exists(f"{features_file}.bak"):
                os.rename(f"{features_file}.bak", features_file)
            if os.path.exists(f"{filenames_file}.bak"):
                os.rename(f"{filenames_file}.bak", filenames_file)
            print("Restored original files due to error")
            
        finally:
            cur.close()

if __name__ == '__main__':
    with app.app_context():
        clean_up_features()
