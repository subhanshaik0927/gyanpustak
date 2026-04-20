from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection, execute_query
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ('admin', 'super_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    conn = None
    try:
        conn = get_db_connection()
        book_count = execute_query(conn, "SELECT COUNT(*) as cnt FROM book", fetchone=True)['cnt']
        order_count = execute_query(conn, "SELECT COUNT(*) as cnt FROM `order`", fetchone=True)['cnt']
        student_count = execute_query(conn, "SELECT COUNT(*) as cnt FROM student", fetchone=True)['cnt']
        ticket_counts = execute_query(conn, "SELECT status, COUNT(*) as cnt FROM trouble_ticket GROUP BY status", fetch=True)
        recent_orders = execute_query(conn, """
            SELECT o.*, u.first_name, u.last_name
            FROM `order` o JOIN user u ON u.user_id = o.student_id
            ORDER BY o.created_at DESC LIMIT 5
        """, fetch=True)
        t_stats = {row['status']: row['cnt'] for row in ticket_counts}
        return render_template('admin/dashboard.html',
                               book_count=book_count, order_count=order_count,
                               student_count=student_count, t_stats=t_stats,
                               recent_orders=recent_orders)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('admin/dashboard.html', book_count=0, order_count=0,
                               student_count=0, t_stats={}, recent_orders=[])
    finally:
        if conn: conn.close()

@admin_bp.route('/books')
@admin_required
def books():
    conn = None
    try:
        conn = get_db_connection()
        books = execute_query(conn, """
            SELECT b.*, bc.name as category_name,
                   GROUP_CONCAT(DISTINCT ba.author_name SEPARATOR ', ') as authors
            FROM book b
            LEFT JOIN book_category bc ON bc.category_id = b.category_id
            LEFT JOIN book_author ba ON ba.book_id = b.book_id
            GROUP BY b.book_id ORDER BY b.title
        """, fetch=True)
        return render_template('admin/books.html', books=books)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('admin/books.html', books=[])
    finally:
        if conn: conn.close()

@admin_bp.route('/books/add', methods=['GET', 'POST'])
@admin_required
def add_book():
    conn = None
    if request.method == 'POST':
        f = request.form
        try:
            conn = get_db_connection()
            book_id = execute_query(conn, """
                INSERT INTO book (title,isbn,publisher,publication_date,edition,language,format,
                                  book_type,purchase_option,price,quantity,category_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (f['title'], f['isbn'], f.get('publisher'), f.get('publication_date') or None,
                  f.get('edition', 1), f.get('language', 'English'), f['format'],
                  f['book_type'], f['purchase_option'], f['price'], f['quantity'],
                  f.get('category_id') or None))
            for author in [a.strip() for a in f.get('authors', '').split(',') if a.strip()]:
                execute_query(conn, "INSERT IGNORE INTO book_author (book_id,author_name) VALUES (%s,%s)", (book_id, author))
            for kw in [k.strip() for k in f.get('keywords', '').split(',') if k.strip()]:
                execute_query(conn, "INSERT IGNORE INTO book_keyword (book_id,keyword) VALUES (%s,%s)", (book_id, kw))
            conn.commit()
            flash('Book added successfully!', 'success')
            return redirect(url_for('admin.books'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
        finally:
            if conn: conn.close()
    conn2 = None
    categories = []
    try:
        conn2 = get_db_connection()
        categories = execute_query(conn2, "SELECT * FROM book_category ORDER BY name", fetch=True)
    except Exception: pass
    finally:
        if conn2: conn2.close()
    return render_template('admin/add_book.html', categories=categories)

@admin_bp.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id):
    conn = None
    try:
        conn = get_db_connection()
        book = execute_query(conn, "SELECT * FROM book WHERE book_id=%s", (book_id,), fetchone=True)
        if not book:
            flash('Book not found.', 'danger')
            return redirect(url_for('admin.books'))
        authors = execute_query(conn, "SELECT author_name FROM book_author WHERE book_id=%s", (book_id,), fetch=True)
        keywords = execute_query(conn, "SELECT keyword FROM book_keyword WHERE book_id=%s", (book_id,), fetch=True)
        categories = execute_query(conn, "SELECT * FROM book_category ORDER BY name", fetch=True)
        if request.method == 'POST':
            f = request.form
            execute_query(conn, """
                UPDATE book SET title=%s,isbn=%s,publisher=%s,publication_date=%s,edition=%s,
                language=%s,format=%s,book_type=%s,purchase_option=%s,price=%s,quantity=%s,category_id=%s
                WHERE book_id=%s
            """, (f['title'], f['isbn'], f.get('publisher'), f.get('publication_date') or None,
                  f.get('edition', 1), f.get('language', 'English'), f['format'],
                  f['book_type'], f['purchase_option'], f['price'], f['quantity'],
                  f.get('category_id') or None, book_id))
            execute_query(conn, "DELETE FROM book_author WHERE book_id=%s", (book_id,))
            for author in [a.strip() for a in f.get('authors', '').split(',') if a.strip()]:
                execute_query(conn, "INSERT IGNORE INTO book_author (book_id,author_name) VALUES (%s,%s)", (book_id, author))
            execute_query(conn, "DELETE FROM book_keyword WHERE book_id=%s", (book_id,))
            for kw in [k.strip() for k in f.get('keywords', '').split(',') if k.strip()]:
                execute_query(conn, "INSERT IGNORE INTO book_keyword (book_id,keyword) VALUES (%s,%s)", (book_id, kw))
            conn.commit()
            flash('Book updated.', 'success')
            return redirect(url_for('admin.books'))
        return render_template('admin/edit_book.html', book=book, authors=authors,
                               keywords=keywords, categories=categories)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('admin.books'))
    finally:
        if conn: conn.close()

@admin_bp.route('/tickets')
@admin_required
def tickets():
    conn = None
    try:
        conn = get_db_connection()
        status_filter = request.args.get('status', '')
        query = """
            SELECT t.*, u.first_name, u.last_name
            FROM trouble_ticket t
            JOIN user u ON u.user_id = t.created_by_user
            WHERE t.status IN ('assigned','in-process','completed')
        """
        params = []
        if status_filter:
            query += " AND t.status = %s"
            params.append(status_filter)
        query += " ORDER BY t.created_at DESC"
        tickets = execute_query(conn, query, params, fetch=True)
        return render_template('admin/tickets.html', tickets=tickets, status_filter=status_filter)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('admin/tickets.html', tickets=[], status_filter='')
    finally:
        if conn: conn.close()

@admin_bp.route('/inventory')
@admin_required
def inventory():
    conn = None
    try:
        conn = get_db_connection()
        low_stock = execute_query(conn, """
            SELECT b.*, GROUP_CONCAT(ba.author_name SEPARATOR ', ') as authors
            FROM book b
            LEFT JOIN book_author ba ON ba.book_id = b.book_id
            GROUP BY b.book_id
            ORDER BY b.quantity ASC LIMIT 20
        """, fetch=True)
        return render_template('admin/inventory.html', books=low_stock)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('admin/inventory.html', books=[])
    finally:
        if conn: conn.close()

@admin_bp.route('/inventory/<int:book_id>/update', methods=['POST'])
@admin_required
def update_inventory(book_id):
    quantity = request.form.get('quantity', 0)
    conn = None
    try:
        conn = get_db_connection()
        execute_query(conn, "UPDATE book SET quantity=%s WHERE book_id=%s", (quantity, book_id))
        conn.commit()
        flash('Inventory updated.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    finally:
        if conn: conn.close()
    return redirect(url_for('admin.inventory'))

@admin_bp.route('/orders')
@admin_required
def orders():
    conn = None
    try:
        conn = get_db_connection()
        orders = execute_query(conn, """
            SELECT o.*, u.first_name, u.last_name,
                   SUM(oi.quantity * oi.unit_price) as total
            FROM `order` o
            JOIN user u ON u.user_id = o.student_id
            LEFT JOIN order_item oi ON oi.order_id = o.order_id
            GROUP BY o.order_id
            ORDER BY o.created_at DESC
        """, fetch=True)
        return render_template('admin/orders.html', orders=orders)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('admin/orders.html', orders=[])
    finally:
        if conn: conn.close()

@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    new_status = request.form.get('status')
    conn = None
    try:
        conn = get_db_connection()
        execute_query(conn, "UPDATE `order` SET order_status=%s WHERE order_id=%s", (new_status, order_id))
        conn.commit()
        flash('Order status updated.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    finally:
        if conn: conn.close()
    return redirect(url_for('admin.orders'))

@admin_bp.route('/courses')
@admin_required
def courses():
    conn = None
    try:
        conn = get_db_connection()
        courses = execute_query(conn, """
            SELECT c.*, u.name as university_name, d.name as dept_name
            FROM course c
            JOIN university u ON u.university_id = c.university_id
            JOIN department d ON d.dept_id = c.dept_id
            ORDER BY u.name, c.course_code
        """, fetch=True)
        return render_template('admin/courses.html', courses=courses)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('admin/courses.html', courses=[])
    finally:
        if conn: conn.close()

@admin_bp.route('/courses/add', methods=['GET', 'POST'])
@admin_required
def add_course():
    conn = None
    try:
        conn = get_db_connection()
        unis = execute_query(conn, "SELECT * FROM university ORDER BY name", fetch=True)
        depts = execute_query(conn, """
            SELECT d.*, u.name as university_name FROM department d
            JOIN university u ON u.university_id = d.university_id ORDER BY u.name, d.name
        """, fetch=True)
        if request.method == 'POST':
            f = request.form
            course_code = f.get('course_code', '').strip()
            course_name = f.get('course_name', '').strip()
            university_id = f.get('university_id', '').strip()
            dept_id = f.get('dept_id', '').strip()
            year = f.get('year', '').strip() or None
            semester = f.get('semester', '').strip() or None
            if not course_code or not course_name or not university_id or not dept_id:
                flash('Course code, name, university and department are required.', 'danger')
            else:
                execute_query(conn, """
                    INSERT INTO course (course_code, course_name, university_id, dept_id, year, semester)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (course_code, course_name, university_id, dept_id, year, semester))
                conn.commit()
                flash(f'Course "{course_code} — {course_name}" added successfully!', 'success')
                return redirect(url_for('admin.courses'))
        return render_template('admin/add_course.html', universities=unis, departments=depts)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('admin.courses'))
    finally:
        if conn: conn.close()


@admin_bp.route('/courses/<int:course_id>/books', methods=['GET', 'POST'])
@admin_required
def course_books(course_id):
    conn = None
    try:
        conn = get_db_connection()
        course = execute_query(conn, "SELECT * FROM course WHERE course_id=%s", (course_id,), fetchone=True)
        course_books = execute_query(conn, """
            SELECT cb.*, b.title, b.isbn
            FROM course_book cb JOIN book b ON b.book_id = cb.book_id
            WHERE cb.course_id = %s
        """, (course_id,), fetch=True)
        all_books = execute_query(conn, "SELECT book_id, title, isbn FROM book ORDER BY title", fetch=True)
        if request.method == 'POST':
            book_id = request.form.get('book_id')
            requirement = request.form.get('requirement', 'required')
            execute_query(conn, """
                INSERT IGNORE INTO course_book (course_id,book_id,requirement) VALUES (%s,%s,%s)
            """, (course_id, book_id, requirement))
            conn.commit()
            flash('Book linked to course.', 'success')
            return redirect(url_for('admin.course_books', course_id=course_id))
        return render_template('admin/course_books.html', course=course,
                               course_books=course_books, all_books=all_books)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('admin.courses'))
    finally:
        if conn: conn.close()
