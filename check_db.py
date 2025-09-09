import MySQLdb
import traceback
import sys
import io

# Set stdout to use UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_database():
    try:
        # Database connection parameters
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'projectdb',  # Updated to match your app's config
            'port': 3307,            # Added port from your app's config
            'autocommit': True
        }

        # Connect to the database
        connection = MySQLdb.connect(**db_config)
        cursor = connection.cursor()

        # Check if the project table exists
        cursor.execute("SHOW TABLES LIKE 'project'")
        table_exists = cursor.fetchone()
        print(f"Project table exists: {bool(table_exists)}")

        if table_exists:
            # Get table structure
            cursor.execute("DESCRIBE project")
            print("\nProject table structure:")
            for column in cursor.fetchall():
                print(column)
            
            # Get sample data
            cursor.execute("SELECT * FROM project LIMIT 5")
            print("\nSample project data (first 5 rows):")
            for row in cursor.fetchall():
                # Convert each field to string and handle encoding
                print("Row:")
                for i, field in enumerate(row):
                    try:
                        field_str = str(field) if field is not None else "NULL"
                        print(f"  Column {i+1}: {field_str}")
                    except UnicodeEncodeError:
                        print(f"  Column {i+1}: [binary or non-printable data]")

    except Exception as e:
        print(f"Error: {e}")
        print(traceback.format_exc())
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    check_database()
