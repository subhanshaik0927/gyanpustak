from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection, execute_query
from werkzeug.security import generate_password_hash
from functools import wraps

superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')

def superadmin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'super_admin':
            flash('Super admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@superadmin_bp.route('/dashboard')
@superadmin_required
def dashboard():
    conn = None
    try:
        conn = get_db_connection()
        employees = execute_query(conn, """
            SELECT u.*, e.emp_number, e.salary, e.gender
            FROM user u JOIN employee e ON e.employee_id = u.user_id
            WHERE u.role IN ('admin','support_staff')
            ORDER BY u.role, u.first_name
        """, fetch=True)
        return render_template('superadmin/dashboard.html', employees=employees)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('superadmin/dashboard.html', employees=[])
    finally:
        if conn: conn.close()

@superadmin_bp.route('/add-employee', methods=['GET', 'POST'])
@superadmin_required
def add_employee():
    if request.method == 'POST':
        f = request.form
        email = f.get('email', '').strip()
        password = f.get('password', '')
        first_name = f.get('first_name', '').strip()
        last_name = f.get('last_name', '').strip()
        phone = f.get('phone', '').strip()
        address = f.get('address', '').strip()
        role = f.get('role', 'support_staff')
        emp_number = f.get('emp_number', '').strip()
        gender = f.get('gender', 'M')
        salary = f.get('salary', 0)
        aadhaar = f.get('aadhaar', '').strip()
        if role not in ('admin', 'support_staff'):
            flash('Invalid role.', 'danger')
            return redirect(url_for('superadmin.add_employee'))
        conn = None
        try:
            conn = get_db_connection()
            existing = execute_query(conn, "SELECT user_id FROM user WHERE email=%s", (email,), fetchone=True)
            if existing:
                flash('Email already exists.', 'danger')
            else:
                pw_hash = generate_password_hash(password)
                uid = execute_query(conn, """
                    INSERT INTO user (email,password_hash,first_name,last_name,phone,address,role)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (email, pw_hash, first_name, last_name, phone, address, role))
                execute_query(conn, """
                    INSERT INTO employee (employee_id,emp_number,gender,salary,aadhaar)
                    VALUES (%s,%s,%s,%s,%s)
                """, (uid, emp_number, gender, salary, aadhaar))
                if role == 'admin':
                    execute_query(conn, "INSERT INTO admin (admin_id) VALUES (%s)", (uid,))
                else:
                    execute_query(conn, "INSERT INTO support_staff (staff_id) VALUES (%s)", (uid,))
                conn.commit()
                flash(f'Employee ({role}) added successfully!', 'success')
                return redirect(url_for('superadmin.dashboard'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
        finally:
            if conn: conn.close()
    return render_template('superadmin/add_employee.html')

@superadmin_bp.route('/employees/<int:emp_id>/deactivate', methods=['POST'])
@superadmin_required
def deactivate_employee(emp_id):
    conn = None
    try:
        conn = get_db_connection()
        execute_query(conn, "DELETE FROM user WHERE user_id=%s AND role IN ('admin','support_staff')", (emp_id,))
        conn.commit()
        flash('Employee removed.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    finally:
        if conn: conn.close()
    return redirect(url_for('superadmin.dashboard'))

@superadmin_bp.route('/students')
@superadmin_required
def students():
    conn = None
    try:
        conn = get_db_connection()
        students = execute_query(conn, """
            SELECT u.*, s.*, uni.name as university_name
            FROM user u
            JOIN student s ON s.student_id = u.user_id
            LEFT JOIN university uni ON uni.university_id = s.university_id
            ORDER BY u.first_name
        """, fetch=True)
        return render_template('superadmin/students.html', students=students)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('superadmin/students.html', students=[])
    finally:
        if conn: conn.close()

@superadmin_bp.route('/universities', methods=['GET', 'POST'])
@superadmin_required
def universities():
    conn = None
    try:
        conn = get_db_connection()
        if request.method == 'POST':
            f = request.form
            name = f.get('name', '').strip()
            address = f.get('address', '').strip()
            rep_first = f.get('rep_first_name', '').strip()
            rep_last = f.get('rep_last_name', '').strip()
            rep_email = f.get('rep_email', '').strip()
            rep_phone = f.get('rep_phone', '').strip()
            if not name:
                flash('University name is required.', 'danger')
            else:
                execute_query(conn, """
                    INSERT INTO university (name, address, rep_first_name, rep_last_name, rep_email, rep_phone)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, address or None, rep_first or None, rep_last or None,
                      rep_email or None, rep_phone or None))
                conn.commit()
                flash(f'University "{name}" added successfully!', 'success')
                return redirect(url_for('superadmin.universities'))
        unis = execute_query(conn, "SELECT * FROM university ORDER BY name", fetch=True)
        return render_template('superadmin/universities.html', universities=unis)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('superadmin/universities.html', universities=[])
    finally:
        if conn: conn.close()


