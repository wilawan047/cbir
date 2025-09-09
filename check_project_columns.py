import pymysql

# Connect to the database
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='projectdb',
    port=3307
)

try:
    with connection.cursor() as cursor:
        # Get column information for the project table
        cursor.execute("SHOW COLUMNS FROM project")
        columns = cursor.fetchall()
        
        print("Columns in project table:")
        for column in columns:
            print(f"- {column[0]} ({column[1]})")
            
        # Check if p_description exists
        column_names = [col[0] for col in columns]
        print("\nChecking for p_description column:")
        print(f"'p_description' in columns: {'p_description' in column_names}")
        
        # Show first row as sample
        cursor.execute("SELECT * FROM project LIMIT 1")
        row = cursor.fetchone()
        if row:
            print("\nSample row data:")
            for i, col in enumerate(cursor.description):
                print(f"- {col[0]}: {row[i]}")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    connection.close()
