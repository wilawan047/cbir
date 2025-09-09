from app import app, mysql

def check_house_table():
    with app.app_context():
        cursor = mysql.connection.cursor()
        try:
            # Check if table exists
            cursor.execute("SHOW TABLES LIKE 'house'")
            if not cursor.fetchone():
                print("House table does not exist")
                return
                
            # Get table structure
            cursor.execute("DESCRIBE house")
            print("\n=== House Table Structure ===")
            print(f"{'Field':<30} {'Type':<20} {'Null':<10} {'Key':<10} {'Default'}")
            print("-" * 80)
            
            for col in cursor.fetchall():
                print(f"{col[0]:<30} {col[1]:<20} {col[2]:<10} {col[3] or '':<10} {col[4] or 'NULL'}")
            
            # Check indexes
            cursor.execute("SHOW INDEX FROM house")
            print("\n=== Indexes ===")
            for idx in cursor.fetchall():
                print(f"Index: {idx[2]} on {idx[4]} ({idx[3]})")
                
        except Exception as e:
            print(f"Error checking house table: {str(e)}")
        finally:
            cursor.close()

if __name__ == "__main__":
    check_house_table()
