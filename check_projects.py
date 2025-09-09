import pymysql

# Connect to the database
try:
    conn = pymysql.connect(
        host='localhost',
        port=3307,
        user='root',
        password='',
        database='projectdb'
    )
    
    with conn.cursor() as cursor:
        # Check if project table exists
        cursor.execute("SHOW TABLES LIKE 'project'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("Project table exists.")
            # Check number of projects
            cursor.execute("SELECT COUNT(*) FROM project")
            count = cursor.fetchone()[0]
            print(f"Number of projects: {count}")
            
            # Show first few projects if they exist
            if count > 0:
                cursor.execute("SELECT * FROM project LIMIT 5")
                print("\nSample projects:")
                for row in cursor.fetchall():
                    print(f"ID: {row[0]}, Name: {row[1]}")
        else:
            print("Project table does not exist.")
            
except pymysql.Error as e:
    print(f"Error connecting to MySQL: {e}")
    
finally:
    if 'conn' in locals() and conn.open:
        conn.close()
