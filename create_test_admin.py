import pymysql
from werkzeug.security import generate_password_hash

def create_test_admin():
    try:
        # Connect to the database
        conn = pymysql.connect(
            host='localhost',
            port=3307,
            user='root',
            password='',
            database='projectdb'
        )
        
        with conn.cursor() as cursor:
            # Check if test admin already exists
            cursor.execute("SELECT * FROM admins WHERE username = 'testadmin'")
            if cursor.fetchone():
                print("Test admin already exists. Username: testadmin")
                return
            
            # Create test admin
            password_hash = generate_password_hash('test1234')
            cursor.execute("""
                INSERT INTO admins (username, password, email, first_name, last_name, role, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'active')
            """, ('testadmin', password_hash, 'test@example.com', 'Test', 'Admin', 'admin'))
            
            conn.commit()
            print("Test admin created successfully!")
            print("Username: testadmin")
            print("Password: test1234")
            
    except pymysql.Error as e:
        print(f"Error creating test admin: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == "__main__":
    create_test_admin()
