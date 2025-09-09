import mysql.connector
from mysql.connector import Error

def add_description_column():
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='projectdb'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("Connected to MySQL server")
            
            # Add p_description column if it doesn't exist
            cursor.execute("""
                ALTER TABLE project 
                ADD COLUMN IF NOT EXISTS p_description TEXT 
                AFTER p_name
            """)
            connection.commit()
            print("Added p_description column to project table")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    add_description_column() 