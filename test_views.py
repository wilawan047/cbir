from app import app, mysql
from flask import jsonify

@app.route('/test/views')
def test_views():
    with app.app_context():
        cur = mysql.connection.cursor()
        
        # Get today's views count
        cur.execute("""
            SELECT COUNT(*) 
            FROM house_views 
            WHERE DATE(created_at) = CURDATE()
        """)
        today_count = cur.fetchone()[0]
        
        # Get total views
        cur.execute("SELECT COUNT(*) FROM house_views")
        total_count = cur.fetchone()[0]
        
        # Get latest views
        cur.execute("""
            SELECT v.id, h.h_title, v.created_at, v.ip_address
            FROM house_views v
            JOIN house h ON v.house_id = h.h_id
            ORDER BY v.created_at DESC
            LIMIT 5
        """)
        latest_views = [
            {'id': row[0], 'house': row[1], 'time': str(row[2]), 'ip': row[3]}
            for row in cur.fetchall()
        ]
        
        return jsonify({
            'today_views': today_count,
            'total_views': total_count,
            'latest_views': latest_views
        })

if __name__ == '__main__':
    app.run(debug=True)
