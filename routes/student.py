from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection, execute_query
from functools import wraps

student_bp = Blueprint('student', __name__, url_prefix='/student')

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'student':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@student_bp.route('/profile')
@student_required
def profile():
    conn = None
    try:
        conn = get_db_connection()
        student = execute_query(conn, """
            SELECT u.*, s.*, uni.name as university_name
            FROM user u
            JOIN student s ON s.student_id = u.user_id
            LEFT JOIN university uni ON uni.university_id = s.university_id
            WHERE u.user_id = %s
        """, (session['user_id'],), fetchone=True)
        universities = execute_query(conn, "SELECT * FROM university ORDER BY name", fetch=True)
        return render_template('student/profile.html', student=student, universities=universities)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('student/profile.html', student=None, universities=[])
    finally:
        if conn: conn.close()

@student_bp.route('/profile/update', methods=['POST'])
@student_required
def update_profile():
    conn = None
    try:
        conn = get_db_connection()
        f = request.form
        execute_query(conn, """
            UPDATE user SET first_name=%s, last_name=%s, phone=%s, address=%s WHERE user_id=%s
        """, (f.get('first_name'), f.get('last_name'), f.get('phone'), f.get('address'), session['user_id']))
        execute_query(conn, """
            UPDATE student SET university_id=%s, major=%s, student_status=%s, year_of_study=%s, date_of_birth=%s
            WHERE student_id=%s
        """, (f.get('university_id') or None, f.get('major'), f.get('student_status'),
              f.get('year_of_study') or None, f.get('date_of_birth') or None, session['user_id']))
        conn.commit()
        session['name'] = f"{f.get('first_name')} {f.get('last_name')}"
        flash('Profile updated.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    finally:
        if conn: conn.close()
    return redirect(url_for('student.profile'))
