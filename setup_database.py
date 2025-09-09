import mysql.connector
from mysql.connector import Error

def setup_database():
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("Connected to MySQL server")
            
            # Create database if not exists
            cursor.execute("CREATE DATABASE IF NOT EXISTS projectdb")
            print("Database 'projectdb' created or already exists")
            
            cursor.execute("USE projectdb")
            print("Using database 'projectdb'")
            
            # Create admins table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'admin',
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Table 'admins' created or already exists")
            
            # Create project table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project (
                    p_id INT AUTO_INCREMENT PRIMARY KEY,
                    p_name VARCHAR(100) NOT NULL,
                    p_description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Table 'project' created or already exists")
            
            # Create house_type table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS house_type (
                    t_id INT AUTO_INCREMENT PRIMARY KEY,
                    t_name VARCHAR(100) NOT NULL,
                    t_description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Table 'house_type' created or already exists")
            
            # Create house table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS house (
                    h_id INT AUTO_INCREMENT PRIMARY KEY,
                    h_title VARCHAR(100) NOT NULL,
                    h_description TEXT,
                    h_image VARCHAR(255),
                    price DECIMAL(10,2),
                    t_id INT,
                    p_id INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (t_id) REFERENCES house_type(t_id) ON DELETE SET NULL,
                    FOREIGN KEY (p_id) REFERENCES project(p_id) ON DELETE SET NULL
                )
            """)
            print("Table 'house' created or already exists")
            
            # Verify tables exist
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("\nExisting tables in database:")
            for table in tables:
                print(f"- {table[0]}")
            
            connection.commit()
            print("\nDatabase and tables created successfully!")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    setup_database() 