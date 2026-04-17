from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection, execute_query
from functools import wraps

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'student':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@orders_bp.route('/')
@student_required
def list_orders():
    conn = None
    try:
        conn = get_db_connection()
        orders = execute_query(conn, """
            SELECT o.*, COUNT(oi.book_id) as item_count,
                   SUM(oi.quantity * oi.unit_price) as total
            FROM `order` o
            LEFT JOIN order_item oi ON oi.order_id = o.order_id
            WHERE o.student_id = %s
            GROUP BY o.order_id
            ORDER BY o.created_at DESC
        """, (session['user_id'],), fetch=True)
        return render_template('orders/list.html', orders=orders)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('orders/list.html', orders=[])
    finally:
        if conn: conn.close()

@orders_bp.route('/<int:order_id>')
@student_required
def detail(order_id):
    conn = None
    try:
        conn = get_db_connection()
        order = execute_query(conn, "SELECT * FROM `order` WHERE order_id=%s AND student_id=%s",
                              (order_id, session['user_id']), fetchone=True)
        if not order:
            flash('Order not found.', 'danger')
            return redirect(url_for('orders.list_orders'))
        items = execute_query(conn, """
            SELECT oi.*, b.title, GROUP_CONCAT(ba.author_name SEPARATOR ', ') as authors
            FROM order_item oi
            JOIN book b ON b.book_id = oi.book_id
            LEFT JOIN book_author ba ON ba.book_id = oi.book_id
            WHERE oi.order_id = %s
            GROUP BY oi.book_id
        """, (order_id,), fetch=True)
        total = sum(item['quantity'] * item['unit_price'] for item in items)
        return render_template('orders/detail.html', order=order, items=items, total=total)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('orders.list_orders'))
    finally:
        if conn: conn.close()

@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
@student_required
def cancel(order_id):
    conn = None
    try:
        conn = get_db_connection()
        order = execute_query(conn, "SELECT * FROM `order` WHERE order_id=%s AND student_id=%s",
                              (order_id, session['user_id']), fetchone=True)
        if not order:
            flash('Order not found.', 'danger')
        elif order['order_status'] not in ('new', 'processed'):
            flash('This order cannot be cancelled.', 'warning')
        else:
            execute_query(conn, "UPDATE `order` SET order_status='canceled' WHERE order_id=%s", (order_id,))
            items = execute_query(conn, "SELECT * FROM order_item WHERE order_id=%s", (order_id,), fetch=True)
            for item in items:
                execute_query(conn, "UPDATE book SET quantity=quantity+%s WHERE book_id=%s",
                              (item['quantity'], item['book_id']))
            conn.commit()
            flash('Order cancelled successfully.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    finally:
        if conn: conn.close()
    return redirect(url_for('orders.detail', order_id=order_id))
