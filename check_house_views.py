from app import mysql

def check_house_views_table():
    cursor = mysql.connection.cursor()
    try:
        # Check if table exists
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'projectdb' AND TABLE_NAME = 'house_views'
        """)
        
        print("\n=== house_views Table Structure ===")
        print(f"{'Column':<20} {'Type':<15} {'Nullable':<10} {'Key':<5} {'Default'}")
        print("-" * 60)
        
        for col in cursor.fetchall():
            print(f"{col[0]:<20} {col[1]:<15} {col[2]:<10} {col[3] or '':<5} {col[4] or 'NULL'}")
            
    except Exception as e:
        print(f"Error checking house_views table: {str(e)}")
    finally:
        cursor.close()

if __name__ == "__main__":
    from app import app
    with app.app_context():
        check_house_views_table()
