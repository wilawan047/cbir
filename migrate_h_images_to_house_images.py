import os
from app import app, mysql

# This script migrates h_image from house to house_images as is_main=1 if not already present.
def migrate_h_images_to_house_images():
    cur = mysql.connection.cursor()
    # Get all houses with h_image set
    cur.execute("SELECT h_id, h_image FROM house WHERE h_image IS NOT NULL AND h_image != ''")
    houses = cur.fetchall()
    migrated = 0
    for h_id, h_image in houses:
        # Check if this image is already in house_images for this house
        cur.execute("SELECT COUNT(*) FROM house_images WHERE house_id = %s AND image_url = %s", (h_id, h_image))
        exists = cur.fetchone()[0]
        if not exists:
            # Insert as main image
            image_url = h_image
            if not image_url.startswith('/static/uploads/'):
                image_url = '/static/uploads/' + image_url
            cur.execute("INSERT INTO house_images (house_id, image_url, is_main) VALUES (%s, %s, 1)", (h_id, image_url))
            migrated += 1
    mysql.connection.commit()
    cur.close()
    print(f"Migrated {migrated} images from house.h_image to house_images.")

if __name__ == "__main__":
    with app.app_context():
        migrate_h_images_to_house_images() 