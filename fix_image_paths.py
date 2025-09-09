import pymysql
import os

def fix_image_paths():
    # Connect to the database
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='projectdb',
        port=3307,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with conn.cursor() as cursor:
            # Get all house images
            cursor.execute("SELECT id, house_id, image_url FROM house_images")
            images = cursor.fetchall()
            
            for img in images:
                old_path = img['image_url']
                new_path = old_path
                
                # Fix the path if it starts with /static/
                if old_path.startswith('/static/'):
                    new_path = old_path[8:]  # Remove /static/ prefix
                
                # Update if path was changed
                if old_path != new_path:
                    print(f"Updating image {img['id']}: {old_path} -> {new_path}")
                    cursor.execute(
                        "UPDATE house_images SET image_url = %s WHERE id = %s",
                        (new_path, img['id'])
                    )
            
            # Commit the changes
            conn.commit()
            print("Image paths have been updated successfully!")
            
    finally:
        conn.close()

if __name__ == "__main__":
    fix_image_paths()
