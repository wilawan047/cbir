import sys
import os
import time
import re
import locale
import io
import traceback
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# Set the locale to handle Thai characters
locale.setlocale(locale.LC_ALL, 'th_TH.UTF-8')

# Set default encoding to UTF-8 for console output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8') 

from flask import (
    Flask, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    flash, 
    session, 
    jsonify, 
    make_response, 
    send_file, 
    send_from_directory, 
    abort, 
    Response
)
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, validators
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from fpdf import FPDF, HTMLMixin
from io import BytesIO
import json
import uuid
import urllib.parse
import matplotlib
matplotlib.use('Agg') # Use the 'Agg' backend for Matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import tempfile

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps

# Import local modules
from dotenv import load_dotenv
from cbir_search import search_similar_images

# --- Load Environment Variables and Configure Flask App ---

# Load environment variables from a .env file
load_dotenv()
print(f"DEBUG: SECRET_KEY from .env: {os.getenv('SECRET_KEY')}")
# Custom JSON encoder to handle datetime objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

app = Flask(__name__)

# Core Flask Configuration
app.debug = True
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')

# Session configuration
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
    SESSION_REFRESH_EACH_REQUEST=True,
    REMEMBER_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    REMEMBER_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_SAMESITE='Lax'
)
app.json_encoder = CustomJSONEncoder

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def admin_required(f):
    """Decorator to ensure the user is logged in as an admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        if 'admin_id' not in session:
            logout_user()
            flash('กรุณาเข้าสู่ระบบเพื่อเข้าถึงหน้านี้', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
login_manager.login_message = 'กรุณาเข้าสู่ระบบเพื่อเข้าถึงหน้านี้'
login_manager.login_message_category = 'error'

# Flask-WTF CSRF Protection
csrf = CSRFProtect(app)

@login_manager.user_loader
def load_user(user_id):
    print(f"\n=== Loading user with ID: {user_id} ===")
    print(f"Session data in load_user: {dict(session)}")
    
    if not user_id or not user_id.isdigit():
        print(f"Invalid user_id: {user_id}")
        return None
        
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # First check if user exists and is active
        cur.execute("""
            SELECT id, username, password, email, first_name, last_name, role, status, created_at 
            FROM admins 
            WHERE id = %s AND status = 'active'
        """, (int(user_id),))
        
        admin = cur.fetchone()
        
        if not admin:
            print(f"No active admin found with id: {user_id}")
            return None
            
        # Create user object with all required fields
        user = admins(
            id=admin['id'],
            username=admin['username'],
            password=admin['password'],
            email=admin.get('email', ''),
            first_name=admin.get('first_name', ''),
            last_name=admin.get('last_name', ''),
            role=admin.get('role', 'admin'),
            status=admin.get('status', 'active'),
            created_at=admin.get('created_at')
        )
        
        # Verify the user object has the required attributes
        print(f"User object created - ID: {user.id}, Username: {user.username}")
        print(f"User is_authenticated: {user.is_authenticated}")
        print(f"User is_active: {user.is_active}")
        print(f"User is_anonymous: {user.is_anonymous}")
        
        return user
        
    except Exception as e:
        print(f"Error in load_user: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None
    finally:
        cur.close()

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'projectdb')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3307))

mysql = MySQL(app)

# --- PDFKit and Font Configuration ---

def setup_thai_font():
    """
    Configures xhtml2pdf to use a local font that supports Thai characters.
    """
    try:
        # A list of common fonts that support Thai characters on Windows systems
        thai_fonts = ['THSarabunNew.ttf', 'THSarabun.ttf', 'THSarabunNew Bold.ttf', 'THSarabun Bold.ttf']
        font_found = False
        
        for font_name in thai_fonts:
            font_path = None
            if sys.platform.startswith('win'):
                font_dirs = [
                    os.path.join(os.environ.get('WINDIR', ''), 'Fonts'),
                    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts')
                ]
                for font_dir in font_dirs:
                    full_path = os.path.join(font_dir, font_name)
                    if os.path.exists(full_path):
                        font_path = full_path
                        break
            
            if font_path:
                print(f"Found Thai font at: {font_path}")
                from xhtml2pdf.default import DEFAULT_FONT
                from reportlab.pdfbase.ttfonts import TTFont
                from reportlab.pdfbase import pdfmetrics
                
                try:
                    pdfmetrics.registerFont(TTFont('ThaiFont', font_path))
                    
                    if 'ThaiFont' not in DEFAULT_FONT:
                        DEFAULT_FONT['ThaiFont'] = DEFAULT_FONT['helvetica'].copy()
                        DEFAULT_FONT['ThaiFont']['helvetica'] = 'ThaiFont'
                        DEFAULT_FONT['ThaiFont']['symbol'] = 'ThaiFont'
                        DEFAULT_FONT['ThaiFont']['zapfdingbats'] = 'ThaiFont'
                        DEFAULT_FONT['ThaiFont']['TrueType'] = True
                        
                    font_found = True
                    print("Thai font registered successfully")
                    break
                except Exception as e:
                    print(f"Error registering font {font_path}: {str(e)}")
        
        if not font_found:
            print("Warning: No suitable Thai font found on the system. PDF may not display Thai characters correctly.")
            try:
                arial_unicode_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', 'ARIALUNI.TTF')
                if os.path.exists(arial_unicode_path):
                    from xhtml2pdf.default import DEFAULT_FONT
                    from reportlab.pdfbase import pdfmetrics
                    from reportlab.pdfbase.ttfonts import TTFont
                    pdfmetrics.registerFont(TTFont('ArialUnicode', arial_unicode_path))
                    DEFAULT_FONT['ArialUnicode'] = DEFAULT_FONT['helvetica'].copy()
                    DEFAULT_FONT['ArialUnicode']['helvetica'] = 'ArialUnicode'
                    print("Using Arial Unicode MS as fallback font")
                else:
                    print("No fallback font available")
            except Exception as e:
                print(f"Error setting up fallback font: {str(e)}")

    except Exception as e:
        print(f"Error in setup_thai_font: {str(e)}")

# Call the font setup function when the module loads
setup_thai_font()

app.config['PDFKIT_OPTIONS'] = {
    'enable-local-file-access': None,
    'encoding': 'UTF-8',
    'page-size': 'A4',
    'margin-top': '15mm',
    'margin-right': '10mm',
    'margin-bottom': '15mm',
    'margin-left': '10mm'
}

# --- File System Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
IMG_FOLDER = os.path.join(BASE_DIR, 'static', 'img')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMG_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['IMG_FOLDER'] = IMG_FOLDER

# Ensure all HTML responses are UTF-8
@app.after_request
def set_charset(response):
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

# --- Helper Functions ---
def serialize_data_for_json(data):
    """Helper function to serialize data for JSON responses"""
    if data is None:
        return None
    if isinstance(data, (str, int, float, bool)) or data is None:
        return data
    if isinstance(data, dict):
        return {k: serialize_data_for_json(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [serialize_data_for_json(item) for item in data]
    if hasattr(data, '__dict__'):
        return serialize_data_for_json(data.__dict__)
    if hasattr(data, 'isoformat'):  # Handle datetime objects
        return data.isoformat()
    return str(data)  # Fallback to string representation

def is_super_admin():
    return current_user.is_authenticated and hasattr(current_user, 'role') and current_user.role == 'superadmin'

def dict_fetchall(cursor):
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]

def dict_fetchone(cursor):
    desc = cursor.description
    data = cursor.fetchone()
    if data:
        return dict(zip([col[0] for col in desc], data))
    return None

def get_project_data(project_id):
    cur = None
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT p_id, p_name, description, a_id, address, p_image, created_at, updated_at FROM project WHERE p_id = %s"
        cur.execute(query, (project_id,))
        project_data = cur.fetchone()
        
        if project_data:
            project_data['p_image'] = project_data.get('p_image', 'default_project.jpg')
            project_data['address'] = project_data.get('address', '')
            project_data['description'] = project_data.get('description', '')
        return project_data
        
    except Exception as e:
        print(f"ERROR in get_project_data: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return None
    finally:
        if cur:
            cur.close()

# Admin model
class admins(UserMixin):
    def __init__(self, id, username, password, email, first_name, last_name, role, status, created_at):
        self.id = id
        self.username = username
        self.password = password
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.status = status
        self.created_at = created_at
        
    def get_id(self):
        return str(self.id)
        
    @property
    def is_active(self):
        return self.status == 'active'
        
    @property
    def is_authenticated(self):
        return True
        
    @property
    def is_anonymous(self):
        return False

class LoginForm(FlaskForm):
    username = StringField('Username', [validators.InputRequired()])
    password = PasswordField('Password', [validators.InputRequired()])

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
        
    # Clear any existing session data
    session.clear()
        
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        print(f"\nLogin attempt for user: {username}")
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cur.execute("SELECT * FROM admins WHERE username = %s", (username,))
            admin = cur.fetchone()
            print(f"Database query result: {admin}")

            if not admin or not check_password_hash(admin['password'], password):
                flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
                return render_template('login.html', form=form), 401

            if admin.get('status') != 'active':
                flash('บัญชีนี้ไม่ได้ใช้งานอยู่ กรุณาติดต่อผู้ดูแลระบบ', 'error')
                return redirect(url_for('login')), 403

            # Clear any existing session data
            session.clear()
            
            # Create user object
            user = admins(
                id=admin['id'],
                username=admin['username'],
                password=admin['password'],
                email=admin['email'],
                first_name=admin['first_name'],
                last_name=admin['last_name'],
                role=admin['role'],
                status=admin['status'],
                created_at=admin['created_at']
            )
            
            # Log the user in
            login_user(user, remember=True)
            
            # Set session variables
            session.permanent = True
            session['admin_id'] = admin['id']
            session['username'] = admin['username']
            session['role'] = admin['role']
            
            # Regenerate session to prevent session fixation
            session.modified = True
            
            flash('เข้าสู่ระบบสำเร็จ!', 'success')
            print(f"User {admin['username']} logged in successfully")
            print(f"Session after login: {dict(session)}")
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_dashboard'))

        except Exception as e:
            print(f"ERROR during login: {str(e)}")
            import traceback
            print(traceback.format_exc())
            flash('เกิดข้อผิดพลาดในการเข้าสู่ระบบ กรุณาลองอีกครั้ง', 'error')
            return render_template('login.html', form=form), 500
        finally:
            cur.close()
    
    # For GET requests or invalid form
    return render_template('login.html', form=form)


@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    print("\n=== Admin Dashboard Route Start ===")
    print(f"Current user: {current_user}")
    print(f"Is authenticated: {current_user.is_authenticated}")
    print(f"Session data: {dict(session)}")
        
    cur = mysql.connection.cursor()

    # Initialize all data variables to empty lists to ensure they are always defined and JSON serializable
    latest_houses = []
    houses_by_type_data = []
    houses_by_project_data = []
    house_types = []
    projects = []
    houses_by_status_data = []
    houses_status_distribution_data = []
    houses_by_bedrooms_data = []
    houses_by_bathrooms_data = []
    houses_by_living_area_data = []
    house_additions_data = []
    house_features = []
    selected_feature = None

    # Retrieve filter values from the request
    selected_type = request.form.get('house_type', None)
    selected_project = request.form.get('project', None)
    selected_feature = request.form.get('house_feature', None)

    try:
        # Apply filters to total counts
        total_houses_query = "SELECT COUNT(*) FROM house WHERE 1 = 1"
        total_houses_params = []
        if selected_type:
            total_houses_query += " AND t_id = %s"
            total_houses_params.append(selected_type)
        if selected_project:
            total_houses_query += " AND p_id = %s"
            total_houses_params.append(selected_project)
        if selected_feature:
            total_houses_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            total_houses_params.append(selected_feature)
        cur.execute(total_houses_query, total_houses_params)
        total_houses = cur.fetchone()[0]

        total_projects_query = "SELECT COUNT(*) FROM project p WHERE 1 = 1"
        total_projects_params = []
        if selected_type:
            total_projects_query += " AND EXISTS (SELECT 1 FROM house h WHERE h.p_id = p.p_id AND h.t_id = %s)"
            total_projects_params.append(selected_type)
        if selected_project:
            total_projects_query += " AND p.p_id = %s"
            total_projects_params.append(selected_project)
        if selected_feature:
            total_projects_query += " AND EXISTS (SELECT 1 FROM house h JOIN house_features hhf ON h.h_id = hhf.h_id WHERE h.p_id = p.p_id AND hhf.f_id = %s)"
            total_projects_params.append(selected_feature)
        cur.execute(total_projects_query, total_projects_params)
        total_projects = cur.fetchone()[0]

        total_types_query = "SELECT COUNT(*) FROM house_type ht WHERE 1 = 1"
        total_types_params = []
        if selected_type:
            total_types_query += " AND ht.t_id = %s"
            total_types_params.append(selected_type)
        if selected_project:
            total_types_query += " AND EXISTS (SELECT 1 FROM house h WHERE h.t_id = ht.t_id AND h.p_id = %s)"
            total_types_params.append(selected_project)
        if selected_feature:
            total_types_query += " AND EXISTS (SELECT 1 FROM house h JOIN house_features hhf ON h.h_id = hhf.h_id WHERE h.t_id = ht.t_id AND hhf.f_id = %s)"
            total_types_params.append(selected_feature)
        cur.execute(total_types_query, total_types_params)
        total_types = cur.fetchone()[0]

        # Latest Houses (by created_at)
        cur.execute("""
            SELECT h.h_id as id, h.h_title as title, h.h_description as description, h.price, h.bedrooms, h.bathrooms, h.living_area as area, h.t_id, h.p_id,
                   h.created_at, t.t_name as type_name, p.p_name as project_name
            FROM house h
            LEFT JOIN house_type t ON h.t_id = t.t_id
            LEFT JOIN project p ON h.p_id = p.p_id
            ORDER BY h.created_at DESC
            LIMIT 5
        """)
        latest_houses = dict_fetchall(cur)
        # Attach main_image_url for each house in latest_houses
        for house in latest_houses:
            cur.execute("SELECT image_url FROM house_images WHERE house_id = %s AND is_main = 1 LIMIT 1", (house['id'],))
            row = cur.fetchone()
            if row:
                url = row[0].lstrip('/')
                if not url.startswith('static/uploads/'):
                    url = 'static/uploads/' + url.split('/')[-1]
                house['main_image_url'] = '/' + url
            else:
                cur.execute("SELECT image_url FROM house_images WHERE house_id = %s LIMIT 1", (house['id'],))
                row = cur.fetchone()
                if row:
                    url = row[0].lstrip('/')
                    if not url.startswith('static/uploads/'):
                        url = 'static/uploads/' + url.split('/')[-1]
                    house['main_image_url'] = '/' + url
                else:
                    house['main_image_url'] = '/static/img/house_placeholder.jpg'
        latest_houses = serialize_data_for_json(latest_houses)

        # Most Recently Edited Houses (by updated_at, fallback to created_at)
        try:
            cur.execute("""
                SELECT h.h_id as id, h.h_title as title, h.h_description as description, h.price, h.bedrooms, h.bathrooms, h.living_area as area, h.t_id, h.p_id,
                       h.created_at, h.updated_at, t.t_name as type_name, p.p_name as project_name
                FROM house h
                LEFT JOIN house_type t ON h.t_id = t.t_id
                LEFT JOIN project p ON h.p_id = p.p_id
                ORDER BY h.updated_at DESC, h.created_at DESC
                LIMIT 8
            """)
            recently_edited_houses = dict_fetchall(cur)
        except Exception:
            cur.execute("""
                SELECT h.h_id as id, h.h_title as title, h.h_description as description, h.price, h.bedrooms, h.bathrooms, h.living_area as area, h.t_id, h.p_id,
                       h.created_at, t.t_name as type_name, p.p_name as project_name
                FROM house h
                LEFT JOIN house_type t ON h.t_id = t.t_id
                LEFT JOIN project p ON h.p_id = p.p_id
                ORDER BY h.created_at DESC
                LIMIT 8
            """)
            recently_edited_houses = dict_fetchall(cur)
        # Attach main_image_url for each house in recently_edited_houses
        for house in recently_edited_houses:
            cur.execute("SELECT image_url FROM house_images WHERE house_id = %s AND is_main = 1 LIMIT 1", (house['id'],))
            row = cur.fetchone()
            if row:
                url = row[0].lstrip('/')
                if not url.startswith('static/uploads/'):
                    url = 'static/uploads/' + url.split('/')[-1]
                house['main_image_url'] = '/' + url
            else:
                cur.execute("SELECT image_url FROM house_images WHERE house_id = %s LIMIT 1", (house['id'],))
                row = cur.fetchone()
                if row:
                    url = row[0].lstrip('/')
                    if not url.startswith('static/uploads/'):
                        url = 'static/uploads/' + url.split('/')[-1]
                    house['main_image_url'] = '/' + url
                else:
                    house['main_image_url'] = '/static/img/house_placeholder.jpg'
        recently_edited_houses = serialize_data_for_json(recently_edited_houses)

        # Set latest_houses for dashboard display
        latest_houses = recently_edited_houses[:5]

        # Get houses by type
        houses_by_type_query = """
            SELECT ht.t_name as name, COUNT(h.h_id) as house_count
            FROM house_type ht
            LEFT JOIN house h ON ht.t_id = h.t_id
            WHERE 1 = 1
        """
        houses_by_type_params = []

        if selected_project:
            houses_by_type_query += " AND h.p_id = %s"
            houses_by_type_params.append(selected_project)

        if selected_type:
            houses_by_type_query += " AND ht.t_id = %s"
            houses_by_type_params.append(selected_type)
        if selected_feature:
            houses_by_type_query += " AND h.h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            houses_by_type_params.append(selected_feature)

        houses_by_type_query += " GROUP BY ht.t_name"
        cur.execute(houses_by_type_query, houses_by_type_params)
        houses_by_type_data = dict_fetchall(cur)
        houses_by_type_data = serialize_data_for_json(houses_by_type_data)

        # Get houses by project
        houses_by_project_query = """
            SELECT p.p_name as name, COUNT(h.h_id) as house_count
            FROM project p
            LEFT JOIN house h ON p.p_id = h.p_id
            WHERE 1 = 1
        """
        houses_by_project_params = []

        if selected_type:
            houses_by_project_query += " AND h.t_id = %s"
            houses_by_project_params.append(selected_type)
        
        if selected_project:
            houses_by_project_query += " AND p.p_id = %s"
            houses_by_project_params.append(selected_project)
        if selected_feature:
            houses_by_project_query += " AND h.h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            houses_by_project_params.append(selected_feature)

        houses_by_project_query += " GROUP BY p.p_name"
        cur.execute(houses_by_project_query, houses_by_project_params)
        houses_by_project_data = dict_fetchall(cur)
        houses_by_project_data = serialize_data_for_json(houses_by_project_data)

        # Get filter options
        cur.execute("SELECT t_id as id, t_name as name FROM house_type")
        house_types = dict_fetchall(cur)
        house_types = serialize_data_for_json(house_types)
        cur.execute("SELECT p_id as id, p_name as name FROM project")
        projects = dict_fetchall(cur)
        projects = serialize_data_for_json(projects)

        # Get house features for filter
        cur.execute("SELECT f_id as id, f_name as name FROM house_features")
        house_features = dict_fetchall(cur)
        house_features = serialize_data_for_json(house_features)

        # Fetch data for Houses by Status (assuming a 'status' column exists)
        houses_status_query = "SELECT status, COUNT(h_id) as count FROM house WHERE 1=1"
        houses_status_params = []
        if selected_type:
            houses_status_query += " AND t_id = %s"
            houses_status_params.append(selected_type)
        if selected_project:
            houses_status_query += " AND p_id = %s"
            houses_status_params.append(selected_project)
        if selected_feature:
            houses_status_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            houses_status_params.append(selected_feature)
        houses_status_query += " GROUP BY status"
        cur.execute(houses_status_query, houses_status_params)
        houses_by_status_data = dict_fetchall(cur)
        houses_by_status_data = serialize_data_for_json(houses_by_status_data)

        # Fetch data for House Status Distribution Chart
        # This data is the same as houses_by_status_data, just needed for the pie chart
        houses_status_distribution_data = houses_by_status_data

        # Fetch data for Houses by Bedrooms
        houses_bedrooms_query = "SELECT bedrooms as name, COUNT(h_id) as count FROM house WHERE bedrooms IS NOT NULL"
        houses_bedrooms_params = []
        if selected_type:
            houses_bedrooms_query += " AND t_id = %s"
            houses_bedrooms_params.append(selected_type)
        if selected_project:
            houses_bedrooms_query += " AND p_id = %s"
            houses_bedrooms_params.append(selected_project)
        if selected_feature:
            houses_bedrooms_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            houses_bedrooms_params.append(selected_feature)
        houses_bedrooms_query += " GROUP BY bedrooms ORDER BY bedrooms"
        cur.execute(houses_bedrooms_query, houses_bedrooms_params)
        houses_by_bedrooms_data = dict_fetchall(cur)
        houses_by_bedrooms_data = serialize_data_for_json(houses_by_bedrooms_data)

        # Fetch data for Houses by Bathrooms
        houses_bathrooms_query = "SELECT bathrooms as name, COUNT(h_id) as count FROM house WHERE bathrooms IS NOT NULL"
        houses_bathrooms_params = []
        if selected_type:
            houses_bathrooms_query += " AND t_id = %s"
            houses_bathrooms_params.append(selected_type)
        if selected_project:
            houses_bathrooms_query += " AND p_id = %s"
            houses_bathrooms_params.append(selected_project)
        if selected_feature:
            houses_bathrooms_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            houses_bathrooms_params.append(selected_feature)
        houses_bathrooms_query += " GROUP BY bathrooms ORDER BY bathrooms"
        cur.execute(houses_bathrooms_query, houses_bathrooms_params)
        houses_by_bathrooms_data = dict_fetchall(cur)
        houses_by_bathrooms_data = serialize_data_for_json(houses_by_bathrooms_data)

        # Fetch data for Houses by Living Area
        houses_living_area_query = "SELECT living_area as name, COUNT(h_id) as count FROM house WHERE living_area IS NOT NULL"
        houses_living_area_params = []
        if selected_type:
            houses_living_area_query += " AND t_id = %s"
            houses_living_area_params.append(selected_type)
        if selected_project:
            houses_living_area_query += " AND p_id = %s"
            houses_living_area_params.append(selected_project)
        if selected_feature:
            houses_living_area_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            houses_living_area_params.append(selected_feature)
        houses_living_area_query += " GROUP BY living_area ORDER BY living_area"
        cur.execute(houses_living_area_query, houses_living_area_params)
        houses_by_living_area_data = dict_fetchall(cur)
        houses_by_living_area_data = serialize_data_for_json(houses_by_living_area_data)

        # Fetch data for House Additions Over Time Chart (assuming 'created_at' column and focusing on last 30 days)
        # This query counts houses created per day for the last 30 days
        house_additions_query = "SELECT DATE(created_at) as date, COUNT(h_id) as count FROM house WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
        house_additions_params = []
        if selected_type:
            house_additions_query += " AND t_id = %s"
            house_additions_params.append(selected_type)
        if selected_project:
            house_additions_query += " AND p_id = %s"
            house_additions_params.append(selected_project)
        if selected_feature:
            house_additions_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            house_additions_params.append(selected_feature)
        house_additions_query += " GROUP BY DATE(created_at) ORDER BY DATE(created_at)"
        cur.execute(house_additions_query, house_additions_params)
        house_additions_data = dict_fetchall(cur)
        house_additions_data = serialize_data_for_json(house_additions_data)

        # Fetch today's view count
        cur.execute("SELECT COUNT(*) FROM house_views WHERE DATE(created_at) = CURDATE()")
        todays_views = cur.fetchone()[0]

        return render_template(
            'admin_dashboard.html',
            total_houses=total_houses,
            total_projects=total_projects,
            total_types=total_types,
            todays_views=todays_views,
            latest_houses=latest_houses,
            recently_edited_houses=recently_edited_houses,
            house_types=house_types,
            projects=projects,
            selected_type=selected_type,
            selected_project=selected_project,
            houses_by_type_data=houses_by_type_data,
            houses_by_project_data=houses_by_project_data,
            houses_by_status_data=houses_by_status_data,
            houses_status_distribution_data=houses_status_distribution_data,
            houses_by_bedrooms_data=houses_by_bedrooms_data,
            houses_by_bathrooms_data=houses_by_bathrooms_data,
            houses_by_living_area_data=houses_by_living_area_data,
            house_additions_data=house_additions_data,
            house_features=house_features,
            selected_feature=selected_feature
        )
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('login'))
    finally:
        cur.close()

class PDF(FPDF, HTMLMixin):
    def header(self):
        # Top bar (lighter blue)
        self.set_fill_color(240, 249, 255)  # #f0f9ff
        self.rect(0, 0, self.w, 30, 'F')  # Increased height to accommodate logo
        
        # Add company logo (left side)
        logo_path = os.path.join('static', 'img', 'logo24.png')
        if os.path.exists(logo_path):
            self.image(logo_path, x=10, y=5, h=20)  # Adjust position and size as needed
        
        # Add report title (centered)
        self.set_xy(0, 8)
        self.set_font('NotoSansThai', 'B', 16)
        self.set_text_color(37, 99, 235)  # #2563eb
        self.cell(0, 10, 'BAANTANG Dashboard Report', 0, 1, 'C')
        
        # Add date (right side)
        self.set_xy(-50, 8)
        self.set_font('NotoSansThai', '', 10)
        self.cell(0, 10, datetime.now().strftime('%d/%m/%Y %H:%M'), 0, 0, 'R')
        
        self.ln(12)  # Adjust spacing below header
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font('NotoSansThai', '', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    def chapter_title(self, title, color=(37, 99, 235)):
        self.set_font('NotoSansThai', 'B', 12)
        self.set_text_color(*color)
        self.cell(0, 10, title, 0, 1, 'L')
        self.set_text_color(50, 50, 50)
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('NotoSansThai', '', 10)
        self.set_text_color(70, 70, 70)
        self.multi_cell(0, 6, body)
        self.ln()

    def add_table(self, header, data, col_widths):
        self.set_fill_color(224, 242, 254)  # Light blue for header
        self.set_text_color(37, 99, 235)  # Blue text for header
        self.set_font('NotoSansThai', 'B', 10)
        for i, col in enumerate(header):
            self.cell(col_widths[i], 7, col, 1, 0, 'C', 1)
        self.ln()
        self.set_font('NotoSansThai', '', 10)
        self.set_text_color(0)
        fill = False
        for row in data:
            self.set_fill_color(245, 245, 245) if fill else self.set_fill_color(255, 255, 255)
            for i, item in enumerate(row):
                self.cell(col_widths[i], 6, str(item), 1, 0, 'L', fill)
            self.ln()
            fill = not fill

    def draw_stat_card(self, x, y, w, h, title, value, color_bg, color_text=(37, 99, 235)):
        self.set_xy(x, y)
        self.set_fill_color(*color_bg)
        self.rounded_rect(x, y, w, h, 3, 'F')
        self.set_xy(x, y + 4)
        self.set_font('NotoSansThai', '', 10)
        self.set_text_color(*color_text)
        self.cell(w, 6, title, 0, 2, 'C')
        self.set_font('NotoSansThai', 'B', 16)
        self.cell(w, 10, str(value), 0, 0, 'C')
        self.set_text_color(0, 0, 0)

    def rounded_rect(self, x, y, w, h, r, style=''):
        # Draw a rounded rectangle (helper for stat cards)
        op = {'F': 'f', 'FD': 'B', 'DF': 'B'}.get(style, 'S')
        self._out(f'{x} {self.h - y} m')
        self._Arc(x + r, self.h - y, x, self.h - (y + r), x, self.h - (y + r))
        self._out(f'{x} {self.h - (y + h - r)} l')
        self._Arc(x, self.h - (y + h - r), x + r, self.h - (y + h), x + r, self.h - (y + h))
        self._out(f'{x + w - r} {self.h - (y + h)} l')
        self._Arc(x + w - r, self.h - (y + h), x + w, self.h - (y + h - r), x + w, self.h - (y + h - r))
        self._out(f'{x + w} {self.h - (y + r)} l')
        self._Arc(x + w, self.h - (y + r), x + w - r, self.h - y, x + w - r, self.h - y)
        self._out(f'{x + r} {self.h - y} l')
        self._out(op)

    def _Arc(self, x1, y1, x2, y2, x3, y3):
        h = 4 / 3 * (2 ** 0.5 - 1) * (x2 - x1)
        self._out(f'{x1 + h} {y1} {x2} {y2 + h} {x2} {y2} c')

@app.route('/admin/dashboard/pdf', methods=['GET', 'POST'])
def apply_bedroom_filter(query, params, selected_bedrooms, table_alias=''):
    """Helper function to apply bedroom filter to a query.
    
    Args:
        query (str): The SQL query to modify
        params (list): The parameters list to append to
        selected_bedrooms (str): The selected number of bedrooms
        table_alias (str): Optional table alias for the bedrooms column
        
    Returns:
        tuple: (modified_query, modified_params)
    """
    if selected_bedrooms.isdigit():
        bedrooms = int(selected_bedrooms)
        query += f" AND {table_alias + '.' if table_alias else ''}bedrooms = %s"
        params.append(bedrooms)
    elif selected_bedrooms == '4+':
        query += f" AND {table_alias + '.' if table_alias else ''}bedrooms >= 4"
    return query, params

@app.route('/admin/dashboard/pdf', methods=['GET', 'POST'])
def dashboard_pdf():
    if 'admin_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    cur = mysql.connection.cursor()
    selected_type = request.form.get('house_type', None)
    selected_project = request.form.get('project', None)
    selected_feature = request.form.get('house_feature', None)
    selected_bedrooms = request.form.get('bedrooms', None)

    print(f"PDF Generation - Selected Type: {selected_type}")
    print(f"PDF Generation - Selected Project: {selected_project}")
    print(f"PDF Generation - Selected Bedrooms: {selected_bedrooms}")

    # Fetch all data needed for the dashboard report
    total_houses = 0
    total_projects = 0
    total_types = 0
    latest_houses = []
    houses_by_type_data = []
    houses_by_project_data = []
    houses_status_distribution_data = []
    houses_by_bedrooms_data = []
    houses_by_bathrooms_data = []
    houses_by_living_area_data = []
    house_additions_data = []

    try:
        # Apply filters to total counts
        total_houses_query = "SELECT COUNT(*) FROM house WHERE 1 = 1"
        total_houses_params = []
        if selected_type:
            total_houses_query += " AND t_id = %s"
            total_houses_params.append(selected_type)
        if selected_project:
            total_houses_query += " AND p_id = %s"
            total_houses_params.append(selected_project)
        if selected_feature:
            total_houses_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            total_houses_params.append(selected_feature)
        cur.execute(total_houses_query, total_houses_params)
        total_houses = cur.fetchone()[0]

        total_projects_query = "SELECT COUNT(*) FROM project p WHERE 1 = 1"
        total_projects_params = []
        if selected_type:
            total_projects_query += " AND EXISTS (SELECT 1 FROM house h WHERE h.p_id = p.p_id AND h.t_id = %s)"
            total_projects_params.append(selected_type)
        if selected_project:
            total_projects_query += " AND p.p_id = %s"
            total_projects_params.append(selected_project)
        if selected_feature:
            total_projects_query += " AND EXISTS (SELECT 1 FROM house h JOIN house_features hhf ON h.h_id = hhf.h_id WHERE h.p_id = p.p_id AND hhf.f_id = %s)"
            total_projects_params.append(selected_feature)
        cur.execute(total_projects_query, total_projects_params)
        total_projects = cur.fetchone()[0]

        total_types_query = "SELECT COUNT(*) FROM house_type ht WHERE 1 = 1"
        total_types_params = []
        if selected_type:
            total_types_query += " AND ht.t_id = %s"
            total_types_params.append(selected_type)
        if selected_project:
            total_types_query += " AND EXISTS (SELECT 1 FROM house h WHERE h.t_id = ht.t_id AND h.p_id = %s)"
            total_types_params.append(selected_project)
        if selected_feature:
            total_types_query += " AND EXISTS (SELECT 1 FROM house h JOIN house_features hhf ON h.h_id = hhf.h_id WHERE h.t_id = ht.t_id AND hhf.f_id = %s)"
            total_types_params.append(selected_feature)
        cur.execute(total_types_query, total_types_params)
        total_types = cur.fetchone()[0]

        # Get latest houses with filters
        latest_houses_query = "SELECT h_id, h_title as title, created_at FROM house WHERE 1=1"
        latest_houses_params = []
        if selected_type:
            latest_houses_query += " AND t_id = %s"
            latest_houses_params.append(selected_type)
        if selected_project:
            latest_houses_query += " AND p_id = %s"
            latest_houses_params.append(selected_project)
        if selected_feature:
            latest_houses_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            latest_houses_params.append(selected_feature)
            
        # Apply bedroom filter using helper function
        latest_houses_query, latest_houses_params = apply_bedroom_filter(
            latest_houses_query, latest_houses_params, selected_bedrooms, '')
            
        latest_houses_query += " ORDER BY created_at DESC LIMIT 5"
        cur.execute(latest_houses_query, latest_houses_params)
        latest_houses = dict_fetchall(cur)
        latest_houses = serialize_data_for_json(latest_houses)

        # Get houses by type
        houses_by_type_query = """
            SELECT ht.t_name as name, COUNT(h.h_id) as house_count
            FROM house_type ht
            LEFT JOIN house h ON ht.t_id = h.t_id
            WHERE 1 = 1
        """
        houses_by_type_params = []

        if selected_project:
            houses_by_type_query += " AND h.p_id = %s"
            houses_by_type_params.append(selected_project)

        if selected_type:
            houses_by_type_query += " AND ht.t_id = %s"
            houses_by_type_params.append(selected_type)
        if selected_feature:
            houses_by_type_query += " AND h.h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            houses_by_type_params.append(selected_feature)

        houses_by_type_query += " GROUP BY ht.t_name"
        cur.execute(houses_by_type_query, houses_by_type_params)
        houses_by_type_data = dict_fetchall(cur)
        houses_by_type_data = serialize_data_for_json(houses_by_type_data)

        # Get houses by project
        houses_by_project_query = """
            SELECT p.p_name as name, COUNT(h.h_id) as house_count
            FROM project p
            LEFT JOIN house h ON p.p_id = h.p_id
            WHERE 1 = 1
        """
        houses_by_project_params = []

        if selected_type:
            houses_by_project_query += " AND h.t_id = %s"
            houses_by_project_params.append(selected_type)
        
        if selected_project:
            houses_by_project_query += " AND p.p_id = %s"
            houses_by_project_params.append(selected_project)
        if selected_feature:
            houses_by_project_query += " AND h.h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            houses_by_project_params.append(selected_feature)

        houses_by_project_query += " GROUP BY p.p_name"
        cur.execute(houses_by_project_query, houses_by_project_params)
        houses_by_project_data = dict_fetchall(cur)
        houses_by_project_data = serialize_data_for_json(houses_by_project_data)

        # Get houses by status with filters
        status_query = "SELECT status, COUNT(h_id) as count FROM house WHERE 1=1"
        status_params = []
        if selected_type:
            status_query += " AND t_id = %s"
            status_params.append(selected_type)
        if selected_project:
            status_query += " AND p_id = %s"
            status_params.append(selected_project)
        if selected_feature:
            status_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            status_params.append(selected_feature)
            
        # Apply bedroom filter using helper function
        status_query, status_params = apply_bedroom_filter(
            status_query, status_params, selected_bedrooms, '')
        status_query += " GROUP BY status"
        cur.execute(status_query, status_params)
        houses_status_distribution_data = dict_fetchall(cur)
        houses_status_distribution_data = serialize_data_for_json(houses_status_distribution_data)

        # Get houses by bedrooms with filters
        bedrooms_query = "SELECT bedrooms as name, COUNT(h_id) as count FROM house WHERE bedrooms IS NOT NULL"
        bedrooms_params = []
        if selected_type:
            bedrooms_query += " AND t_id = %s"
            bedrooms_params.append(selected_type)
        if selected_project:
            bedrooms_query += " AND p_id = %s"
            bedrooms_params.append(selected_project)
        if selected_feature:
            bedrooms_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            bedrooms_params.append(selected_feature)
        if selected_bedrooms:
            if selected_bedrooms == '5':
                bedrooms_query += " AND bedrooms >= 5"
            else:
                bedrooms_query += " AND bedrooms = %s"
                bedrooms_params.append(int(selected_bedrooms))
        bedrooms_query += " GROUP BY bedrooms ORDER BY bedrooms"
        cur.execute(bedrooms_query, bedrooms_params)
        houses_by_bedrooms_data = dict_fetchall(cur)
        houses_by_bedrooms_data = serialize_data_for_json(houses_by_bedrooms_data)

        # Get houses by bathrooms with filters
        bathrooms_query = "SELECT bathrooms as name, COUNT(h_id) as count FROM house WHERE bathrooms IS NOT NULL"
        bathrooms_params = []
        if selected_type:
            bathrooms_query += " AND t_id = %s"
            bathrooms_params.append(selected_type)
        if selected_project:
            bathrooms_query += " AND p_id = %s"
            bathrooms_params.append(selected_project)
        if selected_feature:
            bathrooms_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            bathrooms_params.append(selected_feature)
        if selected_bedrooms:
            if selected_bedrooms == '5':
                bathrooms_query += " AND bedrooms >= 5"
            else:
                bathrooms_query += " AND bedrooms = %s"
                bathrooms_params.append(int(selected_bedrooms))
        bathrooms_query += " GROUP BY bathrooms ORDER BY bathrooms"
        cur.execute(bathrooms_query, bathrooms_params)
        houses_by_bathrooms_data = dict_fetchall(cur)
        houses_by_bathrooms_data = serialize_data_for_json(houses_by_bathrooms_data)

        # Get houses by living area with filters
        living_area_query = "SELECT living_area as name, COUNT(h_id) as count FROM house WHERE living_area IS NOT NULL"
        living_area_params = []
        if selected_type:
            living_area_query += " AND t_id = %s"
            living_area_params.append(selected_type)
        if selected_project:
            living_area_query += " AND p_id = %s"
            living_area_params.append(selected_project)
        if selected_feature:
            living_area_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            living_area_params.append(selected_feature)
        if selected_bedrooms:
            if selected_bedrooms == '5':
                living_area_query += " AND bedrooms >= 5"
            else:
                living_area_query += " AND bedrooms = %s"
                living_area_params.append(int(selected_bedrooms))
        living_area_query += " GROUP BY living_area ORDER BY living_area"
        cur.execute(living_area_query, living_area_params)
        houses_by_living_area_data = dict_fetchall(cur)
        houses_by_living_area_data = serialize_data_for_json(houses_by_living_area_data)

        # Get house additions over time (last 30 days) with filters
        additions_query = """
            SELECT DATE(created_at) as date, COUNT(h_id) as count 
            FROM house 
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """
        additions_params = []
        if selected_type:
            additions_query += " AND t_id = %s"
            additions_params.append(selected_type)
        if selected_project:
            additions_query += " AND p_id = %s"
            additions_params.append(selected_project)
        if selected_feature:
            additions_query += " AND h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            additions_params.append(selected_feature)
        if selected_bedrooms:
            if selected_bedrooms == '5':
                additions_query += " AND bedrooms >= 5"
            else:
                additions_query += " AND bedrooms = %s"
                additions_params.append(int(selected_bedrooms))
        additions_query += " GROUP BY DATE(created_at) ORDER BY DATE(created_at)"
        cur.execute(additions_query, additions_params)
        house_additions_data = dict_fetchall(cur)
        house_additions_data = serialize_data_for_json(house_additions_data)

        # --- CHART IMAGE GENERATION ---
        def make_bar_chart(data, xkey, ykey, title, color='#2563eb'):
            if not data:
                return None
                
            # Configure matplotlib to use a font that supports Thai characters
            try:
                # Try to use a system font that supports Thai
                import matplotlib.font_manager as fm
                
                # List of fonts to try (in order of preference)
                thai_fonts = [
                    'Tahoma',
                    'Noto Sans Thai',
                    'Arial Unicode MS',
                    'Microsoft Sans Serif',
                    'Leelawadee UI',
                    'Angsana New',
                    'Cordia New',
                    'Tahoma'
                ]
                
                # Find the first available font that supports Thai
                for font in thai_fonts:
                    try:
                        font_path = fm.findfont(fm.FontProperties(family=font))
                        plt.rcParams['font.family'] = font
                        break
                    except:
                        continue
                else:
                    # If no font found, fall back to default but with Unicode support
                    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'Tahoma']
                    plt.rcParams['axes.unicode_minus'] = False
            except Exception as e:
                print(f"Warning: Could not set Thai font: {str(e)}")
            
            try:
                fig, ax = plt.subplots(figsize=(4,2.2))
                x = [str(d[xkey]) for d in data]  # Ensure x values are strings
                y = [d[ykey] for d in data]
                bars = ax.bar(x, y, color=color)
                
                # Set title and labels with proper encoding
                ax.set_title(title, fontsize=11, color='#2563eb', pad=10)
                ax.set_ylabel('Count', fontsize=10)
                ax.set_xlabel('')
                
                # Rotate x-axis labels to prevent overlap
                ax.tick_params(axis='x', labelrotation=25, labelsize=9)
                ax.tick_params(axis='y', labelsize=9)
                
                # Add value labels on top of bars
                for bar in bars:
                    ax.annotate(f'{bar.get_height()}',
                                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                                xytext=(0, 3), textcoords="offset points",
                                ha='center', va='bottom', fontsize=8, color='#2563eb')
                
                fig.tight_layout()
                
                # Save the figure with high DPI and proper bbox settings
                tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                plt.savefig(tmpfile.name, bbox_inches='tight', dpi=160, 
                           facecolor=fig.get_facecolor(), edgecolor='none')
                plt.close(fig)
                
                # Add to cleanup list
                if 'chart_images' in locals():
                    chart_images.append(tmpfile.name)
                    
                return tmpfile.name
                
            except Exception as e:
                print(f"Error generating chart: {str(e)}")
                if 'fig' in locals():
                    plt.close(fig)
                return None

        img_by_type = make_bar_chart(houses_by_type_data, 'name', 'house_count', 'Houses by Type') if houses_by_type_data else None
        img_by_project = make_bar_chart(houses_by_project_data, 'name', 'house_count', 'Houses by Project', color='#059669') if houses_by_project_data else None
        img_by_bedrooms = make_bar_chart(houses_by_bedrooms_data, 'name', 'count', 'Houses by Bedrooms', color='#f59e42') if houses_by_bedrooms_data else None
        img_by_bathrooms = make_bar_chart(houses_by_bathrooms_data, 'name', 'count', 'Houses by Bathrooms', color='#f43f5e') if houses_by_bathrooms_data else None
        img_by_area = make_bar_chart(houses_by_living_area_data, 'name', 'count', 'Houses by Living Area', color='#a21caf') if houses_by_living_area_data else None
        # --- END CHART IMAGE GENERATION ---

    except Exception as e:
        flash(f'Error fetching dashboard data for PDF: {str(e)}', 'error')
        cur.close()
        return jsonify({'message': f'Error generating PDF: {str(e)}'}), 500
    finally:
        cur.close()

    pdf = PDF()
    font_path = os.path.join('static', 'fonts', 'NotoSansThai-Regular.ttf')
    font_path_bold = os.path.join('static', 'fonts', 'NotoSansThai-Bold.ttf')
    pdf.add_font('NotoSansThai', '', font_path, uni=True)
    pdf.add_font('NotoSansThai', 'B', font_path_bold, uni=True)
    pdf.set_font('NotoSansThai', '', 10)
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- Modern Stat Cards ---
    card_w = 60
    card_h = 24
    margin = 12
    y_start = pdf.get_y() + 2
    pdf.draw_stat_card(margin, y_start, card_w, card_h, 'Total Houses', total_houses, (224, 242, 254))
    pdf.draw_stat_card(margin + card_w + 8, y_start, card_w, card_h, 'Total Projects', total_projects, (219, 234, 254))
    pdf.draw_stat_card(margin + 2 * (card_w + 8), y_start, card_w, card_h, 'Total Types', total_types, (191, 219, 254))
    pdf.ln(card_h + 10)

    # --- Remove Latest Houses and Dashboard Charts sections ---
    # Only keep the following data tables:

    # --- Section: Houses by Type ---
    pdf.chapter_title('Houses by Type Distribution', color=(37, 99, 235))
    if houses_by_type_data:
        table_data = [(d['name'], d['house_count']) for d in houses_by_type_data]
        pdf.add_table(['House Type', 'Count'], table_data, [100, 50])
    else:
        pdf.chapter_body('No houses by type data available.')
    pdf.ln(2)

    # --- Section: Houses by Project ---
    pdf.chapter_title('Houses by Project Distribution', color=(37, 99, 235))
    if houses_by_project_data:
        table_data = [(d['name'], d['house_count']) for d in houses_by_project_data]
        pdf.add_table(['Project Name', 'Count'], table_data, [100, 50])
    else:
        pdf.chapter_body('No houses by project data available.')
    pdf.ln(2)

    # --- Section: Houses by Status ---
    pdf.chapter_title('Houses by Status Distribution', color=(37, 99, 235))
    if houses_status_distribution_data:
        table_data = [(d['status'], d['count']) for d in houses_status_distribution_data]
        pdf.add_table(['Status', 'Count'], table_data, [100, 50])
    else:
        pdf.chapter_body('No houses by status data available.')
    pdf.ln(2)

    # --- Section: Houses by Bedrooms ---
    pdf.chapter_title('Houses by Bedrooms', color=(37, 99, 235))
    if houses_by_bedrooms_data:
        table_data = [(d['name'], d['count']) for d in houses_by_bedrooms_data]
        pdf.add_table(['Bedrooms', 'Count'], table_data, [100, 50])
    else:
        pdf.chapter_body('No houses by bedrooms data available.')
    pdf.ln(2)

    # --- Section: Houses by Bathrooms ---
    pdf.chapter_title('Houses by Bathrooms', color=(37, 99, 235))
    if houses_by_bathrooms_data:
        table_data = [(d['name'], d['count']) for d in houses_by_bathrooms_data]
        pdf.add_table(['Bathrooms', 'Count'], table_data, [100, 50])
    else:
        pdf.chapter_body('No houses by bathrooms data available.')
    pdf.ln(2)

    # --- Section: Houses by Living Area ---
    pdf.chapter_title('Houses by Living Area', color=(37, 99, 235))
    if houses_by_living_area_data:
        table_data = [(d['name'], d['count']) for d in houses_by_living_area_data]
        pdf.add_table(['Living Area', 'Count'], table_data, [100, 50])
    else:
        pdf.chapter_body('No houses by living area data available.')
    pdf.ln(2)

    # --- Section: House Additions (Last 30 Days) ---
    pdf.chapter_title('House Additions (Last 30 Days)', color=(37, 99, 235))
    if house_additions_data:
        table_data = [(d['date'], d['count']) for d in house_additions_data]
        pdf.add_table(['Date', 'Count'], table_data, [100, 50])
    else:
        pdf.chapter_body('No house additions data available for the last 30 days.')
    pdf.ln(2)

    # Initialize chart images list at the start of the function
    chart_images = []
    img_by_type = img_by_project = img_by_bedrooms = img_by_bathrooms = img_by_area = None

    try:
        # Generate PDF output
        pdf_output = pdf.output(dest='S')
        if isinstance(pdf_output, str):
            pdf_bytes = pdf_output.encode('latin-1')
        else:
            pdf_bytes = bytes(pdf_output)
        
        # Create response
        response = make_response(pdf_bytes)
        response.headers.set('Content-Type', 'application/pdf')
        response.headers.set('Content-Disposition', 'attachment', filename='dashboard_report.pdf')
        
        return response

    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return jsonify({'message': f'Error generating PDF: {str(e)}'}), 500
        
    finally:
        # Clean up chart images
        for img in chart_images:
            try:
                if img and os.path.exists(img):
                    os.remove(img)
            except Exception as e:
                print(f"Warning: Could not remove temporary file {img}: {str(e)}")

@app.route('/logout')
@login_required
def logout():
    # Store a copy of the username for the flash message
    username = current_user.username if current_user.is_authenticated else 'User'
    
    # Log the user out
    logout_user()
    
    # Clear the session completely
    session.clear()
    
    # Clear any remaining session data
    session.modified = True
    
    flash(f'{username} ได้ออกจากระบบเรียบร้อยแล้ว', 'success')
    return redirect(url_for('login'))

@app.route('/admin/houses')
@login_required
@admin_required
def admin_houses():
    
    cur = mysql.connection.cursor()
    try:
        # Get filter values
        search = request.args.get('search', '')
        type_filter = request.args.get('type', '')
        project_filter = request.args.get('project', '')
        sort_order = request.args.get('sort', 'name_asc')

        # Base query
        query = """
            SELECT h.h_id as id, h.h_title as name, 
                   CASE 
                       WHEN h.h_description IS NULL THEN 'No description'
                       WHEN LENGTH(h.h_description) > 50 THEN CONCAT(LEFT(h.h_description, 50), '...')
                       ELSE h.h_description
                   END as description,
                   h.price, h.bedrooms, h.bathrooms, 
                   h.living_area as area, h.parking_space as parking,
                   h.f_id, COALESCE(h.view_count, 0) as view_count,
                   t.t_name as type_name, p.p_name as project_name,
                   h.status,
                   (SELECT image_url FROM house_images WHERE h_id = h.h_id AND is_main = 1 LIMIT 1) as main_image_url
            FROM house h
            LEFT JOIN house_type t ON h.t_id = t.t_id
            LEFT JOIN project p ON h.p_id = p.p_id
        """
        params = []

        # Add WHERE clause if filters are applied
        where_clauses = []
        if search:
            where_clauses.append("(h.h_title LIKE %s OR h.h_description LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        if type_filter:
            where_clauses.append("h.t_id = %s")
            params.append(type_filter)
            
        if project_filter:
            where_clauses.append("h.p_id = %s")
            params.append(project_filter)
            
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        # Add ORDER BY based on sort_order
        if sort_order == 'name_asc':
            query += " ORDER BY h.h_title ASC"
        elif sort_order == 'name_desc':
            query += " ORDER BY h.h_title DESC"
        elif sort_order == 'type_asc':
            query += " ORDER BY t.t_name ASC, h.h_title ASC"
        elif sort_order == 'type_desc':
            query += " ORDER BY t.t_name DESC, h.h_title ASC"
        elif sort_order == 'project_asc':
            query += " ORDER BY p.p_name ASC, h.h_title ASC"
        elif sort_order == 'project_desc':
            query += " ORDER BY p.p_name DESC, h.h_title ASC"
        elif sort_order == 'views_asc':
            query += " ORDER BY view_count ASC, h.h_title ASC"
        elif sort_order == 'views_desc':
            query += " ORDER BY view_count DESC, h.h_title ASC"
        else:  # Default sort by view count descending
            query += " ORDER BY view_count DESC, h.h_title ASC"

        cur.execute(query, params)
        houses = dict_fetchall(cur)

        # Get features for each house
        for house in houses:
            cur.execute("""
                SELECT f_name FROM house_features WHERE f_id = %s
            """, (house['f_id'],))
            feature = dict_fetchone(cur)
            house['feature'] = feature['f_name'] if feature else None

        # Get house types for filter dropdown
        cur.execute("SELECT t_id, t_name FROM house_type ORDER BY t_name")
        house_types = dict_fetchall(cur)

        # Get projects for filter dropdown
        cur.execute("SELECT p_id, p_name FROM project ORDER BY p_name")
        projects = dict_fetchall(cur)

        # After fetching houses = dict_fetchall(cur) in each relevant route:
        for house in houses:
            # Attach main_image_url
            cur.execute("SELECT image_url FROM house_images WHERE house_id = %s AND is_main = 1 LIMIT 1", (house['id'],))
            row = cur.fetchone()
            if row:
                url = row[0].lstrip('/')
                if not url.startswith('static/uploads/'):
                    url = 'static/uploads/' + url.split('/')[-1]
                house['main_image_url'] = '/' + url
            else:
                cur.execute("SELECT image_url FROM house_images WHERE house_id = %s LIMIT 1", (house['id'],))
                row = cur.fetchone()
                if row:
                    url = row[0].lstrip('/')
                    if not url.startswith('static/uploads/'):
                        url = 'static/uploads/' + url.split('/')[-1]
                    house['main_image_url'] = '/' + url
                else:
                    house['main_image_url'] = None

            # Attach gallery_images (optional, for mini-gallery)
            cur.execute("SELECT image_url FROM house_images WHERE house_id = %s", (house['id'],))
            gallery_rows = cur.fetchall()
            house['gallery_images'] = []
            for row in gallery_rows:
                url = row[0].lstrip('/')
                if not url.startswith('static/uploads/'):
                    url = 'static/uploads/' + url.split('/')[-1]
                house['gallery_images'].append('/' + url)

        return render_template('admin_houses.html', 
                            houses=houses,
                            house_types=house_types,
                            projects=projects,
                            sort_order=sort_order)
    finally:
        cur.close()

@app.route('/admin/add-house', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_house():
    # Check if admin is logged in
    
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        try:
            # === 1. Correct Data Retrieval from Form ===
            h_title = request.form.get('h_title')
            # The HTML form uses name="description"
            h_description = request.form.get('description')
            price = request.form.get('price')
            t_id = request.form.get('t_id')
            p_id = request.form.get('p_id')
            bedrooms = request.form.get('bedrooms')
            bathrooms = request.form.get('bathrooms')
            living_area = request.form.get('living_area')
            parking_space = request.form.get('parking_space')
            no_of_floors = request.form.get('no_of_floors')
            status = request.form.get('status')
            
            # Retrieve the single feature ID (correctly)
            f_id = request.form.get('f_id')
            
            # Retrieve a list of all uploaded files (correctly)
            house_images = request.files.getlist('house_images')

            # Basic validation for required fields
            if not all([h_title, h_description, price, t_id, p_id, f_id]):
                flash('All required fields must be filled out.', 'error')
                return redirect(url_for('admin_add_house'))
            
            # === 2. Insert into 'house' table (including f_id) ===
            sql = """
                INSERT INTO house (h_title, h_description, price, t_id, p_id, 
                                 bedrooms, bathrooms, living_area, parking_space, no_of_floors, f_id, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            values = (h_title, h_description, price, t_id, p_id, 
                      bedrooms, bathrooms, living_area, parking_space, no_of_floors, f_id, status)
            
            cur.execute(sql, values)
            house_id = cur.lastrowid
            
            # === 3. Handle multiple image uploads and insert into 'house_images' table ===
            if house_images and house_images[0].filename != '':
                for idx, file in enumerate(house_images):
                    if file and file.filename != '':
                        filename = secure_filename(file.filename)
                        
                        # Create a unique filename to prevent overwrites
                        filename_base, filename_ext = os.path.splitext(filename)
                        unique_filename = f"{filename_base}_{int(time.time())}{filename_ext}"
                        
                        # Save the file to the UPLOAD_FOLDER
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file.save(filepath)
                        
                        # The URL should be relative to the static folder
                        image_url = os.path.join('uploads', unique_filename).replace('\\', '/')
                        
                        # Set is_main for the first image
                        is_main = 1 if idx == 0 else 0
                        
                        image_sql = """
                            INSERT INTO house_images (house_id, image_url, is_main, created_at)
                            VALUES (%s, %s, %s, NOW())
                        """
                        cur.execute(image_sql, (house_id, image_url, is_main))
                        
            # Commit all changes to the database
            mysql.connection.commit()
            flash('House added successfully!', 'success')
            return redirect(url_for('admin_houses'))
            
        except Exception as e:
            # Rollback in case of any error
            print(f"Error adding house: {str(e)}")
            import traceback
            traceback.print_exc()
            mysql.connection.rollback()
            flash(f'Error adding house: {str(e)}', 'error')
            return redirect(url_for('admin_add_house'))
        finally:
            cur.close()

    # GET request logic - loads the page with data for dropdowns
    try:
        cur.execute("SELECT t_id, t_name FROM house_type ORDER BY t_name")
        house_types = dict_fetchall(cur)
        
        cur.execute("SELECT p_id, p_name FROM project ORDER BY p_name")
        projects = dict_fetchall(cur)
        
        cur.execute("SELECT f_id, f_name FROM house_features ORDER BY f_name")
        house_features = dict_fetchall(cur)
        
        cur.close()
        return render_template('admin_add_house.html', 
                               house_types=house_types, 
                               projects=projects,
                               house_features=house_features)
    except Exception as e:
        flash(f'Error loading page: {str(e)}', 'error')
        return redirect(url_for('admin_houses'))
    finally:
        cur.close()

@app.route('/admin/edit-house/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_house(id):

    cur = mysql.connection.cursor()

    if request.method == 'POST':
        try:
            # Retrieve all form data
            h_title = request.form.get('h_title')
            h_description = request.form.get('h_description')
            price = request.form.get('price')
            t_id = request.form.get('t_id')
            p_id = request.form.get('p_id')
            bedrooms = request.form.get('bedrooms')
            bathrooms = request.form.get('bathrooms')
            living_area = request.form.get('living_area')
            parking_space = request.form.get('parking_space')
            no_of_floors = request.form.get('no_of_floors')
            status = request.form.get('status')
            f_id = request.form.get('f_id')
            
            # Use .get() with a default of None for optional fields like lat/long
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            
            # Update the main house record
            update_sql = """
                UPDATE house SET h_title=%s, h_description=%s, price=%s, t_id=%s, 
                p_id=%s, bedrooms=%s, bathrooms=%s, living_area=%s, parking_space=%s, 
                no_of_floors=%s, f_id=%s, status=%s, latitude=%s, longitude=%s
                WHERE h_id=%s
            """
            cur.execute(update_sql, (h_title, h_description, price, t_id, p_id, 
                                     bedrooms, bathrooms, living_area, parking_space, 
                                     no_of_floors, f_id, status, latitude, longitude, id))
            
            # Handle new image uploads
            new_images = request.files.getlist('house_images')
            if new_images and new_images[0].filename != '':
                for idx, file in enumerate(new_images):
                    if file:
                        filename = secure_filename(file.filename)
                        unique_filename = f"{int(time.time())}_{filename}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file.save(filepath)
                        image_url = os.path.join('uploads', unique_filename).replace('\\', '/')
                        
                        # Insert a new image record
                        image_sql = """
                            INSERT INTO house_images (house_id, image_url, is_main, created_at)
                            VALUES (%s, %s, %s, NOW())
                        """
                        # New images are not main by default, set is_main=0
                        cur.execute(image_sql, (id, image_url, 0))

            mysql.connection.commit()
            flash('House updated successfully!', 'success')
            return redirect(url_for('admin_edit_house', id=id))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error updating house: {str(e)}', 'error')
            return redirect(url_for('admin_edit_house', id=id))
        finally:
            cur.close()

    # GET request - Display the form
    try:
        # Fetch the specific house data
        cur.execute("SELECT * FROM house WHERE h_id = %s", [id])
        house = dict_fetchone(cur)

        if not house:
            flash('House not found.', 'error')
            return redirect(url_for('admin_houses'))

        # Fetch the related images for the house
        cur.execute("SELECT * FROM house_images WHERE house_id = %s ORDER BY is_main DESC, id ASC", [id])
        house_images = dict_fetchall(cur)

        # Fetch data for the dropdowns
        cur.execute("SELECT t_id, t_name FROM house_type ORDER BY t_name")
        house_types = dict_fetchall(cur)

        cur.execute("SELECT p_id, p_name FROM project ORDER BY p_name")
        projects = dict_fetchall(cur)

        cur.execute("SELECT f_id, f_name FROM house_features ORDER BY f_name")
        house_features = dict_fetchall(cur)
        
        cur.close()
        
        return render_template('admin_edit_house.html',
                               house=house,
                               house_images=house_images,
                               house_types=house_types,
                               projects=projects,
                               house_features=house_features)

    except Exception as e:
        flash(f'Error loading page: {str(e)}', 'error')
        return redirect(url_for('admin_houses'))
    finally:
        cur.close()

# --- AJAX routes for image management ---
# Route to delete an image
@app.route('/admin/houses/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_house(id):
        
    cur = mysql.connection.cursor()
    try:
        # First, delete associated images
        cur.execute("""
            SELECT image_url FROM house_images 
            WHERE house_id = %s
        """, (id,))
        images = cur.fetchall()
        
        # Delete the images from the filesystem
        for img in images:
            try:
                if img and img[0]:  # Access tuple by index instead of key
                    # Make sure the path is correct by joining with the UPLOAD_FOLDER
                    img_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(img[0]))
                    if os.path.exists(img_path):
                        os.remove(img_path)
                    else:
                        # Try with static folder as fallback (for older uploads)
                        img_path = os.path.join(app.root_path, 'static', img[0].lstrip('/'))
                        if os.path.exists(img_path):
                            os.remove(img_path)
            except Exception as e:
                print(f"Error deleting image file {img[0] if img else 'Unknown'}: {str(e)}")
        
        # Delete from house_images table
        cur.execute("DELETE FROM house_images WHERE house_id = %s", (id,))
        
        # Delete from house table
        cur.execute("DELETE FROM house WHERE h_id = %s", (id,))
        
        mysql.connection.commit()
        flash('House deleted successfully!', 'success')
        return redirect(url_for('admin_houses'))
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error deleting house: {str(e)}")
        flash(f'Error deleting house: {str(e)}', 'error')
        return redirect(url_for('admin_houses'))
    finally:
        cur.close()
    
    return redirect(url_for('admin_houses'))

@app.route('/admin/delete-house-image/<int:house_id>/<int:image_id>', methods=['POST'])
@login_required
@admin_required
def delete_house_image(house_id, image_id):
    
    cur = mysql.connection.cursor()
    try:
        # First, check if the image exists and get its details
        cur.execute("SELECT image_url, is_main FROM house_images WHERE id = %s AND house_id = %s", (image_id, house_id))
        image_data = cur.fetchone()
        
        if not image_data:
            return jsonify({'success': False, 'message': 'Image not found.'})
            
        image_url, is_main = image_data
            
        # Delete the image file from the server
        if image_url:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(image_url))
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError as e:
                    print(f"Error deleting image file: {e}")
        
        # Delete the image record from the database
        cur.execute("DELETE FROM house_images WHERE id = %s", [image_id])
        
        # Check if there are other images for this house
        cur.execute("SELECT COUNT(*) as count FROM house_images WHERE house_id = %s", [house_id])
        count_result = cur.fetchone()
        count = count_result['count'] if count_result and 'count' in count_result else 0
        
        # If the deleted image was the main image and other images exist, set a new main image
        if is_main == 1 and count > 0:
            cur.execute("UPDATE house_images SET is_main = 1 WHERE house_id = %s ORDER BY id ASC LIMIT 1", [house_id])

        mysql.connection.commit()
        return jsonify({'success': True})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cur.close()

# Route to set a new main image
@app.route('/admin/set-main-image/<int:house_id>/<int:image_id>', methods=['POST'])
@login_required
@admin_required
def set_main_image(house_id, image_id):

    cur = mysql.connection.cursor()
    try:
        # Set all images for this house to not main
        cur.execute("UPDATE house_images SET is_main = 0 WHERE house_id = %s", [house_id])
        
        # Set the selected image as main
        cur.execute("UPDATE house_images SET is_main = 1 WHERE id = %s AND house_id = %s", (image_id, house_id))
        
        mysql.connection.commit()
        return jsonify({'success': True})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cur.close()

@app.route('/admin/house-type/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_house_type(id):
        
    cur = mysql.connection.cursor()
    try:
        # First check if there are any houses using this house type
        cur.execute("SELECT COUNT(*) as count FROM house WHERE t_id = %s", (id,))
        count = cur.fetchone()['count']
        
        if count > 0:
            flash('Cannot delete this house type as there are houses associated with it', 'error')
            return redirect(url_for('admin_house_types'))
            
        # If no houses are using this type, proceed with deletion
        cur.execute("DELETE FROM house_type WHERE t_id = %s", (id,))
        mysql.connection.commit()
        flash('House type deleted successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error deleting house type: {str(e)}', 'error')
    finally:
        cur.close()
    return redirect(url_for('admin_house_types'))



@app.route('/admin/projects')
@login_required
@admin_required
def admin_projects():
        
    search = request.args.get('search', '').strip()
    
    print("\n=== DEBUG: admin_projects route called ===")
    
    cur = None
    projects = []
    try:
        # Debug: Check MySQL connection
        print("\n=== DATABASE CONNECTION INFO ===")
        print(f"MySQL Host: {app.config['MYSQL_HOST']}")
        print(f"MySQL Port: {app.config['MYSQL_PORT']}")
        print(f"MySQL Database: {app.config['MYSQL_DB']}")
        
        # Get connection and cursor
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get database and table info
        print("\n=== DATABASE INFO ===")
        cur.execute("SELECT DATABASE() as db")
        current_db = cur.fetchone()['db']
        print(f"Current database: {current_db}")
        
        # Check if project table exists
        cur.execute("SHOW TABLES LIKE 'project'")
        table_exists = cur.fetchone() is not None
        print(f"Project table exists: {table_exists}")
        
        if not table_exists:
            print("ERROR: Project table does not exist in the database!")
            flash('Project table not found in the database', 'error')
            return render_template('admin_projects.html', projects=[])
        
        # Get table structure
        cur.execute("DESCRIBE project")
        columns = [col['Field'] for col in cur.fetchall()]
        print("\n=== PROJECT TABLE STRUCTURE ===")
        print("Columns:", columns)
        
        # Build and execute query
        base_query = """
            SELECT 
                p_id, 
                p_name, 
                description,
                address,
                COALESCE(p_image, 'default_project.jpg') as p_image,
                created_at,
                COALESCE(updated_at, created_at) as updated_at
            FROM project
        """
        
        if search:
            query = f"{base_query} WHERE p_name LIKE %s OR description LIKE %s OR address LIKE %s ORDER BY created_at DESC"
            search_param = f"%{search}%"
            print(f"\n=== EXECUTING SEARCH QUERY ===")
            print(f"Query: {query}")
            print(f"Params: {[search_param, search_param, search_param]}")
            cur.execute(query, (search_param, search_param, search_param))
        else:
            query = f"{base_query} ORDER BY created_at DESC"
            print(f"\n=== EXECUTING QUERY ===")
            print(f"Query: {query}")
            cur.execute(query)
        
        # Fetch and process results
        projects = []
        rows = cur.fetchall()
        
        # Convert rows to list of dictionaries
        for row in rows:
            projects.append({
                'p_id': row.get('p_id'),
                'p_name': row.get('p_name', ''),
                'description': row.get('description', ''),
                'address': row.get('address', ''),
                'p_image': row.get('p_image', 'default_project.jpg'),
                'created_at': row.get('created_at'),
                'updated_at': row.get('updated_at', row.get('created_at'))
            })
        
        print("\n=== QUERY RESULTS ===")
        print(f"Number of projects found: {len(projects)}")
        if projects:
            print("First project sample:", projects[0])
        
        return render_template('admin_projects.html', projects=projects, search=search)
        
    except Exception as e:
        print("\n=== ERROR OCCURRED ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        flash('An error occurred while loading projects. The error has been logged.', 'error')
        return render_template('admin_projects.html', projects=[])
        
    finally:
        if cur:
            cur.close()
            print("\n=== DATABASE CONNECTION CLOSED ===")

# --- Corrected admin_add_project route ---
@app.route('/admin/projects/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_project():
        
    if request.method == 'POST':
        p_name = request.form.get('p_name')
        description = request.form.get('description', '')
        address = request.form.get('address', '')
        p_image = None
        
        # NOTE: Make sure you have 'from werkzeug.utils import secure_filename'
        # and 'app.config['UPLOAD_FOLDER']' set up.
        try:
            # File handling logic
            if 'p_image' in request.files and request.files['p_image'].filename != '':
                from werkzeug.utils import secure_filename
                import os
                file = request.files['p_image']
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                p_image = filename
                
            if not p_name:
                flash('Project name is required.', 'error')
                return render_template('admin_add_project.html', p_name=p_name, description=description, address=address)
            
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute(
                """
                INSERT INTO project (p_name, description, address, p_image, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (p_name, description, address, p_image)
            )
            mysql.connection.commit()
            flash('Project added successfully!', 'success')
            return redirect(url_for('admin_projects'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error adding project: {str(e)}', 'error')
            return render_template('admin_add_project.html', p_name=p_name, description=description, address=address)
        finally:
            if 'cur' in locals():
                cur.close()
            
    return render_template('admin_add_project.html')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# --- Corrected admin_edit_project route ---
@app.route('/admin/projects/edit/<project_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_project(project_id):
    print(f"\n=== DEBUG: admin_edit_project called with project_id: {project_id} (type: {type(project_id)}) ===")
    
    if 'admin_id' not in session:
        flash('Please login to access this page', 'error')
        return redirect(url_for('login'))
    
    # Convert project_id to string to match database type
    project_id_str = str(project_id)
    print(f"DEBUG: Converted project_id to string: {project_id_str}")
    
    # Get project data
    print("DEBUG: Fetching project data...")
    project_data = get_project_data(project_id_str)
    
    if not project_data:
        flash('Project not found.', 'error')
        print(f"DEBUG: Project with ID {project_id_str} not found")
        return redirect(url_for('admin_projects'))
    
    print(f"DEBUG: Project data to be passed to template: {project_data}")
    
    if request.method == 'POST':
        p_name = request.form.get('p_name')
        description = request.form.get('description', '')
        address = request.form.get('address', '')
        
        # Keep existing image by default
        p_image = project_data.get('p_image')
        
        # Debug log form data
        print(f"DEBUG: Form data - Name: {p_name}, Description: {description}, Address: {address}")
        print(f"DEBUG: Current image: {p_image}")
        
        try:
            # File handling for new image upload
            if 'p_image' in request.files and request.files['p_image'].filename != '':
                from werkzeug.utils import secure_filename
                import os
                file = request.files['p_image']
                if file and allowed_file(file.filename):
                    # Ensure upload directory exists
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Generate a unique filename
                    filename = secure_filename(file.filename)
                    base, ext = os.path.splitext(filename)
                    unique_filename = f"{base}_{int(time.time())}{ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    
                    # Save the file
                    file.save(filepath)
                    print(f"DEBUG: Saved new image to {filepath}")
                    
                    # Delete old image if it's not the default
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], p_image)
                    if p_image and p_image != 'default_project.jpg' and os.path.exists(old_image_path):
                        try:
                            os.remove(old_image_path)
                            print(f"DEBUG: Removed old image: {old_image_path}")
                        except Exception as e:
                            print(f"WARNING: Could not remove old image: {e}")
                    
                    p_image = unique_filename
            
            # Validation
            if not p_name:
                flash('Project name is required.', 'error')
                return render_template('admin_edit_project.html', project=project_data)
                
            # Ensure required fields have values
            p_name = p_name.strip()
            description = description.strip()
            address = address.strip()
            
            print(f"DEBUG: Validated data - Name: {p_name}, Description: {description}, Address: {address}")
            
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Build the update query dynamically to only update provided fields
            update_fields = []
            params = []
            
            update_fields.append("p_name = %s")
            params.append(p_name)
            
            update_fields.append("description = %s")
            params.append(description)
            
            update_fields.append("address = %s")
            params.append(address)
            
            update_fields.append("p_image = %s")
            params.append(p_image)
            
            # Always update the updated_at timestamp
            update_fields.append("updated_at = NOW()")
            
            # Add the WHERE condition
            params.append(project_id_str)
            
            # Build the final query
            update_query = f"""
                UPDATE project 
                SET 
                    {', '.join(update_fields)}
                WHERE p_id = %s
            """
            
            print(f"DEBUG: Executing update query: {update_query}")
            print(f"DEBUG: With params: {params}")
            
            cur.execute(update_query, params)
            
            if cur.rowcount == 0:
                flash('Project not found.', 'error')
            else:
                mysql.connection.commit()
                flash('Project updated successfully!', 'success')
            return redirect(url_for('admin_projects'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error updating project: {str(e)}', 'error')
            return render_template('admin_edit_project.html', project=project_data)
        finally:
            if 'cur' in locals():
                cur.close()
                
    # For GET requests, render the edit form with project data
    print("DEBUG: Rendering edit template with project data")
    return render_template('admin_edit_project.html', project=project_data)

# --- Corrected admin_delete_project route ---
@app.route('/admin/projects/delete/<project_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_project(project_id):
        
    # Convert project_id to string to match database type
    project_id_str = str(project_id)
    
    # Check if user is admin
    if session.get('role') != 'admin':
        flash('You do not have permission to delete projects.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Check if the request has a CSRF token
    if not request.form.get('csrf_token') or request.form.get('csrf_token') != session.get('csrf_token'):
        flash('Invalid CSRF token. Please try again.', 'error')
        return redirect(url_for('admin_projects'))
    
    cur = None
    try:
        # First, get the project data to check if it exists and get the image filename
        project_data = get_project_data(project_id_str)
        if not project_data:
            flash('Project not found.', 'error')
            return redirect(url_for('admin_projects'))
        
        # Delete the project from the database
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM project WHERE p_id = %s", (project_id_str,))
        
        if cur.rowcount > 0:
            mysql.connection.commit()
            flash('Project deleted successfully!', 'success')
            
            # Delete the project image if it exists and is not the default image
            if project_data.get('p_image') and project_data['p_image'] != 'default_project.jpg':
                try:
                    import os
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], project_data['p_image'])
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    print(f"Error deleting project image: {str(e)}")
                    # Don't fail the whole operation if image deletion fails
        else:
            flash('Project not found or could not be deleted.', 'error')
            
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error deleting project: {str(e)}', 'error')
    finally:
        if cur:
            cur.close()
    
    return redirect(url_for('admin_projects'))

@app.route('/admin/house-types', methods=['GET'])
@login_required
@admin_required
def admin_house_types():
    
    search = request.args.get('search', '').strip()
    cur = mysql.connection.cursor()
    try:
        query = "SELECT t_id as id, t_name as name, description, created_at FROM house_type"
        params = []
        if search:
            query += " WHERE t_name LIKE %s"
            params.append(f"%{search}%")
        query += " ORDER BY created_at DESC"
        cur.execute(query, params)
        type_list = dict_fetchall(cur)
    except Exception as e:
        flash(f'Error loading house types: {str(e)}', 'error')
        type_list = []
    finally:
        cur.close()
    return render_template('admin_house_types.html', house_types=type_list)

@app.route('/admin/house-types/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_house_type():

    if request.method == 'POST':
        t_name = request.form.get('t_name')
        description = request.form.get('description')
        t_image = request.files.get('t_image')

        if not t_name:
            flash('House type name is required.', 'error')
            return render_template('admin_add_house_type.html')

        image_filename = None
        if t_image and t_image.filename != '':
            image_filename = secure_filename(t_image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            t_image.save(image_path)

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cur.execute("INSERT INTO house_type (t_name, description, t_image) VALUES (%s, %s, %s)", 
                       (t_name, description, image_filename))
            mysql.connection.commit()
            flash('House type added successfully!', 'success')
            return redirect(url_for('admin_house_types'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error adding house type: {str(e)}', 'error')
            return render_template('admin_add_house_type.html')
        finally:
            cur.close()

    return render_template('admin_add_house_type.html')

@app.route('/admin/house-types/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_house_type(id):
    
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        try:
            t_name = request.form.get('t_name')
            description = request.form.get('description')
            t_image = request.files.get('t_image')

            if not t_name:
                flash('House type name is required.', 'error')
                return redirect(url_for('admin_edit_house_type', id=id))

            # Check if a new image was uploaded
            if t_image and t_image.filename != '':
                image_filename = secure_filename(t_image.filename)
                # Create the uploads folder if it doesn't exist
                upload_folder = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                image_path = os.path.join(upload_folder, image_filename)
                t_image.save(image_path)
                
                # Update with new image
                cur.execute(
                    """
                    UPDATE house_type 
                    SET t_name = %s, description = %s, t_image = %s, updated_at = NOW()
                    WHERE t_id = %s
                    """,
                    (t_name, description, image_filename, id)
                )
            else:
                # Update without changing the image
                cur.execute(
                    """
                    UPDATE house_type 
                    SET t_name = %s, description = %s, updated_at = NOW()
                    WHERE t_id = %s
                    """,
                    (t_name, description, id)
                )
            
            if cur.rowcount == 0:
                flash('House type not found.', 'error')
            else:
                mysql.connection.commit()
                flash('House type updated successfully!', 'success')
            
            return redirect(url_for('admin_house_types'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error updating house type: {str(e)}', 'error')
            return redirect(url_for('admin_edit_house_type', id=id))
        finally:
            cur.close()
    
    # GET method - show edit form
    try:
        cur.execute(
            """
            SELECT t_id, t_name, description, 
                   COALESCE(t_image, '') as t_image,
                   created_at
            FROM house_type 
            WHERE t_id = %s
            """,
            (id,)
        )
        # Fix: Convert the tuple result to a dictionary
        row = cur.fetchone()
        if row:
            # Get column names from cursor description
            columns = [desc[0] for desc in cur.description]
            # Create a dictionary from column names and row values
            house_type = dict(zip(columns, row))
        else:
            house_type = None
        
        if not house_type:
            flash('House type not found.', 'error')
            return redirect(url_for('admin_house_types'))
        
        # Pass the dictionary to the template
        return render_template('admin_edit_house_type.html', house_type=house_type)
    except Exception as e:
        mysql.connection.rollback()
        error_msg = str(e).lower()
        if 'foreign key constraint' in error_msg:
            flash('Cannot update house type: It is being referenced by other records', 'error')
        else:
            flash(f'Error loading house type: {str(e)}', 'error')
        return redirect(url_for('admin_house_types'))
    finally:
        cur.close() if 'cur' in locals() else None

@app.route('/admin/house-features', methods=['GET']) 
@login_required
@admin_required
def admin_house_features():
    
    search = request.args.get('search', '').strip()
    cur = mysql.connection.cursor()
    try:
        query = "SELECT f_id as id, f_name as name, f_description as description, COALESCE(f_image, 'house_feature_placeholder.jpg') as image, created_at FROM house_features"
        params = []
        if search:
            query += " WHERE f_name LIKE %s"
            params.append(f"%{search}%")
        query += " ORDER BY f_id DESC"
        cur.execute(query, params)
        features = dict_fetchall(cur)
    except Exception as e:
        flash(f'Error loading house features: {str(e)}', 'error')
        features = []
    finally:
        cur.close()
    return render_template('admin_house_features.html', features=features)

@app.route('/admin/add-house-feature', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_house_feature():
    
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        f_name = request.form.get('f_name')
        f_description = request.form.get('f_description')
        f_image = request.files.get('f_image')
        admin_id = session.get('admin_id') # Get admin ID

        if not f_name:
            flash('Feature name is required.', 'error')
            cur.close()
            return render_template('admin_add_house_feature.html')
        
        image_filename = None
        if f_image and f_image.filename != '':
            image_filename = secure_filename(f_image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            f_image.save(image_path)

        try:
            cur.execute("INSERT INTO house_features (f_name, f_description, f_image, a_id) VALUES (%s, %s, %s, %s)", 
                        (f_name, f_description, image_filename, admin_id))
            mysql.connection.commit()
            flash('House feature added successfully!', 'success')
            return redirect(url_for('admin_house_features'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error adding house feature: {str(e)}', 'error')
            cur.close()
            return render_template('admin_add_house_feature.html')
    
    cur.close()
    return render_template('admin_add_house_feature.html')

@app.route('/admin/edit-house-feature/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_house_feature(id):
    
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        f_name = request.form.get('f_name')
        f_description = request.form.get('f_description')
        f_image = request.files.get('f_image')
        admin_id = session.get('admin_id') # Get admin ID
            
        if not f_name:
            flash('Feature name is required.', 'error')
            cur.execute("SELECT f_id as id, f_name as name, f_description as description, COALESCE(f_image, 'house_feature_placeholder.jpg') as image_filename, created_at FROM house_features WHERE f_id = %s", (id,))
            feature_data = dict_fetchone(cur)
            cur.close()
            return render_template('admin_edit_house_feature.html', feature=feature_data)
                
        image_filename = None
        # Check if a new image was uploaded
        if f_image and f_image.filename != '':
            image_filename = secure_filename(f_image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            f_image.save(image_path)
        else:
            # Retain existing image if no new image is uploaded
            cur.execute("SELECT f_image FROM house_features WHERE f_id = %s", (id,))
            existing_image = cur.fetchone()
            if existing_image:
                image_filename = existing_image[0]

        try:
            if image_filename:
                cur.execute("UPDATE house_features SET f_name = %s, f_description = %s, f_image = %s, a_id = %s WHERE f_id = %s", 
                            (f_name, f_description, image_filename, admin_id, id))
            else:
                cur.execute("UPDATE house_features SET f_name = %s, f_description = %s, a_id = %s WHERE f_id = %s", 
                            (f_name, f_description, admin_id, id))
            mysql.connection.commit()
            flash('House feature updated successfully!', 'success')
            return redirect(url_for('admin_house_features'))
        except Exception as e:
            mysql.connection.rollback()
            flash('Error updating house feature: {}'.format(str(e)), 'error')
            cur.execute("SELECT f_id as id, f_name as name, f_description as description, COALESCE(f_image, 'house_feature_placeholder.jpg') as image_filename FROM house_features WHERE f_id = %s", (id,))
            feature_data = dict_fetchone(cur)
            cur.close()
            return render_template('admin_edit_house_feature.html', feature=feature_data)

    # For GET requests
    query = """
        SELECT 
            f_id as id, 
            f_name as name, 
            f_description as description,
            f_image as image_filename
        FROM house_features 
        WHERE f_id = %s
    """
    cur.execute(query, (id,))
    feature_data = dict_fetchone(cur)
    cur.close()
    
    if feature_data is None:
        flash('House feature not found.', 'error')
        return redirect(url_for('admin_house_features'))
    
    # Process the image path
    if not feature_data.get('image_filename'):
        feature_data['image'] = 'img/house_placeholder.jpg'
    else:
        # Clean up the path
        image_path = feature_data['image_filename'].replace('\\', '/')
        # Remove any leading slashes or img/ prefixes
        image_path = image_path.lstrip('/').replace('img/', '').replace('static/', '')
        feature_data['image'] = image_path

    return render_template('admin_edit_house_feature.html', feature=feature_data)

@app.route('/admin/delete-house-feature/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_house_feature(id):
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM house_features WHERE f_id = %s", (id,))
        mysql.connection.commit()
        flash('House feature deleted successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error deleting house feature: {str(e)}', 'error')
    finally:
        cur.close()
    return redirect(url_for('admin_house_features'))

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    try:
        # Retrieve filter values from the request
        selected_type = request.args.get('house_type', None)
        selected_project = request.args.get('project', None)
        selected_feature = request.args.get('feature', None)
        search_query = request.args.get('search', None)

        # Fetch all houses (potentially filtered)
        house_query = """
            SELECT h.h_id as id, h.h_title as title, h.h_description as description, 
                   h.price, h.bedrooms, h.bathrooms, 
                   h.living_area as area, h.parking_space as parking,
                   t.t_name as type_name, p.p_name as project_name
            FROM house h
            LEFT JOIN house_type t ON h.t_id = t.t_id
            LEFT JOIN project p ON h.p_id = p.p_id
            WHERE 1=1
        """
        house_params = []

        if selected_type:
            house_query += " AND h.t_id = %s"
            house_params.append(selected_type)
        if selected_project:
            house_query += " AND h.p_id = %s"
            house_params.append(selected_project)
        if selected_feature:
            house_query += " AND h.h_id IN (SELECT h_id FROM house_features WHERE f_id = %s)"
            house_params.append(selected_feature)
        if search_query:
            sq = f"%{search_query}%"
            house_query += """
                AND (
                    h.h_title LIKE %s OR
                    h.h_description LIKE %s OR
                    t.t_name LIKE %s OR
                    p.p_name LIKE %s
                )
            """
            house_params.extend([sq, sq, sq, sq])

        house_query += " ORDER BY h.created_at DESC LIMIT 4"
        cur.execute(house_query, house_params)
        houses = dict_fetchall(cur)

        # Fetch all house types for the dropdown
        cur.execute("SELECT t_id as id, t_name as name FROM house_type")
        house_types = dict_fetchall(cur)

        # Fetch all projects for the dropdown
        cur.execute("SELECT p_id as id, p_name as name FROM project")
        projects = dict_fetchall(cur)
        
        # Fetch all house features for the dropdown
        cur.execute("SELECT f_id as id, f_name as name FROM house_features")
        house_features = dict_fetchall(cur)

        # Attach main_image_url to each house
        for house in houses:
            cur.execute("SELECT image_url FROM house_images WHERE house_id = %s AND is_main = 1 LIMIT 1", (house['id'],))
            row = cur.fetchone()
            if row:
                url = row[0].lstrip('/')
                if not url.startswith('static/uploads/'):
                    url = 'static/uploads/' + url.split('/')[-1]
                house['main_image_url'] = '/' + url
            else:
                cur.execute("SELECT image_url FROM house_images WHERE house_id = %s LIMIT 1", (house['id'],))
                if row:
                    url = row[0].lstrip('/')
                    if not url.startswith('static/uploads/'):
                        url = 'static/uploads/' + url.split('/')[-1]
                    house['main_image_url'] = '/' + url
                else:
                    house['main_image_url'] = None

            # Attach gallery_images (optional, for mini-gallery)
            cur.execute("SELECT image_url FROM house_images WHERE house_id = %s", (house['id'],))
            gallery_rows = cur.fetchall()
            house['gallery_images'] = []
            for row in gallery_rows:
                url = row[0].lstrip('/')
                if not url.startswith('static/uploads/'):
                    url = 'static/uploads/' + url.split('/')[-1]
                house['gallery_images'].append('/' + url)

        return render_template(
            'index.html',
            houses=houses,
            house_types=house_types,
            projects=projects,
            house_features=house_features,
            selected_type=selected_type,
            selected_project=selected_project,
            selected_feature=selected_feature
        )
    finally:
        cur.close()

def track_house_view(house_id, request):
    """Helper function to track house views with additional metadata"""
    cur = mysql.connection.cursor()
    
    # Get client IP address
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    
    # Log the view
    cur.execute("""
        INSERT INTO house_views (house_id, ip_address)
        VALUES (%s, %s)
    """, (house_id, ip)) 
    
    # Update the view count in the house table
    cur.execute("""
        UPDATE house 
        SET view_count = COALESCE(view_count, 0) + 1 
        WHERE h_id = %s
    """, (house_id,))
    
    mysql.connection.commit()
    cur.close()

@app.route('/house/<int:house_id>')
def house_detail(house_id):
    cur = mysql.connection.cursor()
    
    # First check if house exists
    cur.execute("SELECT h_id FROM house WHERE h_id = %s", (house_id,))
    if not cur.fetchone():
        cur.close()
        flash('บ้านไม่พบ', 'error')
        return redirect(url_for('index'))
    
    # Track the view
    track_house_view(house_id, request)
    
    # Get house details with view count
    cur.execute("""
        SELECT 
            h.h_title AS title, 
            h.h_description AS house_description,
            h.bedrooms, 
            h.bathrooms, 
            h.living_area,
            h.view_count,
            p.address AS project_address,
            p.description AS project_description,
            h.*, 
            p.*
        FROM house h
        LEFT JOIN project p ON h.p_id = p.p_id
        WHERE h.h_id = %s
    """, (house_id,))
    house = dict_fetchone(cur)

    # Attach gallery_images
    cur.execute("SELECT image_url FROM house_images WHERE house_id = %s", (house_id,))
    gallery_rows = cur.fetchall()
    house['gallery_images'] = []
    for row in gallery_rows:
        url = row[0].lstrip('/')
        if not url.startswith('static/uploads/'):
            url = 'static/uploads/' + url.split('/')[-1]
        house['gallery_images'].append('/' + url)

    # Set main_image_url
    if house['gallery_images']:
        house['main_image_url'] = house['gallery_images'][0]
    else:
        house['main_image_url'] = '/static/img/house_placeholder.jpg'

    return render_template('house_detail.html', house=house)

@app.route('/api/house/<int:house_id>/images', methods=['POST'])
def upload_house_images(house_id):
    if 'admin_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
            
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("INSERT INTO house_images (house_id, image_url, is_main) VALUES (%s, %s, %s)", (house_id, filename, 0))
                mysql.connection.commit()
                cur.close()
    
                return jsonify({'message': 'Image uploaded successfully'}), 200
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({'message': f'Error uploading image: {str(e)}'}), 500
    else:
        return jsonify({'message': 'File type not allowed'}), 400

@app.route('/admin/houses/<int:house_id>/delete-image/<int:image_id>', methods=['POST'])
@login_required
@admin_required
def delete_house_image_route(house_id, image_id):

    cur = mysql.connection.cursor()
    try:
        # Get the image URL before deleting (to remove the file)
        cur.execute("SELECT image_url FROM house_images WHERE id = %s", (image_id,))
        image_url_result = cur.fetchone()

        if image_url_result:
            file_to_delete = os.path.join(app.config['UPLOAD_FOLDER'], image_url_result[0])
            if os.path.exists(file_to_delete):
                os.remove(file_to_delete)

        # Delete the image record from the database
        cur.execute("DELETE FROM house_images WHERE id = %s", (image_id,))
        mysql.connection.commit()
        flash('House image deleted successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error deleting image: {str(e)}', 'error')
    finally:
        cur.close()
    return redirect(url_for('admin_edit_house', id=house_id))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    
    current_user_id = session.get('admin_id')
    is_super_admin = session.get('admin_role') == 'superadmin'
    
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    cur = mysql.connection.cursor()
    
    try:
        # Debug: Print current user and role
        print("\n=== DEBUG: SESSION AND DATABASE INFO ===")
        print(f"Session Data: {dict(session)}")
        print(f"Current User ID: {current_user_id}")
        print(f"Admin Role from Session: {session.get('admin_role')}")
        print(f"Is Super Admin: {is_super_admin}")
        
        # Debug: Check all admins in the database
        cur.execute("SELECT id, username, role, status FROM admins")
        all_admins = cur.fetchall()
        print("\nAll admins in database:")
        for admin in all_admins:
            print(f"- ID: {admin[0]}, Username: {admin[1]}, Role: {admin[2]}, Status: {admin[3]}")
        
        # Check if current user is in the database
        cur.execute("SELECT role, status FROM admins WHERE id = %s", (current_user_id,))
        current_user_db = cur.fetchone()
        print(f"\nCurrent user's DB record: {current_user_db}")
        
        # Double-check super admin status from DB
        is_super_admin_db = current_user_db and current_user_db[0] == 'superadmin' if current_user_db else False
        if is_super_admin != is_super_admin_db:
            print(f"WARNING: Session role mismatch! Session says superadmin: {is_super_admin}, DB says: {is_super_admin_db}")
            # Update session if there's a mismatch
            if current_user_db:
                session['admin_role'] = current_user_db[0]
                is_super_admin = is_super_admin_db
                print(f"Updated session role to: {session['admin_role']}")
        
        # Simple query to get all columns
        query = "SELECT * FROM admins WHERE 1=1"
        params = []
        
        # Regular admins can only see their own profile
        if not is_super_admin:
            query += " AND id = %s"
            params.append(current_user_id)
        
        # Apply search filter
        if search_query:
            query += " AND (username LIKE %s OR email LIKE %s OR first_name LIKE %s OR last_name LIKE %s)"
            search_param = f"%{search_query}%"
            params.extend([search_param] * 4)
        
        # Apply status filter
        if status_filter in ['active', 'inactive']:
            query += " AND status = %s"
            params.append(status_filter)
        
        # Order by creation date (newest first)
        query += " ORDER BY created_at DESC"
        
        # Debug: Print the final query and parameters
        print(f"Executing query: {query}")
        print(f"With params: {params}")
        
        # Execute query
        cur.execute(query, params)
        
        # Get column names
        columns = [col[0] for col in cur.description]
        
        # Fetch all rows and convert to list of dictionaries
        users = []
        for row in cur.fetchall():
            user = dict(zip(columns, row))
            # Format the date if it's a datetime object
            if 'created_at' in user and user['created_at'] and not isinstance(user['created_at'], str):
                user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M')
            users.append(user)
            
        print(f"Found {len(users)} users")
        
        return render_template('admin_users.html', 
                             users=users, 
                             search_query=search_query, 
                             status_filter=status_filter,
                             is_super_admin=is_super_admin,
                             current_user_id=current_user_id)
        
    except Exception as e:
        flash('เกิดข้อผิดพลาดในการโหลดข้อมูลผู้ใช้', 'error')
        print(f"Error loading users: {str(e)}")
        return render_template('admin_users.html', 
                             users=[], 
                             search_query=search_query, 
                             status_filter=status_filter,
                             is_super_admin=is_super_admin,
                             current_user_id=current_user_id)
        
    finally:
        cur.close()

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    
    # Only super admins can add new users
    if session.get('admin_role') != 'superadmin':
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'error')
        return redirect(url_for('admin_users'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        role = request.form.get('role', 'admin')  # Default to 'admin' if not specified
        status = request.form.get('status', 'active')  # Default to 'active' if not specified
        
        # Validate input
        if not all([username, email, first_name, last_name, password]):
            flash('กรุณากรอกข้อมูลให้ครบถ้วน', 'error')
            return render_template('admin_add_user.html', 
                                is_super_admin=True,  # Only super admins can access this page
                                form_data=request.form)
        
        # Validate password strength
        if len(password) < 8:
            flash('รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร', 'error')
            return render_template('admin_add_user.html',
                                is_super_admin=True,
                                form_data=request.form)
        
        # Check if username or email already exists
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cur.execute("SELECT id FROM admins WHERE username = %s", (username,))
            if cur.fetchone():
                flash('ชื่อผู้ใช้นี้มีอยู่แล้ว', 'error')
                return render_template('admin_add_user.html',
                                    is_super_admin=True,
                                    form_data=request.form)
                
            cur.execute("SELECT id FROM admins WHERE email = %s", (email,))
            if cur.fetchone():
                flash('อีเมลนี้มีผู้ใช้งานแล้ว', 'error')
                return render_template('admin_add_user.html',
                                    is_super_admin=True,
                                    form_data=request.form)
            
            # Hash the password
            hashed_password = generate_password_hash(password)
            
            # Insert new admin user
            cur.execute("""
                INSERT INTO admins (username, email, password, first_name, last_name, role, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (username, email, hashed_password, first_name, last_name, role, status))
            
            mysql.connection.commit()
            flash('เพิ่มผู้ใช้งานเรียบร้อยแล้ว', 'success')
            return redirect(url_for('admin_users'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาดในการสร้างผู้ใช้: {str(e)}', 'error')
            return render_template('admin_add_user.html',
                                is_super_admin=True,
                                form_data=request.form)
            
        finally:
            cur.close()
    
    # For GET request, render the form
    return render_template('admin_add_user.html',
                         is_super_admin=True)

@app.route('/admin/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(id):
        
    current_user_id = session.get('admin_id')
    is_super_admin = session.get('admin_role') == 'superadmin'
    
    # Regular users can only edit their own profile
    if not is_super_admin and id != current_user_id:
        flash('คุณไม่มีสิทธิ์แก้ไขผู้ใช้นี้', 'error')
        return redirect(url_for('admin_users'))

    cur = mysql.connection.cursor()
    
    try:
        # Get the current user data
        cur.execute("""
            SELECT id, username, email, first_name, last_name, role, status 
            FROM admins WHERE id = %s
        """, (id,))
        user_data = dict_fetchone(cur)
        
        if user_data is None:
            flash('ไม่พบผู้ใช้งาน', 'error')
            return redirect(url_for('admin_users'))
            
        # Count other super admins for the template
        other_super_admins = 0
        if user_data['role'] == 'superadmin':
            cur.execute("SELECT COUNT(*) as count FROM admins WHERE role = 'superadmin' AND id != %s", (id,))
            other_super_admins = cur.fetchone()['count']

        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            
            # Only super admins can change roles and status
            if is_super_admin:
                role = request.form.get('role', user_data['role'])
                status = request.form.get('status', user_data['status'])
                
                # Prevent removing last super admin
                if user_data['role'] == 'superadmin' and role != 'superadmin' and other_super_admins == 0:
                    flash('ไม่สามารถเปลี่ยนบทบาทของผู้ดูแลระบบหลักคนสุดท้ายได้', 'error')
                    return redirect(url_for('admin_edit_user', id=id))
            else:
                # Regular users can't change their own role or status
                role = user_data['role']
                status = user_data['status']
                
            password = request.form.get('password')

            # Validate required fields
            if not all([username, email, first_name, last_name]):
                flash('กรุณากรอกข้อมูลให้ครบถ้วน', 'error')
                return render_template('admin_edit_user.html', 
                                    user=user_data, 
                                    is_super_admin=is_super_admin,
                                    current_user_id=current_user_id,
                                    other_super_admins=other_super_admins)

            # Check for existing username/email excluding the current user
            cur.execute("SELECT id FROM admins WHERE username = %s AND id != %s", (username, id))
            if cur.fetchone():
                flash('ชื่อผู้ใช้งานนี้มีอยู่แล้ว', 'error')
                return render_template('admin_edit_user.html', 
                                    user=user_data, 
                                    is_super_admin=is_super_admin,
                                    current_user_id=current_user_id,
                                    other_super_admins=other_super_admins)

            cur.execute("SELECT id FROM admins WHERE email = %s AND id != %s", (email, id))
            if cur.fetchone():
                flash('อีเมลนี้มีผู้ใช้งานแล้ว', 'error')
                return render_template('admin_edit_user.html', 
                                    user=user_data, 
                                    is_super_admin=is_super_admin,
                                    current_user_id=current_user_id,
                                    other_super_admins=other_super_admins)

            try:
                if password:
                    hashed_password = generate_password_hash(password)
                    cur.execute("""
                        UPDATE admins 
                        SET username=%s, email=%s, first_name=%s, last_name=%s, 
                            role=%s, status=%s, password=%s
                        WHERE id=%s
                    """, (username, email, first_name, last_name, role, status, hashed_password, id))
                else:
                    cur.execute("""
                        UPDATE admins 
                        SET username=%s, email=%s, first_name=%s, last_name=%s, 
                            role=%s, status=%s
                        WHERE id=%s
                    """, (username, email, first_name, last_name, role, status, id))
                
                mysql.connection.commit()
                
                # Update session if user is editing their own profile
                if id == current_user_id:
                    session['admin_username'] = username
                    session['admin_email'] = email
                    session['admin_first_name'] = first_name
                    session['admin_last_name'] = last_name
                    session['admin_role'] = role
                
                flash('อัปเดตข้อมูลผู้ใช้เรียบร้อยแล้ว', 'success')
                return redirect(url_for('admin_users'))
                
            except Exception as e:
                mysql.connection.rollback()
                flash('เกิดข้อผิดพลาดในการอัปเดตข้อมูลผู้ใช้', 'error')
                print(f"Error updating user: {str(e)}")
        
        # For GET request or if there was an error, render the edit form
        return render_template('admin_edit_user.html',
                            user=user_data,
                            is_super_admin=is_super_admin,
                            current_user_id=current_user_id,
                            other_super_admins=other_super_admins)
                            
    except Exception as e:
        flash('เกิดข้อผิดพลาดในการโหลดข้อมูลผู้ใช้', 'error')
        print(f"Error loading user data: {str(e)}")
        return redirect(url_for('admin_users'))
        
    finally:
        cur.close()

@app.route('/promote-to-superadmin/<username>')
def promote_to_superadmin(username):
    """Temporary route to promote an existing admin to superadmin"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # First, check if the user exists
        cur.execute("SELECT id FROM admins WHERE username = %s", (username,))
        if not cur.fetchone():
            return f'No user found with username: {username}', 404
        
        # Update the user's role to superadmin
        cur.execute("""
            UPDATE admins 
            SET role = 'superadmin'
            WHERE username = %s
        """, (username,))
            
        mysql.connection.commit()
        return f'Successfully promoted {username} to superadmin. You can now log in with this account.'
        
    except Exception as e:
        mysql.connection.rollback()
        return f'Error promoting user: {str(e)}', 500
    finally:
        cur.close()

@app.route('/create-super-admin/<username>/<email>/<password>')
def create_super_admin(username, email, password):
    """Temporary route to create a super admin account"""
    try:
        from werkzeug.security import generate_password_hash
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if username or email already exists
        cur.execute("SELECT id FROM admins WHERE username = %s OR email = %s", (username, email))
        if cur.fetchone():
            return 'Username or email already exists', 400
        
        # Create super admin
        hashed_password = generate_password_hash(password)
        cur.execute("""
            INSERT INTO admins (username, email, password, first_name, last_name, role, status, created_at, updated_at)
            VALUES (%s, %s, %s, 'Admin', 'User', 'superadmin', 'active', NOW(), NOW())
        """, (username, email, hashed_password))
        
        mysql.connection.commit()
        return f'Super admin created with username: {username} and email: {email}'
        
    except Exception as e:
        return f'Error creating super admin: {str(e)}', 500
    finally:
        cur.close()

@app.route('/debug/db')
def debug_db():
    """Temporary debug route to check database structure"""
    # Temporarily allowing access without authentication for debugging
    pass
    
    result = {}
    cur = mysql.connection.cursor()
    
    try:
        # Get all tables
        cur.execute('SHOW TABLES')
        tables = [table[0] for table in cur.fetchall()]
        result['tables'] = tables
        
        # Check if admins table exists
        if 'admins' in tables:
            # Get table structure
            cur.execute('DESCRIBE admins')
            result['admins_structure'] = cur.fetchall()
            
            # Get all admin users
            cur.execute('SELECT * FROM admins')
            columns = [col[0] for col in cur.description]
            result['admins_data'] = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        return result
    except Exception as e:
        return {'error': str(e), 'type': type(e).__name__}
    finally:
        cur.close()

@app.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(id):
    
    # Only super admins can delete users
    if session.get('admin_role') != 'superadmin':
        flash('คุณไม่มีสิทธิ์ลบผู้ใช้งาน', 'error')
        return redirect(url_for('admin_users'))
    
    # Prevent deleting self
    if id == session.get('admin_id'):
        flash('ไม่สามารถลบบัญชีของตัวเองได้', 'error')
        return redirect(url_for('admin_users'))
    
    cur = mysql.connection.cursor()
    
    try:
        # Check if user exists and get role
        cur.execute("SELECT role FROM admins WHERE id = %s", (id,))
        user = cur.fetchone()
        
        if not user:
            flash('ไม่พบผู้ใช้งาน', 'error')
            return redirect(url_for('admin_users'))
            
        # Prevent deleting the last super admin
        if user['role'] == 'superadmin':
            cur.execute("SELECT COUNT(*) as count FROM admins WHERE role = 'superadmin'")
            superadmin_count = cur.fetchone()['count']
            if superadmin_count <= 1:
                flash('ไม่สามารถลบผู้ดูแลระบบหลักคนสุดท้ายได้', 'error')
                return redirect(url_for('admin_users'))
        
        # Delete the user
        cur.execute("DELETE FROM admins WHERE id = %s", (id,))
        mysql.connection.commit()
        
        flash('ลบผู้ใช้งานเรียบร้อยแล้ว', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash('เกิดข้อผิดพลาดในการลบผู้ใช้งาน', 'error')
        print(f"Error deleting user: {str(e)}")
    finally:
        cur.close()
    
    return redirect(url_for('admin_users'))

@app.route('/house-types')
def house_types_page():
    cur = mysql.connection.cursor()
    cur.execute("SELECT t_id as id, t_name as name, COALESCE(t_image, 'house_type_placeholder.jpg') as image FROM house_type")
    house_types = dict_fetchall(cur)
    cur.close()
    return render_template('house_types.html', house_types=house_types)

@app.route('/houses/type/<int:type_id>')
def houses_by_type(type_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT h.h_id as id, h.h_title as title, h.h_description as description, 
                   h.price, h.bedrooms, h.bathrooms, 
                   h.living_area as area, h.parking_space as parking,
                   t.t_name as type_name, p.p_name as project_name
            FROM house h
            LEFT JOIN house_type t ON h.t_id = t.t_id
            LEFT JOIN project p ON h.p_id = p.p_id
            WHERE h.t_id = %s
        """, (type_id,))
        houses = dict_fetchall(cur)
        # Attach main_image_url and gallery_images to each house
        for house in houses:
            cur.execute("SELECT image_url FROM house_images WHERE house_id = %s AND is_main = 1 LIMIT 1", (house['id'],))
            row = cur.fetchone()
            if row:
                url = row[0].lstrip('/')
                if not url.startswith('static/uploads/'):
                    url = 'static/uploads/' + url.split('/')[-1]
                house['main_image_url'] = '/' + url
            else:
                cur.execute("SELECT image_url FROM house_images WHERE house_id = %s LIMIT 1", (house['id'],))
                row = cur.fetchone()
                if row:
                    url = row[0].lstrip('/')
                    if not url.startswith('static/uploads/'):
                        url = 'static/uploads/' + url.split('/')[-1]
                    house['main_image_url'] = '/' + url
                else:
                    house['main_image_url'] = None
            cur.execute("SELECT image_url FROM house_images WHERE house_id = %s", (house['id'],))
            gallery_rows = cur.fetchall()
            house['gallery_images'] = []
            for row in gallery_rows:
                url = row[0].lstrip('/')
                if not url.startswith('static/uploads/'):
                    url = 'static/uploads/' + url.split('/')[-1]
                house['gallery_images'].append('/' + url)
        
        # Fetch all house types and projects for the dropdowns
        cur.execute("SELECT t_id as id, t_name as name FROM house_type")
        house_types = dict_fetchall(cur)
        
        cur.execute("SELECT p_id as id, p_name as name FROM project")
        projects = dict_fetchall(cur)
        
        return render_template(
            'houses_list.html', 
            houses=houses, 
            title="บ้านตามประเภท",
            house_types=house_types,
            projects=projects,
            request=request,
            selected_type=type_id
        )
    finally:
        cur.close()

@app.route('/projects')
def projects_page():
    cur = mysql.connection.cursor()
    cur.execute("SELECT p_id as id, p_name as name, COALESCE(p_image, 'project_placeholder.jpg') as image FROM project")
    projects = dict_fetchall(cur)
    cur.close()
    return render_template('projects.html', projects=projects)

@app.route('/houses/project/<int:project_id>')
def houses_by_project(project_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT h.h_id as id, h.h_title as title, h.h_description as description, 
                   h.price, h.bedrooms, h.bathrooms, 
                   h.living_area as area, h.parking_space as parking,
                   t.t_name as type_name, p.p_name as project_name
            FROM house h
            LEFT JOIN house_type t ON h.t_id = t.t_id
            LEFT JOIN project p ON h.p_id = p.p_id
            WHERE h.p_id = %s
        """, (project_id,))
        houses = dict_fetchall(cur)
        # Attach main_image_url and gallery_images to each house
        for house in houses:
            cur.execute("SELECT image_url FROM house_images WHERE house_id = %s AND is_main = 1 LIMIT 1", (house['id'],))
            row = cur.fetchone()
            if row:
                url = row[0].lstrip('/')
                if not url.startswith('static/uploads/'):
                    url = 'static/uploads/' + url.split('/')[-1]
                house['main_image_url'] = '/' + url
            else:
                cur.execute("SELECT image_url FROM house_images WHERE house_id = %s LIMIT 1", (house['id'],))
                row = cur.fetchone()
                if row:
                    url = row[0].lstrip('/')
                    if not url.startswith('static/uploads/'):
                        url = 'static/uploads/' + url.split('/')[-1]
                    house['main_image_url'] = '/' + url
                else:
                    house['main_image_url'] = None
            cur.execute("SELECT image_url FROM house_images WHERE house_id = %s", (house['id'],))
            gallery_rows = cur.fetchall()
            house['gallery_images'] = []
            for row in gallery_rows:
                url = row[0].lstrip('/')
                if not url.startswith('static/uploads/'):
                    url = 'static/uploads/' + url.split('/')[-1]
                house['gallery_images'].append('/' + url)
        
        # Fetch all house types and projects for the dropdowns
        cur.execute("SELECT t_id as id, t_name as name FROM house_type")
        house_types = dict_fetchall(cur)
        
        cur.execute("SELECT p_id as id, p_name as name FROM project")
        projects = dict_fetchall(cur)
        
        return render_template(
            'houses_list.html', 
            houses=houses, 
            title="บ้านในโครงการ",
            house_types=house_types,
            projects=projects,
            request=request,
            selected_project=project_id
        )
    finally:
        cur.close()

@app.route('/house-features')
def house_features_page():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            f_id as id, 
            f_name as name, 
            f_description as description, 
            CASE 
                WHEN f_image IS NULL OR f_image = '' THEN 'house_placeholder.jpg'
                ELSE f_image 
            END as image 
        FROM house_features
    """)
    features = dict_fetchall(cur)
    cur.close()
    return render_template('house_features.html', features=features)

@app.route('/houses/feature/<int:feature_id>')
def houses_by_feature(feature_id):
    cur = mysql.connection.cursor()
    try:
        # First, get the feature name to determine if it's a bedroom filter
        cur.execute("SELECT f_name FROM house_features WHERE f_id = %s", (feature_id,))
        feature = cur.fetchone()
        
        if not feature:
            return render_template('houses_list.html', houses=[], title="ไม่พบลักษณะบ้านที่ระบุ")
            
        feature_name = feature[0]
        
        # Check if this is a bedroom filter (e.g., "3 ห้องนอน")
        import re
        bedroom_match = re.search(r'(\d+)\s*ห้องนอน', feature_name)
        
        if bedroom_match:
            # This is a bedroom filter
            bedroom_count = int(bedroom_match.group(1))
            query = """
                SELECT h.h_id as id, h.h_title as title, h.h_description as description, 
                       h.price, h.bedrooms, h.bathrooms, 
                       h.living_area as area, h.parking_space as parking,
                       t.t_name as type_name, p.p_name as project_name
                FROM house h
                LEFT JOIN house_type t ON h.t_id = t.t_id
                LEFT JOIN project p ON h.p_id = p.p_id
                WHERE h.bedrooms = %s
            """
            params = (bedroom_count,)
        else:
            # This is a regular feature filter
            query = """
                SELECT h.h_id as id, h.h_title as title, h.h_description as description, 
                       h.price, h.bedrooms, h.bathrooms, 
                       h.living_area as area, h.parking_space as parking,
                       t.t_name as type_name, p.p_name as project_name
                FROM house h
                LEFT JOIN house_type t ON h.t_id = t.t_id
                LEFT JOIN project p ON h.p_id = p.p_id
                JOIN house_feature_mapping hfm ON h.h_id = hfm.house_id
                WHERE hfm.feature_id = %s
            """
            params = (feature_id,)
            
        cur.execute(query, params)
        houses = dict_fetchall(cur)
        # Attach main_image_url and gallery_images to each house
        for house in houses:
            cur.execute("SELECT image_url FROM house_images WHERE house_id = %s AND is_main = 1 LIMIT 1", (house['id'],))
            row = cur.fetchone()
            if row:
                url = row[0].lstrip('/')
                if not url.startswith('static/uploads/'):
                    url = 'static/uploads/' + url.split('/')[-1]
                house['main_image_url'] = '/' + url
            else:
                cur.execute("SELECT image_url FROM house_images WHERE house_id = %s LIMIT 1", (house['id'],))
                row = cur.fetchone()
                if row:
                    url = row[0].lstrip('/')
                    if not url.startswith('static/uploads/'):
                        url = 'static/uploads/' + url.split('/')[-1]
                    house['main_image_url'] = '/' + url
                else:
                    house['main_image_url'] = None
            cur.execute("SELECT image_url FROM house_images WHERE house_id = %s", (house['id'],))
            gallery_rows = cur.fetchall()
            house['gallery_images'] = []
            for row in gallery_rows:
                url = row[0].lstrip('/')
                if not url.startswith('static/uploads/'):
                    url = 'static/uploads/' + url.split('/')[-1]
                house['gallery_images'].append('/' + url)
        return render_template('houses_list.html', houses=houses, title="บ้านตามลักษณะ")
    finally:
        cur.close()

@app.route('/check_house_structure')
def check_house_structure():
    cur = mysql.connection.cursor()
    try:
        cur.execute("SHOW COLUMNS FROM house")
        columns = cur.fetchall()
        return jsonify([{
            'Field': col[0],
            'Type': col[1],
            'Null': col[2],
            'Key': col[3],
            'Default': col[4],
            'Extra': col[5]
        } for col in columns])
    finally:
        cur.close()

@app.route('/check_house_images')
def check_house_images():
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT h_id, h_title, h_image FROM house LIMIT 5")
        houses = dict_fetchall(cur)
        return jsonify(houses)
    finally:
        cur.close()

@app.route('/houses', methods=['GET'])
def houses_list():
    cur = mysql.connection.cursor()
    # Filters - use the same parameter names as index route
    selected_type = request.args.get('house_type', None)
    selected_project = request.args.get('project', None)
    selected_feature = request.args.get('feature', None)
    bedrooms = request.args.get('bedrooms', None)
    search_query = request.args.get('search', None)
    # Pagination
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
    except ValueError:
        page = 1
        per_page = 12
    offset = (page - 1) * per_page

    # Build filter query
    house_query = """
        SELECT h.h_id as id, h.h_title as title, h.h_description as description, 
               h.price, h.bedrooms, h.bathrooms, 
               h.living_area as area, h.parking_space as parking,
               t.t_name as type_name, p.p_name as project_name
        FROM house h
        LEFT JOIN house_type t ON h.t_id = t.t_id
        LEFT JOIN project p ON h.p_id = p.p_id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) FROM house h LEFT JOIN house_type t ON h.t_id = t.t_id LEFT JOIN project p ON h.p_id = p.p_id WHERE 1=1"
    house_params = []
    count_params = []

    if selected_type:
        house_query += " AND h.t_id = %s"
        count_query += " AND h.t_id = %s"
        house_params.append(selected_type)
        count_params.append(selected_type)
    if selected_project:
        house_query += " AND h.p_id = %s"
        count_query += " AND h.p_id = %s"
        house_params.append(selected_project)
        count_params.append(selected_project)
    if selected_feature:
        house_query += " AND h.f_id = %s"
        count_query += " AND h.f_id = %s"
        house_params.append(selected_feature)
        count_params.append(selected_feature)
    # Add bedrooms filter if provided
    if bedrooms and bedrooms.isdigit():
        house_query += " AND h.bedrooms = %s"
        count_query += " AND h.bedrooms = %s"
        house_params.append(int(bedrooms))
        count_params.append(int(bedrooms))
        
    if search_query:
        sq = f"%{search_query}%"
        house_query += """
            AND (
                h.h_title LIKE %s OR
                h.h_description LIKE %s OR
                t.t_name LIKE %s OR
                p.p_name LIKE %s
            )
        """
        count_query += """
            AND (
                h.h_title LIKE %s OR
                h.h_description LIKE %s OR
                t.t_name LIKE %s OR
                p.p_name LIKE %s
            )
        """
        house_params.extend([sq, sq, sq, sq])
        count_params.extend([sq, sq, sq, sq])

    house_query += " ORDER BY h.created_at DESC LIMIT %s OFFSET %s"
    house_params.extend([per_page, offset])

    # Get total count for pagination
    cur.execute(count_query, count_params)
    total = cur.fetchone()[0]

    # Get paginated houses
    cur.execute(house_query, house_params)
    houses = dict_fetchall(cur)
       # Attach main_image_url and gallery_images to each house
    for house in houses:
       # Attach main_image_url
       cur.execute("SELECT image_url FROM house_images WHERE house_id = %s AND is_main = 1 LIMIT 1", (house['id'],))
       row = cur.fetchone()
       if row:
           url = row[0].lstrip('/')
           if not url.startswith('static/uploads/'):
               url = 'static/uploads/' + url.split('/')[-1]
           house['main_image_url'] = '/' + url
       else:
           cur.execute("SELECT image_url FROM house_images WHERE house_id = %s LIMIT 1", (house['id'],))
           row = cur.fetchone()
           if row:
               url = row[0].lstrip('/')
               if not url.startswith('static/uploads/'):
                   url = 'static/uploads/' + url.split('/')[-1]
               house['main_image_url'] = '/' + url
           else:
               house['main_image_url'] = None

       # Attach gallery_images (for mini-gallery)
       cur.execute("SELECT image_url FROM house_images WHERE house_id = %s", (house['id'],))
       gallery_rows = cur.fetchall()
       house['gallery_images'] = []
       for row in gallery_rows:
           url = row[0].lstrip('/')
           if not url.startswith('static/uploads/'):
               url = 'static/uploads/' + url.split('/')[-1]
           house['gallery_images'].append('/' + url)

    # Fetch all house types for the dropdown
    cur.execute("SELECT t_id as id, t_name as name FROM house_type")
    house_types = dict_fetchall(cur)

    # Fetch all projects for the dropdown
    cur.execute("SELECT p_id as id, p_name as name FROM project")
    projects = dict_fetchall(cur)

    # Fetch all house features for the dropdown
    cur.execute("SELECT f_id as id, f_name as name FROM house_features")
    house_features = dict_fetchall(cur)

    # Pagination helper object
    class Pagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1
        def iter_pages(self, left_edge=2, left_current=2, right_current=2, right_edge=2):
            last = 0
            for num in range(1, self.pages + 1):
                if (
                    num <= left_edge
                    or (num > self.page - left_current - 1 and num < self.page + right_current)
                    or num > self.pages - right_edge
                ):
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num

    pagination = Pagination(page, per_page, total)
    cur.close()
    return render_template(
        'results.html',
        houses=houses,
        house_types=house_types,
        projects=projects,
        house_features=house_features,
        pagination=pagination,
        request=request,
        selected_type=selected_type,
        selected_project=selected_project,
        selected_feature=selected_feature
    )

@app.route('/admin/houses/<int:house_id>/set-main-image/<int:image_id>', methods=['POST'])
@login_required
@admin_required
def set_main_house_image(house_id, image_id):
    cur = mysql.connection.cursor()
    try:
        # Set all images for this house to is_main=0
        cur.execute("UPDATE house_images SET is_main=0 WHERE house_id=%s", (house_id,))
        # Set the selected image to is_main=1
        cur.execute("UPDATE house_images SET is_main=1 WHERE id=%s", (image_id,))
        mysql.connection.commit()
        flash('Main image updated!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error setting main image: {str(e)}', 'error')
    finally:
        cur.close()
    return redirect(url_for('admin_edit_house', id=house_id))

@csrf.exempt
@app.route('/search_by_image', methods=['POST'])
def search_by_image():
    file = request.files.get('query_img') or request.files.get('file')
    if not file:
        return "No file part in request.", 400
    if file.filename == '':
        print("[ERROR] File part present but filename is empty.")
        return "No selected file.", 400

    # Save the uploaded image
    filename = secure_filename(file.filename)
    upload_dir = os.path.join('static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)  # Ensure upload directory exists
    upload_path = os.path.join(upload_dir, filename)
    file.save(upload_path)

    # Run CBIR search
    results = search_similar_images(upload_path, top_k=6)
    print("[DEBUG] CBIR Results:", results)

    # Convert numpy strings to regular strings and get filenames
    cbir_results = []
    for r in results:
        try:
            img_filename = os.path.basename(str(r['filename']))
            similarity = float(r['similarity'])
            
            # Check if the image file exists in the uploads directory
            possible_paths = [
                os.path.join('static', 'uploads', img_filename),
                img_filename,
                os.path.join('static', 'uploads', os.path.basename(img_filename))
            ]
            
            # Check if any of the paths exist
            if not any(os.path.exists(path) for path in possible_paths):
                print(f"[DEBUG] Image file not found: {img_filename}")
                continue
                
            cbir_results.append({
                'filename': img_filename,
                'similarity': similarity
            })
        except (ValueError, KeyError) as e:
            print(f"[WARNING] Invalid result format: {r}, error: {e}")
    
    if not cbir_results:
        return render_template('results.html', houses=[], query_image=filename, pagination=None)

    cur = mysql.connection.cursor()
    # Get all existing image filenames from the database
    cur.execute("SELECT id, house_id, image_url FROM house_images WHERE image_url IS NOT NULL")
    all_images = cur.fetchall()
    
    # Create a mapping of basenames to their full paths
    existing_images = {}
    for img_id, house_id, image_url in all_images:
        if not image_url:
            continue
        img_filename = os.path.basename(str(image_url).split('/')[-1])  # Get just the filename
        existing_images[img_filename] = {
            'house_id': house_id,
            'image_url': image_url
        }
    
    # Get all valid house images from the database
    cur.execute("""
        SELECT hi.id, hi.house_id, hi.image_url, h.h_title 
        FROM house_images hi
        JOIN house h ON hi.house_id = h.h_id
        WHERE hi.image_url IS NOT NULL
    """)
    db_images = cur.fetchall()
    
    # Create a mapping of filenames to their database records
    valid_images = {}
    for img_id, house_id, image_url, house_title in db_images:
        if not image_url:
            continue
            
        # Extract just the filename
        img_filename = os.path.basename(str(image_url).split('/')[-1])
        
        # Check if the file exists on disk
        possible_paths = [
            os.path.join('static', 'uploads', img_filename),
            img_filename,
            os.path.join('static', 'uploads', os.path.basename(img_filename))
        ]
        
        if not any(os.path.exists(path) for path in possible_paths):
            print(f"[DEBUG] Image file not found in database: {img_filename}")
            continue
            
        valid_images[img_filename] = {
            'id': img_id,
            'house_id': house_id,
            'image_url': image_url,
            'house_title': house_title
        }
    
    # Filter CBIR results to only include existing images and keep track of best matches
    house_best_matches = {}  # house_id -> best matching image info
    
    for result in cbir_results:
        img_filename = result['filename']
        
        # Try to find a matching image in our valid images
        if img_filename in valid_images:
            img_data = valid_images[img_filename]
            house_id = img_data['house_id']
            similarity = result['similarity']
            
            # Only keep the best match for each house
            if house_id not in house_best_matches or similarity > house_best_matches[house_id]['similarity']:
                house_best_matches[house_id] = {
                    'filename': img_filename,
                    'similarity': similarity,
                    'image_url': img_data['image_url'],
                    'house_title': img_data['house_title']
                }
    
    if not house_best_matches:
        cur.close()
        return render_template('results.html', 
                            houses=[], 
                            query_image=filename, 
                            pagination=None,
                            message="No matching houses found with similar images.")
    
    # Sort houses by similarity (highest first) and take top 5
    top_houses = sorted(
        house_best_matches.items(),
        key=lambda x: x[1]['similarity'],
        reverse=True
    )[:5]  # Get top 5 most similar houses
    
    matched_house_ids = {house_id for house_id, _ in top_houses}
    image_to_house = {info['filename']: house_id for house_id, info in top_houses}
    
    # Create a mapping of house_id to its best similarity score
    house_similarities = {house_id: info['similarity'] for house_id, info in top_houses}

    if not matched_house_ids:
        cur.close()
        return render_template('results.html', houses=[], query_image=filename, pagination=None)

    # Fetch houses for matched house_ids
    format_strings = ','.join(['%s'] * len(matched_house_ids))
    query = f'''
        SELECT h.h_id as id, h.h_title as title, h.h_description as description, 
               h.price, h.bedrooms, h.bathrooms, 
               h.living_area as area, h.parking_space as parking,
               h.no_of_floors as floors, h.status,
               h.latitude, h.longitude,
               t.t_name as type_name, p.p_name as project_name
        FROM house h
        LEFT JOIN house_type t ON h.t_id = t.t_id
        LEFT JOIN project p ON h.p_id = p.p_id
        WHERE h.h_id IN ({format_strings})
    '''
    cur.execute(query, tuple(matched_house_ids))
    houses = dict_fetchall(cur)
    # Attach similarity score and images to each house
    for house in houses:
        house_id = house['id']
        # Get the best similarity score we already calculated for this house
        house_similarity = house_similarities.get(house_id, 0)
        
        # Get all images for this house
        cur.execute("SELECT image_url FROM house_images WHERE house_id = %s", (house_id,))
        gallery_rows = cur.fetchall()
        house['gallery_images'] = []
        
        for row in gallery_rows:
            if not row or not row[0]:
                continue
                
            # Handle both full paths and filenames
            url = str(row[0]).lstrip('/')
            img_filename = os.path.basename(url)
            
            # Create the correct URL for display
            if not url.startswith(('http', 'static/')):
                display_url = f"static/uploads/{img_filename}"
            else:
                display_url = url
                
            # Ensure the URL starts with a slash for web access
            if not display_url.startswith('/'):
                display_url = '/' + display_url
                
            house['gallery_images'].append(display_url)
        
        # Set the best image as the main image (or first image if no best match)
        best_match = house_best_matches.get(house_id, {})
        if best_match and 'image_url' in best_match:
            best_url = best_match['image_url'].lstrip('/')
            if not best_url.startswith(('http', 'static/')):
                best_url = f"static/uploads/{os.path.basename(best_url)}"
            if not best_url.startswith('/'):
                best_url = '/' + best_url
            house['main_image_url'] = best_url
        else:
            house['main_image_url'] = house['gallery_images'][0] if house['gallery_images'] else '/static/img/house_placeholder.jpg'
        
        # Set the similarity score
        house['similarity'] = house_similarity
    cur.close()

    # Sort houses by similarity (descending) and ensure we only return up to 5
    houses.sort(key=lambda x: x.get('similarity', 0), reverse=True)
    houses = houses[:5]  # Limit to top 5 most similar houses

    return render_template('results.html', houses=houses, query_image=filename, pagination=None)



@app.route('/cbir-results')
def cbir_results():
    results = session.get('cbir_results', [])
    query_image = session.get('cbir_query_image', None)
    # Optionally clear session after use
    session.pop('cbir_results', None)
    session.pop('cbir_query_image', None)
    return render_template('results.html', results=results, query_image=query_image)

@app.route('/test_upload', methods=['POST'])
def test_upload():
    print("Test upload files:", request.files)
    print("Test upload form:", request.form)
    print("Test upload content-type:", request.content_type)
    return "OK"

@app.template_filter('currency')
def currency_filter(value):
    try:
        return "{:,.0f} ฿".format(float(value))
    except (ValueError, TypeError):
        return value

@app.route('/api/chart-data')
def get_chart_data():
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    cur = mysql.connection.cursor()
    
    # Get filter parameters
    selected_type = request.args.get('house_type') or None
    selected_project = request.args.get('project') or None
    selected_status = request.args.get('house_status') or None
    selected_bedrooms = request.args.get('bedrooms') or None
    selected_bathrooms = request.args.get('bathrooms') or None
    selected_living_area = request.args.get('living_area') or None

    # Base query for filtering
    query = "SELECT * FROM house WHERE 1=1"
    params = []
    
    if selected_type:
        query += " AND t_id = %s"
        params.append(selected_type)
    if selected_project:
        query += " AND p_id = %s"
        params.append(selected_project)
    if selected_status:
        query += " AND status = %s"
        params.append(selected_status)
    if selected_bedrooms:
        query += " AND bedrooms = %s"
        params.append(selected_bedrooms)
    if selected_bathrooms:
        query += " AND bathrooms = %s"
        params.append(selected_bathrooms)
    if selected_living_area:
        query += " AND living_area = %s"
        params.append(selected_living_area)

    cur.execute(query, params)
    houses = dict_fetchall(cur)

    # --- CHART DATA QUERIES ---
    # Houses by Type
    houses_by_type_query = """
        SELECT ht.t_name as name, COUNT(h.h_id) as house_count
        FROM house_type ht
        LEFT JOIN house h ON ht.t_id = h.t_id
        WHERE 1 = 1
    """
    houses_by_type_params = []
    if selected_project:
        houses_by_type_query += " AND h.p_id = %s"
        houses_by_type_params.append(selected_project)
    if selected_type:
        houses_by_type_query += " AND ht.t_id = %s"
        houses_by_type_params.append(selected_type)
    houses_by_type_query += " GROUP BY ht.t_name"
    cur.execute(houses_by_type_query, houses_by_type_params)
    houses_by_type_data = dict_fetchall(cur)
    
    # Houses by Project
    houses_by_project_query = """
        SELECT p.p_name as name, COUNT(h.h_id) as house_count
        FROM project p
        LEFT JOIN house h ON p.p_id = h.p_id
        WHERE 1 = 1
    """
    houses_by_project_params = []
    if selected_type:
        houses_by_project_query += " AND h.t_id = %s"
        houses_by_project_params.append(selected_type)
    if selected_project:
        houses_by_project_query += " AND p.p_id = %s"
        houses_by_project_params.append(selected_project)
    houses_by_project_query += " GROUP BY p.p_name"
    cur.execute(houses_by_project_query, houses_by_project_params)
    houses_by_project_data = dict_fetchall(cur)
    
    # Houses by Status
    houses_status_query = "SELECT status, COUNT(h_id) as count FROM house WHERE 1=1"
    houses_status_params = []
    if selected_type:
        houses_status_query += " AND t_id = %s"
        houses_status_params.append(selected_type)
    if selected_project:
        houses_status_query += " AND p_id = %s"
        houses_status_params.append(selected_project)
    houses_status_query += " GROUP BY status"
    cur.execute(houses_status_query, houses_status_params)
    houses_by_status_data = dict_fetchall(cur)
    
    # Houses by Bedrooms
    houses_bedrooms_query = "SELECT bedrooms as name, COUNT(h_id) as count FROM house WHERE bedrooms IS NOT NULL"
    houses_bedrooms_params = []
    if selected_type:
        houses_bedrooms_query += " AND t_id = %s"
        houses_bedrooms_params.append(selected_type)
    if selected_project:
        houses_bedrooms_query += " AND p_id = %s"
        houses_bedrooms_params.append(selected_project)
    houses_bedrooms_query += " GROUP BY bedrooms ORDER BY bedrooms"
    cur.execute(houses_bedrooms_query, houses_bedrooms_params)
    houses_by_bedrooms_data = dict_fetchall(cur)
    
    # Houses by Bathrooms
    houses_bathrooms_query = "SELECT bathrooms as name, COUNT(h_id) as count FROM house WHERE bathrooms IS NOT NULL"
    houses_bathrooms_params = []
    if selected_type:
        houses_bathrooms_query += " AND t_id = %s"
        houses_bathrooms_params.append(selected_type)
    if selected_project:
        houses_bathrooms_query += " AND p_id = %s"
        houses_bathrooms_params.append(selected_project)
    houses_bathrooms_query += " GROUP BY bathrooms ORDER BY bathrooms"
    cur.execute(houses_bathrooms_query, houses_bathrooms_params)
    houses_by_bathrooms_data = dict_fetchall(cur)
    
    # Houses by Living Area
    houses_living_area_query = "SELECT living_area as name, COUNT(h_id) as count FROM house WHERE living_area IS NOT NULL"
    houses_living_area_params = []
    if selected_type:
        houses_living_area_query += " AND t_id = %s"
        houses_living_area_params.append(selected_type)
    if selected_project:
        houses_living_area_query += " AND p_id = %s"
        houses_living_area_params.append(selected_project)
    houses_living_area_query += " GROUP BY living_area ORDER BY living_area"
    cur.execute(houses_living_area_query, houses_living_area_params)
    houses_by_living_area_data = dict_fetchall(cur)
    
    # Calculate stats
    total_houses = len(houses)
    total_projects = len(set(h['p_id'] for h in houses if h.get('p_id')))
    total_types = len(set(h['t_id'] for h in houses if h.get('t_id')))
    
    # Get view count statistics
    total_views = 0
    most_viewed_houses = []
    views_by_type = {}
    views_trend = []
    
    # Assuming you have a 'views' table in your database with the following structure:
    # id, house_id, view_count, created_at
    views_query = "SELECT * FROM views WHERE 1=1"
    views_params = []
    if selected_type:
        views_query += " AND t_id = %s"
        views_params.append(selected_type)
    if selected_project:
        views_query += " AND p_id = %s"
        views_params.append(selected_project)
    cur.execute(views_query, views_params)
    views = dict_fetchall(cur)
    
    for view in views:
        total_views += view['view_count']
        if view['house_id'] not in most_viewed_houses:
            most_viewed_houses.append(view['house_id'])
        if view['t_id'] not in views_by_type:
            views_by_type[view['t_id']] = 0
        views_by_type[view['t_id']] += view['view_count']
        views_trend.append({'date': view['created_at'], 'views': view['view_count']})
    
    return jsonify({
        'success': True,
        'stats': {
            'total_houses': total_houses,
            'total_projects': total_projects,
            'total_types': total_types
        },
        'charts': {
            'houses_by_type': houses_by_type_data,
            'houses_by_project': houses_by_project_data,
            'houses_by_status': houses_by_status_data,
            'houses_by_bedrooms': houses_by_bedrooms_data,
            'houses_by_bathrooms': houses_by_bathrooms_data,
            'houses_by_living_area': houses_by_living_area_data
        },
        'view_stats': {
            'total_views': total_views,
            'most_viewed_houses': most_viewed_houses,
            'views_by_type': views_by_type,
            'views_trend': views_trend
        }
    })



# Debug routes
@app.route('/debug/check-session')
def debug_check_session():
    if 'admin_id' not in session:
        return "Not logged in"
    
    # Get database info for the current user
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT id, username, role FROM admins WHERE id = %s", (session.get('admin_id'),))
        db_user = cur.fetchone()
        
        return f"""
        <h2>Session Information</h2>
        <pre>
        Session Data: {dict(session)}
        
        Database Info:
        ID: {db_user[0] if db_user else 'Not found'}
        Username: {db_user[1] if db_user else 'N/A'}
        Role in DB: {db_user[2] if db_user else 'N/A'}
        
        Session Role: {session.get('admin_role')}
        Is Super Admin: {session.get('admin_role') == 'superadmin'}
        </pre>
        
        <p><a href="/debug/fix-session">Click here to fix session</a></p>
        <p><a href="/admin/users">Back to Admin Users</a></p>
        """
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cur.close()

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

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    """
    Renders the main reports dashboard page.
    
    This route serves the HTML template where the user can view statistics,
    charts, and generate PDF reports. It requires the user to be logged in
    as an administrator.
    """
    
    # Get projects and house types for filters
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    try:
        # Get all projects
        cur.execute("SELECT p_id as id, p_name as name FROM project ORDER BY p_name")
        projects = cur.fetchall()
        
        # Get all house types
        cur.execute("SELECT t_id as id, t_name as name FROM house_type ORDER BY t_name")
        house_types = cur.fetchall()
        
        # Get all house features
        cur.execute("SELECT f_id as id, f_name as name FROM house_features ORDER BY name")
        house_features = cur.fetchall()
        
        # Get selected filters from request args
        selected_type = request.args.get('type')
        selected_project = request.args.get('project')
        selected_feature = request.args.get('feature')
        
        return render_template('admin_reports.html', 
                             projects=projects, 
                             house_types=house_types,
                             house_features=house_features,
                             selected_type=selected_type,
                             selected_project=selected_project,
                             selected_feature=selected_feature)
    except Exception as e:
        print(f"Error fetching dropdown data: {str(e)}")
        # Still render the template even if there's an error
        return render_template('admin_reports.html', 
                             projects=[], 
                             house_types=[],
                             house_features=[])
    finally:
        cur.close()

@app.route('/admin/reports/pdf')
@login_required
@admin_required
def generate_pdf_report():
    """
    Generates a PDF report of house data based on applied filters.
    
    This function retrieves filtered data from the database, constructs an HTML
    table from the results, and then uses the xhtml22pdf library to convert
    the HTML content into a PDF document, which is sent as a response.
    """
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    try:
        # Get filter parameters from the request query string
        search_query = request.args.get('search', '')
        project_filter = request.args.get('project', '')
        type_filter = request.args.get('type', '')
        bedroom_filter = request.args.get('bedrooms', '')
        min_price = request.args.get('min_price', '')
        max_price = request.args.get('max_price', '')
        status_filter = request.args.get('house_status', '')

        # Build the WHERE clause and parameters for the SQL query
        where_conditions = []
        params = []

        if search_query:
            where_conditions.append("(h.h_title LIKE %s OR h.h_description LIKE %s OR p.p_name LIKE %s)")
            params.extend([f"%{search_query}%"] * 3)
        
        if project_filter:
            where_conditions.append("h.p_id = %s")
            params.append(project_filter)
        
        if type_filter:
            where_conditions.append("h.t_id = %s")
            params.append(type_filter)
        
        if bedroom_filter:
            if bedroom_filter.isdigit():
                where_conditions.append("h.bedrooms = %s")
                params.append(int(bedroom_filter))
        
        if min_price:
            where_conditions.append("h.price >= %s")
            params.append(min_price)
        
        if max_price:
            where_conditions.append("h.price <= %s")
            params.append(max_price)
            
        if status_filter:
            where_conditions.append("h.status = %s")
            params.append(status_filter)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get database connection
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get today's view count
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT COUNT(*) as today_views 
            FROM house_views 
            WHERE DATE(created_at) = CURDATE()
        """)
        result = cur.fetchone()
        today_views = result['today_views'] if result else 0
        
        # Get house data with filters
        query = f"""
            SELECT 
                h.h_id, h.h_title, h.h_description, h.price, h.bedrooms, h.bathrooms, h.living_area as area,
                p.p_name as project_name,
                ht.t_name as type_name,
                (SELECT COUNT(*) FROM house_views hv WHERE hv.house_id = h.h_id) as view_count
            FROM house h
            LEFT JOIN project p ON h.p_id = p.p_id
            LEFT JOIN house_type ht ON h.t_id = ht.t_id
            WHERE {where_clause}
            ORDER BY h.h_id
        """
        print(f"Executing query: {query}")
        print(f"With params: {params}")
        
        cur.execute(query, params)
        houses = cur.fetchall()
        cur.close()
        
        print(f"Found {len(houses)} houses in the database")
        if houses:
            print(f"Sample house data: {houses[0]}")

        # Generate table rows for the HTML
        rows_html = ""
        for house in houses:
            rows_html += f"""
                <tr>
                    <td>{house['h_id']}</td>
                    <td>{house['h_title']}</td>
                    <td>{house['project_name'] or '-'}</td>
                    <td>{house['type_name'] or '-'}</td>
                    <td>{house['bedrooms'] or '0'}</td>
                    <td>{house['bathrooms'] or '0'}</td>
                    <td>{house['area'] or '0'}</td>
                    <td class="text-right">{float(house['price'] or 0):,.2f}</td>
                </tr>
            """

        try:
            from reportlab.lib.pagesizes import A4, letter, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import mm, inch
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfbase import cidfonts
            from datetime import datetime
            import os
            
            try:
                # Register Thai font with proper encoding
                font_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'fonts')
                regular_font_path = os.path.join(font_folder, 'NotoSansThai-Regular.ttf')
                bold_font_path = os.path.join(font_folder, 'NotoSansThai-Bold.ttf')
                
                # Register the fonts with reportlab
                pdfmetrics.registerFont(TTFont('NotoSansThai', regular_font_path))
                pdfmetrics.registerFont(TTFont('NotoSansThai-Bold', bold_font_path))
                
                # Get default styles and create custom ones
                styles = getSampleStyleSheet()
                
                # Create custom style for Thai text
                thai_style = ParagraphStyle(
                    'ThaiStyle',
                    parent=styles['Normal'],
                    fontName='NotoSansThai',
                    fontSize=10,
                    leading=12,
                    wordWrap='CJK',
                    alignment=TA_JUSTIFY
                )
                
                # Create custom style for Thai headings (smaller and less bold)
                thai_heading_style = ParagraphStyle(
                    'ThaiHeadingStyle',
                    fontName='NotoSansThai',  # Using regular weight instead of bold
                    fontSize=12,              # Reduced from 16
                    leading=14,               # Reduced from 20
                    spaceAfter=8,             # Reduced from 12
                    alignment=TA_CENTER,
                    textColor=colors.white  # White text for better visibility
                )
                
                # Create custom style for table cells (lighter and more compact)
                thai_table_style = TableStyle([
                    # All cells
                    ('FONTNAME', (0, 0), (-1, -1), 'NotoSansThai'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),  # Smaller font size
                    ('LEADING', (0, 0), (-1, -1), 9),   # Tighter line spacing
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    
                    # Header row
                    ('FONTNAME', (0, 0), (-1, 0), 'NotoSansThai'),  # Not bold
                    ('FONTSIZE', (0, 0), (-1, 0), 9),  # Slightly larger for headers
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#333333')),  # Dark gray
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),  # Lighter gray
                    
                    # Grid and borders
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e9ecef')),  # Lighter grid
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),  # Lighter border
                    
                    # Cell padding and styling
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),  # Less vertical padding
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ])
                
            except Exception as e:
                print(f"Error setting up PDF styles: {e}")
                # Fallback to default styles if there's an error
                thai_style = styles['Normal']
                thai_heading_style = styles['Heading1']
                thai_table_style = TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
                ])
            
            print("Starting PDF generation...")
            
            # Create a buffer to receive PDF data
            buffer = io.BytesIO()
            
            # Create PDF with landscape orientation and proper margins
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), 
                                 rightMargin=20, leftMargin=20, 
                                 topMargin=40, bottomMargin=20)
            elements = []
                    
            # Add today's views
            views_text = f"<b>จำนวนการเข้าชมในวันนี้:</b> {today_views} ครั้ง"
            views_para = Paragraph(views_text, thai_style)
            elements.append(views_para)
            elements.append(Spacer(1, 10))
            
            # Add main title with Thai font
            main_title_style = ParagraphStyle(
                'MainTitleStyle',
                parent=styles['Title'],
                fontName='NotoSansThai-Bold',
                fontSize=24,
                leading=28,
                alignment=TA_CENTER,
                spaceAfter=10,
                textColor=colors.HexColor('#2463EB')  # Dark blue color
            )
            
            # Add subtitle with date
            subtitle_style = ParagraphStyle(
                'SubtitleStyle',
                parent=styles['Normal'],
                fontName='NotoSansThai',
                fontSize=14,
                leading=16,
                alignment=TA_CENTER,
                spaceAfter=20,
                textColor=colors.HexColor('#4B5563')  # Gray color
            )
            
            # Add main title and subtitle
            elements.append(Paragraph('BAANTANG DEVELOPMENT REPORT', main_title_style))
            elements.append(Paragraph(f'Generated on: {datetime.now().strftime("%d %B %Y, %H:%M")}', subtitle_style))
            elements.append(Spacer(1, 20))
            
            # Add report title with Thai font
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Title'],
                fontName='NotoSansThai-Bold',
                fontSize=18,
                leading=22,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            
            # Date style for the report generation timestamp
            date_style = ParagraphStyle(
                'DateStyle',
                fontName='NotoSansThai',
                fontSize=10,
                alignment=TA_RIGHT,
                textColor=colors.HexColor('#666666')
            )
            
            
            
            # Prepare table data with Thai headers and proper text wrapping
            table_data = [
                [
                    Paragraph('ID', thai_heading_style),
                    Paragraph('ชื่อบ้าน', thai_heading_style),
                    Paragraph('โครงการ', thai_heading_style),
                    Paragraph('ประเภท', thai_heading_style),
                    Paragraph('ห้องนอน', thai_heading_style),
                    Paragraph('ห้องน้ำ', thai_heading_style),
                    Paragraph('พื้นที่ (ตร.ม.)', thai_heading_style),
                    Paragraph('ราคา (บาท)', thai_heading_style)
                ]
            ]
            
            # Add house data with proper text wrapping
            for house in houses:
                table_data.append([
                    Paragraph(str(house['h_id']), thai_style),
                    Paragraph(house['h_title'], thai_style),
                    Paragraph(house.get('project_name', '-'), thai_style),
                    Paragraph(house.get('type_name', '-'), thai_style),
                    Paragraph(str(house.get('bedrooms', '0')), thai_style),
                    Paragraph(str(house.get('bathrooms', '0')), thai_style),
                    Paragraph(str(house.get('area', '0')), thai_style),
                    Paragraph(f"{float(house.get('price', 0)):,.2f}", thai_style),
                    Paragraph(str(house.get('view_count', '0')), thai_style)  # Add view count column
                ])
            
            # Add view count column header
            table_data[0].append(Paragraph('จำนวนการเข้าชม', thai_heading_style))
            
            # Sort houses by view count in descending order
            if len(table_data) > 1:  # Check if there's data beyond the header
                table_data[1:] = sorted(
                    table_data[1:], 
                    key=lambda x: int(x[-1].text) if x[-1].text.isdigit() else 0, 
                    reverse=True
                )
            
            # Set column widths to ensure text fits on one line
            col_widths = [
                0.5*inch,   # ID (0.5")
                2.2*inch,   # House Name (slightly narrower)
                1.5*inch,   # Project (narrower)
                0.9*inch,   # Type (slightly narrower)
                0.9*inch,   # Bedrooms
                0.9*inch,   # Bathrooms
                0.8*inch,   # Area
                1.2*inch,   # Price
                1.3*inch    # View Count
            ]
            
            # Create the table with adjusted column widths
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Define table style with Thai fonts and proper text wrapping
            table_style = TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2463EB')),  # Dark blue header
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # White text for header row only
                ('FONTNAME', (0, 0), (-1, 0), 'NotoSansThai-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), 'NotoSansThai'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEADING', (0, 0), (-1, -1), 12),  # Line height
                
                # Column alignments
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # ID column centered
                ('ALIGN', (4, 1), (5, -1), 'CENTER'),  # Bed/Bath columns centered
                ('ALIGN', (6, 1), (8, -1), 'RIGHT'),   # Area/Price/View count right-aligned
                
                # Grid and borders
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1E40AF')),
                
                # Text color for data rows
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1F2937')),
                
                # Cell padding
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                
                # Alternating row colors (zebra striping)
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
            ])
            
            # Apply the table style
            table.setStyle(table_style)
            elements.append(table)
            
            # Add page number footer with Thai font
            def add_page_number(canvas, doc):
                canvas.saveState()
                # Set Thai font for footer
                canvas.setFont('NotoSansThai', 8)
                
                # Get current page number and total pages
                page_num = canvas.getPageNumber()
                
                # Create footer text with Thai date
                footer_date = f"สร้างเมื่อ: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                footer_page = f"หน้า {page_num}"
                
                # Draw footer text
                canvas.drawString(doc.leftMargin, 20, footer_date)
                canvas.drawRightString(doc.width + doc.rightMargin - 20, 20, footer_page)
                
                # Add a thin line above footer
                canvas.setStrokeColor(colors.HexColor('#E5E7EB'))
                canvas.line(doc.leftMargin, 30, doc.width + doc.rightMargin, 30)
                
                canvas.restoreState()
            
            # Build the PDF with page numbers
            doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
            
            # Get the value of the BytesIO buffer
            pdf = buffer.getvalue()
            buffer.close()
            
            if not pdf:
                return "Error generating PDF: Empty content", 500
            
            # Create response with proper headers
            response = make_response(pdf)
            response.mimetype = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=house_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            response.headers['Content-Length'] = len(pdf)
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
            return response
            
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Error generating PDF: {str(e)}'}), 500

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to generate PDF'}), 500


