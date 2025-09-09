import mysql.connector
from mysql.connector import Error

def check_data():
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
            
            # Check admins table
            cursor.execute("SELECT * FROM admins")
            admins = cursor.fetchall()
            print("\nAdmins table:")
            if admins:
                for admin in admins:
                    print(f"- ID: {admin[0]}, Username: {admin[1]}, Email: {admin[3]}, Role: {admin[6]}, Status: {admin[7]}")
            else:
                print("No records found in admins table")
            
            # Check project table
            cursor.execute("SELECT * FROM project")
            projects = cursor.fetchall()
            print("\nProject table:")
            if projects:
                for project in projects:
                    print(f"- ID: {project[0]}, Name: {project[1]}, Description: {project[2]}")
            else:
                print("No records found in project table")
            
            # Check house_type table
            cursor.execute("SELECT * FROM house_type")
            house_types = cursor.fetchall()
            print("\nHouse Type table:")
            if house_types:
                for house_type in house_types:
                    print(f"- ID: {house_type[0]}, Name: {house_type[1]}, Description: {house_type[2]}")
            else:
                print("No records found in house_type table")
            
            # Check house table
            cursor.execute("SELECT * FROM house")
            houses = cursor.fetchall()
            print("\nHouse table:")
            if houses:
                for house in houses:
                    print(f"- ID: {house[0]}, Title: {house[1]}, Description: {house[2]}, Price: {house[4]}, Type ID: {house[5]}, Project ID: {house[6]}")
            else:
                print("No records found in house table")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nMySQL connection closed.")

if __name__ == "__main__":
    check_data() 