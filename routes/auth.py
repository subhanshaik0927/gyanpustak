from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection, execute_query
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'student':
            return redirect(url_for('books.browse'))
        elif role == 'support_staff':
            return redirect(url_for('support.dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'super_admin':
            return redirect(url_for('superadmin.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('auth.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        conn = None
        try:
            conn = get_db_connection()
            user = execute_query(conn, "SELECT * FROM user WHERE email = %s", (email,), fetchone=True)
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['user_id']
                session['role'] = user['role']
                session['name'] = f"{user['first_name']} {user['last_name']}"
                session['email'] = user['email']
                flash('Welcome back!', 'success')
                return redirect(url_for('auth.index'))
            else:
                flash('Invalid email or password.', 'danger')
        except Exception as e:
            flash(f'Login error: {e}', 'danger')
        finally:
            if conn:
                conn.close()
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('auth.index'))
    conn = None
    if request.method == 'POST':
        f = request.form
        email = f.get('email', '').strip()
        password = f.get('password', '')
        first_name = f.get('first_name', '').strip()
        last_name = f.get('last_name', '').strip()
        phone = f.get('phone', '').strip()
        address = f.get('address', '').strip()
        university_id = f.get('university_id') or None
        major = f.get('major', '').strip()
        student_status = f.get('student_status', 'undergraduate')
        year_of_study = f.get('year_of_study') or None
        dob = f.get('date_of_birth') or None
        try:
            conn = get_db_connection()
            existing = execute_query(conn, "SELECT user_id FROM user WHERE email=%s", (email,), fetchone=True)
            if existing:
                flash('Email already registered.', 'danger')
            else:
                pw_hash = generate_password_hash(password)
                uid = execute_query(conn,
                    "INSERT INTO user (email,password_hash,first_name,last_name,phone,address,role) VALUES (%s,%s,%s,%s,%s,%s,'student')",
                    (email, pw_hash, first_name, last_name, phone, address))
                execute_query(conn,
                    "INSERT INTO student (student_id,university_id,major,student_status,year_of_study,date_of_birth) VALUES (%s,%s,%s,%s,%s,%s)",
                    (uid, university_id, major, student_status, year_of_study, dob))
                execute_query(conn, "INSERT INTO cart (student_id) VALUES (%s)", (uid,))
                conn.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'Registration error: {e}', 'danger')
        finally:
            if conn:
                conn.close()
    conn2 = None
    universities = []
    try:
        conn2 = get_db_connection()
        universities = execute_query(conn2, "SELECT university_id, name FROM university ORDER BY name", fetch=True)
    except Exception:
        pass
    finally:
        if conn2:
            conn2.close()
    return render_template('auth/register.html', universities=universities)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
