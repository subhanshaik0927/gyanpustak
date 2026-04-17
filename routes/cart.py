from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection, execute_query
from functools import wraps

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'student':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)
    return decorated

@cart_bp.route('/')
@student_required
def view():
    conn = None
    try:
        conn = get_db_connection()
        cart = execute_query(conn, "SELECT * FROM cart WHERE student_id=%s", (session['user_id'],), fetchone=True)
        if not cart:
            execute_query(conn, "INSERT INTO cart (student_id) VALUES (%s)", (session['user_id'],))
            conn.commit()
            cart = execute_query(conn, "SELECT * FROM cart WHERE student_id=%s", (session['user_id'],), fetchone=True)
        items = execute_query(conn, """
            SELECT ci.*, b.title, b.price, b.format, b.book_type,
                   GROUP_CONCAT(ba.author_name SEPARATOR ', ') as authors
            FROM cart_item ci
            JOIN book b ON b.book_id = ci.book_id
            LEFT JOIN book_author ba ON ba.book_id = ci.book_id
            WHERE ci.cart_id = %s
            GROUP BY ci.book_id
        """, (cart['cart_id'],), fetch=True)
        total = sum(item['price'] * item['quantity'] for item in items)
        return render_template('cart/view.html', cart=cart, items=items, total=total)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('cart/view.html', cart=None, items=[], total=0)
    finally:
        if conn: conn.close()

@cart_bp.route('/add', methods=['POST'])
@student_required
def add():
    book_id = request.form.get('book_id')
    quantity = int(request.form.get('quantity', 1))
    purchase_option = request.form.get('purchase_option', 'buy')
    conn = None
    try:
        conn = get_db_connection()
        cart = execute_query(conn, "SELECT * FROM cart WHERE student_id=%s", (session['user_id'],), fetchone=True)
        if not cart:
            execute_query(conn, "INSERT INTO cart (student_id) VALUES (%s)", (session['user_id'],))
            cart = execute_query(conn, "SELECT * FROM cart WHERE student_id=%s", (session['user_id'],), fetchone=True)
        existing = execute_query(conn, "SELECT * FROM cart_item WHERE cart_id=%s AND book_id=%s",
                                 (cart['cart_id'], book_id), fetchone=True)
        if existing:
            execute_query(conn, "UPDATE cart_item SET quantity=quantity+%s WHERE cart_id=%s AND book_id=%s",
                          (quantity, cart['cart_id'], book_id))
        else:
            execute_query(conn, "INSERT INTO cart_item (cart_id,book_id,quantity,purchase_option) VALUES (%s,%s,%s,%s)",
                          (cart['cart_id'], book_id, quantity, purchase_option))
        conn.commit()
        flash('Book added to cart!', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    finally:
        if conn: conn.close()
    return redirect(url_for('books.detail', book_id=book_id))

@cart_bp.route('/remove/<int:book_id>', methods=['POST'])
@student_required
def remove(book_id):
    conn = None
    try:
        conn = get_db_connection()
        cart = execute_query(conn, "SELECT * FROM cart WHERE student_id=%s", (session['user_id'],), fetchone=True)
        if cart:
            execute_query(conn, "DELETE FROM cart_item WHERE cart_id=%s AND book_id=%s", (cart['cart_id'], book_id))
            conn.commit()
            flash('Item removed.', 'info')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    finally:
        if conn: conn.close()
    return redirect(url_for('cart.view'))

@cart_bp.route('/checkout', methods=['GET', 'POST'])
@student_required
def checkout():
    conn = None
    try:
        conn = get_db_connection()
        cart = execute_query(conn, "SELECT * FROM cart WHERE student_id=%s", (session['user_id'],), fetchone=True)
        items = execute_query(conn, """
            SELECT ci.*, b.title, b.price, b.quantity as stock
            FROM cart_item ci JOIN book b ON b.book_id = ci.book_id
            WHERE ci.cart_id = %s
        """, (cart['cart_id'],), fetch=True)
        total = sum(item['price'] * item['quantity'] for item in items)

        if request.method == 'POST':
            shipping = request.form.get('shipping_type', 'standard')
            cc_number = request.form.get('cc_number', '').replace(' ', '')
            cc_expiry = request.form.get('cc_expiry', '')
            cc_holder = request.form.get('cc_holder', '')
            cc_type = request.form.get('cc_type', 'Visa')
            order_id = execute_query(conn, """
                INSERT INTO `order` (student_id, shipping_type, cc_number, cc_expiry, cc_holder, cc_type, order_status)
                VALUES (%s,%s,%s,%s,%s,%s,'new')
            """, (session['user_id'], shipping, cc_number, cc_expiry, cc_holder, cc_type))
            for item in items:
                execute_query(conn, """
                    INSERT INTO order_item (order_id,book_id,quantity,unit_price,purchase_option)
                    VALUES (%s,%s,%s,%s,%s)
                """, (order_id, item['book_id'], item['quantity'], item['price'], item['purchase_option']))
                execute_query(conn, "UPDATE book SET quantity=quantity-%s WHERE book_id=%s",
                              (item['quantity'], item['book_id']))
            execute_query(conn, "DELETE FROM cart_item WHERE cart_id=%s", (cart['cart_id'],))
            conn.commit()
            flash('Order placed successfully!', 'success')
            return redirect(url_for('orders.detail', order_id=order_id))
        return render_template('cart/checkout.html', items=items, total=total)
    except Exception as e:
        flash(f'Checkout error: {e}', 'danger')
        return redirect(url_for('cart.view'))
    finally:
        if conn: conn.close()