@app.route('/admin/reports/view-stats')
def view_statistics():
    """
    Retrieves view statistics for the admin reports page.
    Returns data for most viewed houses, views by type, and view trends.
    """
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        cur = mysql.connection.cursor()
        
        # Get total views across all houses
        cur.execute("""
            SELECT COALESCE(SUM(view_count), 0) as total_views
            FROM house
        """)
        total_views = cur.fetchone()[0]
        
        # Get today's views
        cur.execute("""
            SELECT COUNT(*) 
            FROM house_views 
            WHERE DATE(created_at) = CURDATE()
        """)
        todays_views = cur.fetchone()[0]
        
        # Get most viewed houses (top 5)
        cur.execute("""
            SELECT h.h_id, h.h_title, h.view_count, p.p_name as project_name
            FROM house h
            LEFT JOIN project p ON h.p_id = p.p_id
            WHERE h.view_count > 0
            ORDER BY h.view_count DESC
            LIMIT 5
        """)
        most_viewed_houses = [
            {'id': row[0], 'title': row[1], 'views': row[2], 'project': row[3]}
            for row in cur.fetchall()
        ]
        
        # Get views by house type
        cur.execute("""
            SELECT 
                ht.t_name as type_name,
                COALESCE(SUM(h.view_count), 0) as total_views
            FROM house_type ht
            LEFT JOIN house h ON ht.t_id = h.t_id
            GROUP BY ht.t_id, ht.t_name
            ORDER BY total_views DESC
        """)
        views_by_type = [
            {'type': row[0], 'views': int(row[1] or 0)}
            for row in cur.fetchall()
        ]
        
        # Get views trend (last 30 days)
        cur.execute("""
            SELECT 
                DATE(created_at) as view_date,
                COUNT(*) as view_count
            FROM house_views
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY DATE(created_at)
            ORDER BY view_date
        """)
        views_trend = [
            {'date': row[0].strftime('%Y-%m-%d'), 'views': row[1]}
            for row in cur.fetchall()
        ]
        
        return jsonify({
            'success': True,
            'total_views': total_views,
            'most_viewed_houses': most_viewed_houses,
            'views_by_type': views_by_type,
            'views_trend': views_trend
        })
        
    except Exception as e:
        print(f"Error getting view statistics: {str(e)}")
        return jsonify({'error': 'Failed to get view statistics'}), 500
    finally:
        cur.close()

