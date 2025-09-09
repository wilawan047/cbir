import os
import numpy as np
from app import app, mysql
from cbir_search import extract_feature
from pathlib import Path

def regenerate_features():
    with app.app_context():
        print("Starting feature regeneration...")
        
        # Output directories
        features_dir = os.path.join('static', 'features')
        os.makedirs(features_dir, exist_ok=True)
        
        features_file = os.path.join(features_dir, 'house_features.npy')
        filenames_file = os.path.join(features_dir, 'filenames.npy')
        
        # Get all valid images from the database
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                SELECT hi.id, hi.image_url, h.h_id, h.h_title
                FROM house_images hi
                JOIN house h ON hi.house_id = h.h_id
                WHERE hi.image_url IS NOT NULL 
                AND hi.image_url != ''
            """)
            
            db_images = cur.fetchall()
            print(f"Found {len(db_images)} images in the database")
            
            valid_images = []
            valid_filenames = []
            
            for img_id, img_url, house_id, house_title in db_images:
                if not img_url:
                    continue
                    
                # Extract just the filename
                filename = os.path.basename(str(img_url).split('/')[-1])
                
                # Check if file exists in any possible location
                possible_paths = [
                    os.path.join('static', 'uploads', filename),
                    os.path.join('static', 'uploads', os.path.basename(filename)),
                    filename,
                    os.path.basename(filename)
                ]
                
                img_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        img_path = path
                        break
                
                if not img_path:
                    print(f"[WARNING] Image not found: {filename}")
                    continue
                
                try:
                    # Extract features
                    features = extract_feature(img_path)
                    valid_images.append(features)
                    valid_filenames.append(filename)
                    print(f"Processed: {filename}")
                except Exception as e:
                    print(f"[ERROR] Failed to process {filename}: {e}")
            
            if not valid_images:
                print("No valid images found to process!")
                return
            
            # Convert to numpy arrays
            features_array = np.array(valid_images)
            filenames_array = np.array(valid_filenames)
            
            # Backup old files if they exist
            if os.path.exists(features_file):
                backup_path = f"{features_file}.bak"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(features_file, backup_path)
                
            if os.path.exists(filenames_file):
                backup_path = f"{filenames_file}.bak"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(filenames_file, backup_path)
            
            # Save the new feature database
            np.save(features_file, features_array)
            np.save(filenames_file, filenames_array)
            
            print(f"\nSuccessfully regenerated feature database with {len(valid_images)} images")
            
        except Exception as e:
            print(f"[ERROR] Failed to regenerate features: {e}")
            # Try to restore backups if they exist
            if os.path.exists(f"{features_file}.bak") and not os.path.exists(features_file):
                os.rename(f"{features_file}.bak", features_file)
            if os.path.exists(f"{filenames_file}.bak") and not os.path.exists(filenames_file):
                os.rename(f"{filenames_file}.bak", filenames_file)
            print("Restored original feature files due to error")
            
        finally:
            cur.close()

if __name__ == '__main__':
    with app.app_context():
        regenerate_features()
