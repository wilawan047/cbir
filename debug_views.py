from app import mysql

def check_house_views():
    try:
        cur = mysql.connection.cursor()
        
        # Check if table exists
        cur.execute("SHOW TABLES LIKE 'house_views'")
        table_exists = cur.fetchone()
        
        if not table_exists:
            return "Error: house_views table does not exist"
        
        # Get table structure
        cur.execute("DESCRIBE house_views")
        structure = cur.fetchall()
        
        # Get row count for today
        cur.execute("SELECT COUNT(*) FROM house_views WHERE DATE(created_at) = CURDATE()")
        today_count = cur.fetchone()[0]
        
        # Get total row count
        cur.execute("SELECT COUNT(*) FROM house_views")
        total_count = cur.fetchone()[0]
        
        # Get some sample data
        cur.execute("SELECT * FROM house_views ORDER BY created_at DESC LIMIT 5")
        sample_data = cur.fetchall()
        
        return {
            'table_exists': True,
            'structure': structure,
            'today_count': today_count,
            'total_count': total_count,
            'sample_data': sample_data
        }
        
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if 'cur' in locals():
            cur.close()

# For testing
if __name__ == '__main__':
    from app import app
    with app.app_context():
        result = check_house_views()
        import pprint
        pprint.pprint(result)
