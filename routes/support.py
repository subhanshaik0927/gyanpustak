from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection, execute_query
from functools import wraps

support_bp = Blueprint('support', __name__, url_prefix='/support')

def support_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'support_staff':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@support_bp.route('/dashboard')
@support_required
def dashboard():
    conn = None
    try:
        conn = get_db_connection()
        counts = execute_query(conn, """
            SELECT status, COUNT(*) as cnt FROM trouble_ticket GROUP BY status
        """, fetch=True)
        recent_tickets = execute_query(conn, """
            SELECT t.*, u.first_name, u.last_name
            FROM trouble_ticket t
            JOIN user u ON u.user_id = t.created_by_user
            ORDER BY t.created_at DESC LIMIT 10
        """, fetch=True)
        stats = {row['status']: row['cnt'] for row in counts}
        return render_template('support/dashboard.html', stats=stats, recent_tickets=recent_tickets)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('support/dashboard.html', stats={}, recent_tickets=[])
    finally:
        if conn: conn.close()

@support_bp.route('/tickets')
@support_required
def tickets():
    conn = None
    try:
        conn = get_db_connection()
        status_filter = request.args.get('status', '')
        query = """
            SELECT t.*, u.first_name, u.last_name
            FROM trouble_ticket t
            JOIN user u ON u.user_id = t.created_by_user
            WHERE 1=1
        """
        params = []
        if status_filter:
            query += " AND t.status = %s"
            params.append(status_filter)
        query += " ORDER BY t.created_at DESC"
        tickets = execute_query(conn, query, params, fetch=True)
        return render_template('support/tickets.html', tickets=tickets, status_filter=status_filter)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('support/tickets.html', tickets=[], status_filter='')
    finally:
        if conn: conn.close()

@support_bp.route('/tickets/<int:ticket_id>/assign', methods=['POST'])
@support_required
def assign_ticket(ticket_id):
    conn = None
    try:
        conn = get_db_connection()
        ticket = execute_query(conn, "SELECT * FROM trouble_ticket WHERE ticket_id=%s", (ticket_id,), fetchone=True)
        if not ticket or ticket['status'] != 'new':
            flash('Can only assign tickets with status "new".', 'warning')
        else:
            execute_query(conn, "UPDATE trouble_ticket SET status='assigned' WHERE ticket_id=%s", (ticket_id,))
            execute_query(conn, """
                INSERT INTO ticket_status_log (ticket_id, old_status, new_status, changed_by)
                VALUES (%s,'new','assigned',%s)
            """, (ticket_id, session['user_id']))
            conn.commit()
            flash('Ticket assigned to admin.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    finally:
        if conn: conn.close()
    return redirect(url_for('support.tickets'))
