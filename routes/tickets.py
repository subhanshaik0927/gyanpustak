from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection, execute_query
from functools import wraps

tickets_bp = Blueprint('tickets', __name__, url_prefix='/tickets')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

CATEGORIES = ['user profile', 'products', 'cart', 'orders', 'other']

@tickets_bp.route('/')
@login_required
def list_tickets():
    conn = None
    try:
        conn = get_db_connection()
        role = session.get('role')
        user_id = session['user_id']
        if role == 'student':
            tickets = execute_query(conn, """
                SELECT t.*, u.first_name, u.last_name
                FROM trouble_ticket t
                JOIN user u ON u.user_id = t.created_by_user
                WHERE t.created_by_user = %s
                ORDER BY t.created_at DESC
            """, (user_id,), fetch=True)
        else:
            tickets = execute_query(conn, """
                SELECT t.*, u.first_name, u.last_name
                FROM trouble_ticket t
                JOIN user u ON u.user_id = t.created_by_user
                ORDER BY t.created_at DESC
            """, fetch=True)
        return render_template('tickets/list.html', tickets=tickets, categories=CATEGORIES)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('tickets/list.html', tickets=[], categories=CATEGORIES)
    finally:
        if conn: conn.close()

@tickets_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    role = session.get('role')
    if role == 'admin':
        flash('Admins cannot create tickets.', 'danger')
        return redirect(url_for('tickets.list_tickets'))
    if request.method == 'POST':
        category = request.form.get('category')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        conn = None
        try:
            conn = get_db_connection()
            ticket_id = execute_query(conn, """
                INSERT INTO trouble_ticket (category, title, description, status, created_by_user)
                VALUES (%s,%s,%s,'new',%s)
            """, (category, title, description, session['user_id']))
            execute_query(conn, """
                INSERT INTO ticket_status_log (ticket_id, old_status, new_status, changed_by)
                VALUES (%s, NULL, 'new', %s)
            """, (ticket_id, session['user_id']))
            conn.commit()
            flash('Ticket submitted successfully!', 'success')
            return redirect(url_for('tickets.detail', ticket_id=ticket_id))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
        finally:
            if conn: conn.close()
    return render_template('tickets/create.html', categories=CATEGORIES)

@tickets_bp.route('/<int:ticket_id>')
@login_required
def detail(ticket_id):
    conn = None
    try:
        conn = get_db_connection()
        role = session.get('role')
        ticket = execute_query(conn, """
            SELECT t.*, u.first_name, u.last_name,
                   au.first_name as admin_fname, au.last_name as admin_lname
            FROM trouble_ticket t
            JOIN user u ON u.user_id = t.created_by_user
            LEFT JOIN admin a ON a.admin_id = t.resolved_by_admin
            LEFT JOIN user au ON au.user_id = a.admin_id
            WHERE t.ticket_id = %s
        """, (ticket_id,), fetchone=True)
        if not ticket:
            flash('Ticket not found.', 'danger')
            return redirect(url_for('tickets.list_tickets'))
        if role == 'student' and ticket['created_by_user'] != session['user_id']:
            flash('Access denied.', 'danger')
            return redirect(url_for('tickets.list_tickets'))
        logs = execute_query(conn, """
            SELECT tsl.*, u.first_name, u.last_name
            FROM ticket_status_log tsl
            JOIN user u ON u.user_id = tsl.changed_by
            WHERE tsl.ticket_id = %s
            ORDER BY tsl.changed_at
        """, (ticket_id,), fetch=True)
        return render_template('tickets/detail.html', ticket=ticket, logs=logs)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('tickets.list_tickets'))
    finally:
        if conn: conn.close()

@tickets_bp.route('/<int:ticket_id>/update', methods=['POST'])
@login_required
def update(ticket_id):
    role = session.get('role')
    conn = None
    try:
        conn = get_db_connection()
        ticket = execute_query(conn, "SELECT * FROM trouble_ticket WHERE ticket_id=%s", (ticket_id,), fetchone=True)
        if not ticket:
            flash('Ticket not found.', 'danger')
            return redirect(url_for('tickets.list_tickets'))

        old_status = ticket['status']
        new_status = request.form.get('status', old_status)
        solution = request.form.get('solution', ticket.get('solution', '') or '')

        if role == 'support_staff':
            if old_status != 'new':
                flash('Support staff can only modify new tickets.', 'warning')
                return redirect(url_for('tickets.detail', ticket_id=ticket_id))
            execute_query(conn, "UPDATE trouble_ticket SET status=%s WHERE ticket_id=%s", (new_status, ticket_id))
        elif role == 'admin':
            if old_status == 'new':
                flash('Admins cannot edit new tickets.', 'warning')
                return redirect(url_for('tickets.detail', ticket_id=ticket_id))
            resolved_by = session['user_id'] if new_status == 'completed' else ticket['resolved_by_admin']
            completed_at = 'NOW()' if new_status == 'completed' else 'NULL'
            execute_query(conn, f"""
                UPDATE trouble_ticket
                SET status=%s, solution=%s, resolved_by_admin=%s,
                    completed_at={'NOW()' if new_status == 'completed' else 'NULL'}
                WHERE ticket_id=%s
            """, (new_status, solution, resolved_by, ticket_id))

        if old_status != new_status:
            execute_query(conn, """
                INSERT INTO ticket_status_log (ticket_id, old_status, new_status, changed_by)
                VALUES (%s,%s,%s,%s)
            """, (ticket_id, old_status, new_status, session['user_id']))
        conn.commit()
        flash('Ticket updated.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    finally:
        if conn: conn.close()
    return redirect(url_for('tickets.detail', ticket_id=ticket_id))
