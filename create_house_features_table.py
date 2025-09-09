import mysql.connector

# Replace with your actual database credentials
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "projectdb"
}


sql_query = """
CREATE TABLE IF NOT EXISTS house_features (
    f_id INT AUTO_INCREMENT PRIMARY KEY,
    f_name VARCHAR(100) NOT NULL,
    f_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

conn = None
cursor = None

try:
    print("Connecting to the database...")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    print("Executing CREATE TABLE statement for house_features...")
    cursor.execute(sql_query)
    conn.commit()

    print("Table 'house_features' processed successfully (created if it didn't exist).")

except mysql.connector.Error as err:
    print(f"Error: {err}")

finally:
    if cursor:
        cursor.close()
    if conn and conn.is_connected():
        conn.close()
        print("Database connection closed.")