@app.route('/admin/view-stats')
@login_required
@admin_required
def admin_view_stats():
    """
    Renders the view statistics page.
    
    This route serves the HTML template where the user can view detailed
    statistics about house views, including trends and most viewed houses.
    It requires the user to be logged in as an administrator.
    """
    cursor = None
    try:
        # Debug: Print session info
        print("\n=== Session Debug ===")
        print(f"Session ID: {session.sid if 'sid' in dir(session) else 'N/A'}")
        print(f"Session data: {dict(session)}")
        print(f"Admin logged in: {'admin_id' in session}")
        
        # Ensure admin_username is set in session
        if 'admin_username' not in session and current_user.is_authenticated:
            session['admin_username'] = current_user.username
        
        # Get filter parameters
        days = request.args.get('days', '30')
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        # Get view statistics data
        stats_data = view_statistics()
        
        # Get database connection and cursor
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get house types for filter
        cursor.execute("SELECT * FROM house_type ORDER BY t_name")
        house_types = cursor.fetchall()
        
        # Get top 5 most viewed houses
        cursor.execute("""
            SELECT h.h_id, h.h_title, h.price, h.bedrooms, h.bathrooms, h.living_area,
                   h.parking_space, h.no_of_floors, h.status, h.view_count,
                   ht.t_name as type_name, p.p_name as project_name,
                   COUNT(v.id) as total_views
            FROM house h
            LEFT JOIN house_views v ON h.h_id = v.house_id
            LEFT JOIN house_type ht ON h.t_id = ht.t_id
            LEFT JOIN project p ON h.p_id = p.p_id
            GROUP BY h.h_id, h.h_title, h.price, h.bedrooms, h.bathrooms, h.living_area,
                     h.parking_space, h.no_of_floors, h.status, h.view_count,
                     ht.t_name, p.p_name
            ORDER BY total_views DESC
            LIMIT 5
        """)
        most_viewed_houses = cursor.fetchall()
        
        # Get views by house type
        cursor.execute("""
            SELECT 
                ht.t_id as id, 
                ht.t_name as name, 
                COUNT(DISTINCT v.id) as view_count
            FROM house_type ht
            LEFT JOIN house h ON ht.t_id = h.t_id
            LEFT JOIN house_views v ON h.h_id = v.house_id
            GROUP BY ht.t_id, ht.t_name
            ORDER BY view_count DESC
        """)
        views_by_type = cursor.fetchall()
        
        # Get view trends (last X days based on the filter)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate a series of dates for the selected period
        date_series = []
        current_date = start_date
        while current_date <= end_date:
            date_series.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # Get view counts for each day in the period
        cursor.execute("""
            SELECT 
                DATE(v.created_at) as view_date, 
                COUNT(DISTINCT v.id) as view_count
            FROM house_views v
            WHERE v.created_at BETWEEN %s AND %s
            GROUP BY DATE(v.created_at)
            ORDER BY view_date
        """, (start_date, end_date))
        
        view_trends = cursor.fetchall()
        
        # Create a dictionary of date: count for easy lookup
        view_counts_dict = {row['view_date'].strftime('%Y-%m-%d'): row['view_count'] for row in view_trends}
        
        # Ensure we have data for all dates in the range
        view_dates = date_series
        view_counts = [int(view_counts_dict.get(date, 0)) for date in date_series]
        
        # Ensure all numeric fields are properly converted to int
        for house in most_viewed_houses:
            for key in ['view_count', 'h_id', 'price', 'bedrooms', 'bathrooms', 'living_area', 'parking_space', 'no_of_floors']:
                if key in house and house[key] is not None:
                    try:
                        house[key] = int(float(house[key]))
                    except (ValueError, TypeError):
                        house[key] = 0
        
        # Convert views_by_type to a list of dicts with proper int conversion
        views_by_type_list = []
        for row in views_by_type:
            try:
                view_count = int(float(row['view_count'])) if row['view_count'] is not None else 0
                views_by_type_list.append({
                    'id': int(float(row['id'])),
                    'name': str(row['name']),
                    'view_count': view_count
                })
            except (ValueError, TypeError, KeyError) as e:
                print(f"Error processing views_by_type row: {row}, error: {str(e)}")
        
        # Prepare data for template with proper JSON serialization
        template_data = {
            'title': 'สถิติการเข้าชม',
            'view_dates': view_dates,
            'view_counts': view_counts,
            'most_viewed_houses': most_viewed_houses,
            'views_by_type': views_by_type_list,
            'selected_days': int(days),
            'house_types': house_types,
            'stats_data': stats_data
        }
        
        # Debug: Print data being sent to template
        print("\n=== Template Data ===")
        print(f"view_dates type: {type(view_dates[0]) if view_dates else 'empty'}")
        print(f"view_counts type: {type(view_counts[0]) if view_counts else 'empty'}")
        print(f"views_by_type sample: {views_by_type_list[:1] if views_by_type_list else 'empty'}")
        print(f"most_viewed_houses sample: {most_viewed_houses[0] if most_viewed_houses else 'empty'}")
        
        return render_template('admin_view_stats.html', **template_data)
        
    except Exception as e:
        print(f"Error in admin_view_stats: {str(e)}")
        flash('เกิดข้อผิดพลาดในการโหลดหน้าสถิติการเข้าชม', 'error')
        return redirect(url_for('admin_dashboard'))
        
    finally:
        # Ensure cursor is always closed
        if cursor is not None:
            try:
                cursor.close()
            except:
                pass
    
    return render_template('admin_view_stats.html', **template_data)