@superadmin_bp.route('/departments', methods=['GET', 'POST'])
@superadmin_required
def departments():
    conn = None
    try:
        conn = get_db_connection()
        if request.method == 'POST':
            f = request.form
            name = f.get('name', '').strip()
            university_id = f.get('university_id', '').strip()
            if not name or not university_id:
                flash('Department name and university are required.', 'danger')
            else:
                execute_query(conn, """
                    INSERT INTO department (name, university_id) VALUES (%s, %s)
                """, (name, university_id))
                conn.commit()
                flash(f'Department "{name}" added successfully!', 'success')
                return redirect(url_for('superadmin.departments'))
        depts = execute_query(conn, """
            SELECT d.*, u.name as university_name
            FROM department d
            JOIN university u ON u.university_id = d.university_id
            ORDER BY u.name, d.name
        """, fetch=True)
        unis = execute_query(conn, "SELECT * FROM university ORDER BY name", fetch=True)
        return render_template('superadmin/departments.html', departments=depts, universities=unis)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('superadmin/departments.html', departments=[], universities=[])
    finally:
        if conn: conn.close()


@superadmin_bp.route('/instructors', methods=['GET', 'POST'])
@superadmin_required
def instructors():
    conn = None
    try:
        conn = get_db_connection()
        if request.method == 'POST':
            f = request.form
            first_name = f.get('first_name', '').strip()
            last_name = f.get('last_name', '').strip()
            university_id = f.get('university_id', '').strip()
            dept_id = f.get('dept_id', '').strip()
            if not first_name or not university_id or not dept_id:
                flash('First name, university and department are required.', 'danger')
            else:
                execute_query(conn, """
                    INSERT INTO instructor (first_name, last_name, university_id, dept_id)
                    VALUES (%s, %s, %s, %s)
                """, (first_name, last_name or '', university_id, dept_id))
                conn.commit()
                flash(f'Instructor "{first_name} {last_name}" added successfully!', 'success')
                return redirect(url_for('superadmin.instructors'))
        instructors_list = execute_query(conn, """
            SELECT i.*, u.name as university_name, d.name as dept_name
            FROM instructor i
            JOIN university u ON u.university_id = i.university_id
            JOIN department d ON d.dept_id = i.dept_id
            ORDER BY i.first_name, i.last_name
        """, fetch=True)
        unis = execute_query(conn, "SELECT * FROM university ORDER BY name", fetch=True)
        depts = execute_query(conn, """
            SELECT d.*, u.name as university_name FROM department d
            JOIN university u ON u.university_id = d.university_id ORDER BY u.name, d.name
        """, fetch=True)
        return render_template('superadmin/instructors.html',
                               instructors=instructors_list, universities=unis, departments=depts)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('superadmin/instructors.html', instructors=[], universities=[], departments=[])
    finally:
        if conn: conn.close()


@superadmin_bp.route('/stats')
@superadmin_required
def stats():
    conn = None
    try:
        conn = get_db_connection()
        total_revenue = execute_query(conn, """
            SELECT COALESCE(SUM(oi.quantity * oi.unit_price),0) as total
            FROM order_item oi
            JOIN `order` o ON o.order_id = oi.order_id
            WHERE o.order_status NOT IN ('canceled')
        """, fetchone=True)
        top_books = execute_query(conn, """
            SELECT b.title, SUM(oi.quantity) as sold,
                   GROUP_CONCAT(ba.author_name SEPARATOR ', ') as authors
            FROM order_item oi
            JOIN book b ON b.book_id = oi.book_id
            LEFT JOIN book_author ba ON ba.book_id = b.book_id
            GROUP BY oi.book_id
            ORDER BY sold DESC LIMIT 10
        """, fetch=True)
        monthly_orders = execute_query(conn, """
            SELECT DATE_FORMAT(created_at,'%Y-%m') as month, COUNT(*) as cnt,
                   SUM(0) as total
            FROM `order`
            WHERE order_status != 'canceled'
            GROUP BY month ORDER BY month DESC LIMIT 12
        """, fetch=True)
        return render_template('superadmin/stats.html',
                               total_revenue=total_revenue['total'],
                               top_books=top_books,
                               monthly_orders=monthly_orders)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('superadmin/stats.html', total_revenue=0, top_books=[], monthly_orders=[])
    finally:
        if conn: conn.close()
