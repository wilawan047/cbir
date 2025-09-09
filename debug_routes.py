"""
Temporary debug routes for admin user management.
These should be removed after debugging is complete.
"""
from flask import session, redirect, url_for, flash
from app import mysql

@app.route('/debug/fix-session')
def debug_fix_session():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    current_user_id = session.get('admin_id')
    cur = mysql.connection.cursor()
    
    try:
        # Get the current user's role from the database
        cur.execute("SELECT role FROM admins WHERE id = %s", (current_user_id,))
        result = cur.fetchone()
        
        if result:
            # Update the session with the correct role
            session['admin_role'] = result[0]
            mysql.connection.commit()
            return f"Session updated. New role: {result[0]}"
        else:
            return "User not found in database"
            
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cur.close()

@app.route('/debug/check-session')
def debug_check_session():
    if 'admin_id' not in session:
        return "Not logged in"
    
    return {
        'session_id': session.sid,
        'admin_id': session.get('admin_id'),
        'admin_username': session.get('admin_username'),
        'admin_role': session.get('admin_role'),
        'is_super_admin': session.get('admin_role') == 'superadmin'
    }