@app.route('/admin/reports/chart-data')
def reports_chart_data():
    """
    Retrieves filtered statistical and chart data for the admin reports page.

    This function accepts various filter parameters from the request, applies them to
    several SQL queries to calculate total stats and aggregate data for charts,
    and returns the results as a JSON object.
    """
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get filter parameters from the request arguments
        search_query = request.args.get('search', '')
        
        # Get database connection
        cur = mysql.connection.cursor()
        
        project_filter = request.args.get('project', '')
        type_filter = request.args.get('type', '')
        feature_filter = request.args.get('feature', '')
        min_price = request.args.get('min_price', '')
        max_price = request.args.get('max_price', '')
        status_filter = request.args.get('house_status', '')

        # Build the base WHERE clause and parameters for all queries
        where_conditions = []
        params = []
        join_conditions = []

        if search_query:
            where_conditions.append("(h.h_title LIKE %s OR h.h_description LIKE %s OR p.p_name LIKE %s)")
            params.extend([f"%{search_query}%"] * 3)
            join_conditions.append("LEFT JOIN project p ON h.p_id = p.p_id")
        
        if project_filter:
            where_conditions.append("h.p_id = %s")
            params.append(project_filter)
        
        if type_filter:
            where_conditions.append("h.t_id = %s")
            params.append(type_filter)
            
        if feature_filter:
            where_conditions.append("h.f_id = %s")
            params.append(feature_filter)
        
        if min_price:
            where_conditions.append("h.price >= %s")
            params.append(min_price)
        
        if max_price:
            where_conditions.append("h.price <= %s")
            params.append(max_price)
            
        if status_filter:
            where_conditions.append("h.status = %s")
            params.append(status_filter)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        join_clause = " ".join(join_conditions) if join_conditions else ""
        
        # Get database connection
        cur = mysql.connection.cursor()
        
        # Get total views across all houses
        cur.execute(f"""
            SELECT COALESCE(SUM(view_count), 0) as total_views
            FROM house h
            {join_clause}
            WHERE {where_clause}
        """, tuple(params))
        total_views = cur.fetchone()[0]
        
        # Get most viewed houses (top 5) with filters
        most_viewed_query = f"""
            SELECT h.h_id, h.h_title, h.view_count
            FROM house h
            {join_clause}
        """
            
        most_viewed_query += f"""
            WHERE {where_clause} AND h.view_count > 0
            GROUP BY h.h_id, h.h_title, h.view_count
            ORDER BY h.view_count DESC
            LIMIT 5
        """
        
        cur.execute(most_viewed_query, tuple(params))
        most_viewed_houses = [
            {'id': row[0], 'title': row[1], 'views': row[2]}
            for row in cur.fetchall()
        ]
        
        # Get views by house type with filters
        views_by_type_query = f"""
            SELECT 
                COALESCE(ht.t_name, 'ไม่มีประเภท') as type_name,
                COUNT(DISTINCT h.h_id) as house_count
            FROM house h
            LEFT JOIN house_type ht ON h.t_id = ht.t_id
            LEFT JOIN project p ON h.p_id = p.p_id
        """
            
        views_by_type_query += f"""
            WHERE {where_clause}
            GROUP BY ht.t_id, ht.t_name
            ORDER BY house_count DESC
        """
        
        cur.execute(views_by_type_query, tuple(params))
        views_by_type = [
            {'type': row[0], 'views': int(row[1] or 0)}
            for row in cur.fetchall()
        ]
        
        # Get views trend (last 30 days) with filters
        views_trend_query = f"""
            SELECT 
                DATE(hv.created_at) as view_date,
                COUNT(DISTINCT hv.id) as view_count
            FROM house_views hv
            JOIN house h ON hv.house_id = h.h_id
            {join_clause}
        """
            
        views_trend_query += f"""
            WHERE hv.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            AND {where_clause}
            GROUP BY DATE(hv.created_at)
            ORDER BY view_date
        """
        
        cur.execute(views_trend_query, tuple(params))
        views_trend = [
            {'date': row[0].strftime('%Y-%m-%d'), 'views': row[1]}
            for row in cur.fetchall()
        ]

        # Initialize cursor and data dictionaries
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        stats = {}
        charts = {}
        
        # Debug: Print the where_clause and params
        print("Where clause:", where_clause)
        print("Params:", params)
        
        # --- Fetch Statistics ---
        
        # Total houses
        query_houses = f"""
            SELECT COUNT(*) as total_houses 
            FROM house h
            LEFT JOIN project p ON h.p_id = p.p_id
            WHERE {where_clause}
        """
        cur.execute(query_houses, tuple(params))
        stats['total_houses'] = cur.fetchone()['total_houses']

        # Total projects (that have houses matching the filter)
        query_projects = f"""
            SELECT COUNT(DISTINCT p.p_id) as total_projects 
            FROM house h
            LEFT JOIN project p ON h.p_id = p.p_id
            WHERE {where_clause}
        """
        cur.execute(query_projects, tuple(params))
        stats['total_projects'] = cur.fetchone()['total_projects']

        # Total house types (that have houses matching the filter)
        query_types = f"""
            SELECT COUNT(DISTINCT h.t_id) as total_types 
            FROM house h
            LEFT JOIN house_type ht ON h.t_id = ht.t_id
            LEFT JOIN project p ON h.p_id = p.p_id
            WHERE {where_clause}
        """
        cur.execute(query_types, tuple(params))
        stats['total_types'] = cur.fetchone()['total_types']

        # --- Fetch Chart Data ---
        
        # Houses by type - Modified to ensure we get all houses even if type is null
        query_houses_by_type = f"""
            SELECT 
                COALESCE(ht.t_id, 0) as id, 
                COALESCE(ht.t_name, 'ไม่มีประเภท') as name, 
                COUNT(h.h_id) as house_count
            FROM house h
            LEFT JOIN house_type ht ON h.t_id = ht.t_id
            LEFT JOIN project p ON h.p_id = p.p_id
            WHERE {where_clause}
            GROUP BY 
                CASE WHEN ht.t_id IS NULL THEN 0 ELSE ht.t_id END,
                CASE WHEN ht.t_name IS NULL THEN 'ไม่มีประเภท' ELSE ht.t_name END
            ORDER BY house_count DESC
        """
        cur.execute(query_houses_by_type, tuple(params))
        charts['housesByType'] = cur.fetchall()

        # Houses by project - Modified to ensure we get all houses even if project is null
        query_houses_by_project = f"""
            SELECT 
                COALESCE(p.p_id, 0) as id, 
                COALESCE(p.p_name, 'ไม่มีโครงการ') as name, 
                COUNT(h.h_id) as house_count
            FROM house h
            LEFT JOIN project p ON h.p_id = p.p_id
            LEFT JOIN house_type ht ON h.t_id = ht.t_id
            WHERE {where_clause}
            GROUP BY 
                CASE WHEN p.p_id IS NULL THEN 0 ELSE p.p_id END,
                CASE WHEN p.p_name IS NULL THEN 'ไม่มีโครงการ' ELSE p.p_name END
            ORDER BY house_count DESC
        """
        
        # Debug: Print the queries
        print("Houses by type query:", query_houses_by_type)
        print("Houses by project query:", query_houses_by_project)
        cur.execute(query_houses_by_project, tuple(params))
        charts['housesByProject'] = cur.fetchall()

        # Houses by status
        # Houses by status
        query_houses_by_status = f"""
            SELECT 
                CASE 
                    WHEN h.status = 'Available' THEN 'ว่าง' 
                    WHEN h.status = 'Reserved' THEN 'จองแล้ว' 
                    WHEN h.status = 'Sold' THEN 'ขายแล้ว' 
                    ELSE COALESCE(h.status, 'ไม่ระบุ')
                END as status,
                COUNT(*) as count
            FROM house h
            LEFT JOIN project p ON h.p_id = p.p_id
            LEFT JOIN house_type ht ON h.t_id = ht.t_id
            WHERE {where_clause}
            GROUP BY 
                CASE 
                    WHEN h.status = 'Available' THEN 'ว่าง' 
                    WHEN h.status = 'Reserved' THEN 'จองแล้ว' 
                    WHEN h.status = 'Sold' THEN 'ขายแล้ว' 
                    ELSE COALESCE(h.status, 'ไม่ระบุ')
                END
            ORDER BY count DESC
        """
        cur.execute(query_houses_by_status, tuple(params))
        charts['housesByStatus'] = cur.fetchall()

        # Houses by bedrooms
        query_houses_by_bedrooms = f"""
            SELECT 
                COALESCE(bedrooms, 0) as bedrooms,
                COUNT(*) as count
            FROM house h
            LEFT JOIN project p ON h.p_id = p.p_id
            LEFT JOIN house_type ht ON h.t_id = ht.t_id
            WHERE {where_clause}
            GROUP BY COALESCE(bedrooms, 0)
            ORDER BY COALESCE(bedrooms, 0)
        """
        cur.execute(query_houses_by_bedrooms, tuple(params))
        charts['housesByBedrooms'] = cur.fetchall()

        # Houses by bathrooms
        query_houses_by_bathrooms = f"""
            SELECT 
                COALESCE(bathrooms, 0) as bathrooms,
                COUNT(*) as count
            FROM house h
            LEFT JOIN project p ON h.p_id = p.p_id
            LEFT JOIN house_type ht ON h.t_id = ht.t_id
            WHERE {where_clause}
            GROUP BY COALESCE(bathrooms, 0)
            ORDER BY COALESCE(bathrooms, 0)
        """
        cur.execute(query_houses_by_bathrooms, tuple(params))
        charts['housesByBathrooms'] = cur.fetchall()

        # Houses by living area (grouped in ranges)
        query_houses_by_area = f"""
            SELECT 
                CASE
                    WHEN living_area IS NULL THEN 'ไม่ระบุ'
                    WHEN living_area < 50 THEN '0-50 ตร.ม.'
                    WHEN living_area BETWEEN 50 AND 99 THEN '50-99 ตร.ม.'
                    WHEN living_area BETWEEN 100 AND 149 THEN '100-149 ตร.ม.'
                    WHEN living_area BETWEEN 150 AND 199 THEN '150-199 ตร.ม.'
                    WHEN living_area >= 200 THEN '200+ ตร.ม.'
                    ELSE 'ไม่ระบุ'
                END as area_range,
                COUNT(*) as count
            FROM house h
            LEFT JOIN project p ON h.p_id = p.p_id
            LEFT JOIN house_type ht ON h.t_id = ht.t_id
            WHERE {where_clause}
            GROUP BY 
                CASE
                    WHEN living_area IS NULL THEN 'ไม่ระบุ'
                    WHEN living_area < 50 THEN '0-50 ตร.ม.'
                    WHEN living_area BETWEEN 50 AND 99 THEN '50-99 ตร.ม.'
                    WHEN living_area BETWEEN 100 AND 149 THEN '100-149 ตร.ม.'
                    WHEN living_area BETWEEN 150 AND 199 THEN '150-199 ตร.ม.'
                    WHEN living_area >= 200 THEN '200+ ตร.ม.'
                    ELSE 'ไม่ระบุ'
                END
            ORDER BY 
                CASE 
                    WHEN CASE
                        WHEN living_area IS NULL THEN 'ไม่ระบุ'
                        WHEN living_area < 50 THEN '0-50 ตร.ม.'
                        WHEN living_area BETWEEN 50 AND 99 THEN '50-99 ตร.ม.'
                        WHEN living_area BETWEEN 100 AND 149 THEN '100-149 ตร.ม.'
                        WHEN living_area BETWEEN 150 AND 199 THEN '150-199 ตร.ม.'
                        WHEN living_area >= 200 THEN '200+ ตร.ม.'
                        ELSE 'ไม่ระบุ'
                    END = 'ไม่ระบุ' THEN 0
                    WHEN living_area < 50 THEN 1
                    WHEN living_area BETWEEN 50 AND 99 THEN 2
                    WHEN living_area BETWEEN 100 AND 149 THEN 3
                    WHEN living_area BETWEEN 150 AND 199 THEN 4
                    WHEN living_area >= 200 THEN 5
                    ELSE 6
                END
        """
        cur.execute(query_houses_by_area, tuple(params))
        charts['housesByLivingArea'] = cur.fetchall()

        # Debug: Print number of params and placeholders
        print(f"Executing queries with {len(params)} parameters")
        
        # Execute houses by type query
        cur.execute(query_houses_by_type, tuple(params))
        houses_by_type = cur.fetchall()
        print(f"Houses by type results: {houses_by_type}")
        
        # Execute houses by project query
        cur.execute(query_houses_by_project, tuple(params))
        houses_by_project = cur.fetchall()
        print(f"Houses by project results: {houses_by_project}")
        
        # Execute houses by status query
        cur.execute(query_houses_by_status, tuple(params))
        houses_by_status = cur.fetchall()
        print(f"Houses by status results: {houses_by_status}")
        
        # Execute houses by bedrooms query
        cur.execute(query_houses_by_bedrooms, tuple(params))
        houses_by_bedrooms = cur.fetchall()
        
        # Execute houses by bathrooms query
        cur.execute(query_houses_by_bathrooms, tuple(params))
        houses_by_bathrooms = cur.fetchall()
        
        # Execute houses by living area query
        cur.execute(query_houses_by_area, tuple(params))
        houses_by_living_area = cur.fetchall()
        
        # Prepare the response with the data we've already fetched
        response_data = {
            'stats': stats,
            'charts': {
                'housesByType': houses_by_type if houses_by_type else [],
                'housesByProject': houses_by_project if houses_by_project else [],
                'housesByStatus': houses_by_status if houses_by_status else [],
                'housesByBedrooms': [{'bedrooms': str(row['bedrooms']), 'count': row['count']} for row in houses_by_bedrooms] if houses_by_bedrooms else [],
                'housesByBathrooms': [{'bathrooms': str(row['bathrooms']), 'count': row['count']} for row in houses_by_bathrooms] if houses_by_bathrooms else [],
                'housesByLivingArea': houses_by_living_area if houses_by_living_area else []
            }
        }
        
        print("Final response data:", json.dumps(response_data, default=str))
        return jsonify(response_data)

    except Exception as e:
        print(f"Error executing queries: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

    finally:
        if 'cur' in locals() and cur:
            cur.close()

@app.route('/create_house_views_table')
def create_house_views_table():
    try:
        cur = mysql.connection.cursor()
        # Create house_views table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS house_views (
            id INT AUTO_INCREMENT PRIMARY KEY,
            house_id INT NOT NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (house_id) REFERENCES houses(h_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        # Create indexes
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_house_views_house_id ON house_views(house_id);
        CREATE INDEX IF NOT EXISTS idx_house_views_created_at ON house_views(created_at);
        """)
        
        mysql.connection.commit()
        cur.close()
        return "house_views table created successfully!"
    except Exception as e:
        return f"Error creating house_views table: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))