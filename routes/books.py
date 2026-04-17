from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection, execute_query
from functools import wraps

books_bp = Blueprint('books', __name__, url_prefix='/books')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@books_bp.route('/')
@login_required
def browse():
    conn = None
    try:
        conn = get_db_connection()
        search = request.args.get('q', '').strip()
        category_id = request.args.get('category')
        fmt = request.args.get('format')
        book_type = request.args.get('type')
        purchase = request.args.get('purchase')

        query = """
            SELECT b.*, bc.name as category_name,
                   GROUP_CONCAT(DISTINCT ba.author_name ORDER BY ba.author_name SEPARATOR ', ') as authors
            FROM book b
            LEFT JOIN book_category bc ON b.category_id = bc.category_id
            LEFT JOIN book_author ba ON b.book_id = ba.book_id
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND (b.title LIKE %s OR b.isbn LIKE %s OR ba.author_name LIKE %s)"
            params += [f'%{search}%', f'%{search}%', f'%{search}%']
        if category_id:
            query += " AND b.category_id = %s"
            params.append(category_id)
        if fmt:
            query += " AND b.format = %s"
            params.append(fmt)
        if book_type:
            query += " AND b.book_type = %s"
            params.append(book_type)
        if purchase:
            query += " AND (b.purchase_option = %s OR b.purchase_option = 'both')"
            params.append(purchase)
        query += " GROUP BY b.book_id ORDER BY b.title"

        books = execute_query(conn, query, params, fetch=True)
        categories = execute_query(conn, "SELECT * FROM book_category WHERE parent_id IS NULL ORDER BY name", fetch=True)
        return render_template('books/browse.html', books=books, categories=categories,
                               search=search, category_id=category_id, fmt=fmt,
                               book_type=book_type, purchase=purchase)
    except Exception as e:
        flash(f'Error loading books: {e}', 'danger')
        return render_template('books/browse.html', books=[], categories=[])
    finally:
        if conn: conn.close()

@books_bp.route('/<int:book_id>')
@login_required
def detail(book_id):
    conn = None
    try:
        conn = get_db_connection()
        book = execute_query(conn, """
            SELECT b.*, bc.name as category_name
            FROM book b
            LEFT JOIN book_category bc ON b.category_id = bc.category_id
            WHERE b.book_id = %s
        """, (book_id,), fetchone=True)
        if not book:
            flash('Book not found.', 'danger')
            return redirect(url_for('books.browse'))
        authors = execute_query(conn, "SELECT author_name FROM book_author WHERE book_id=%s", (book_id,), fetch=True)
        keywords = execute_query(conn, "SELECT keyword FROM book_keyword WHERE book_id=%s", (book_id,), fetch=True)
        reviews = execute_query(conn, """
            SELECT r.*, u.first_name, u.last_name
            FROM review r
            JOIN user u ON u.user_id = r.student_id
            WHERE r.book_id = %s
            ORDER BY r.created_at DESC
        """, (book_id,), fetch=True)
        courses = execute_query(conn, """
            SELECT c.course_code, c.course_name, u.name as university_name, cb.requirement
            FROM course_book cb
            JOIN course c ON c.course_id = cb.course_id
            JOIN university u ON u.university_id = c.university_id
            WHERE cb.book_id = %s
        """, (book_id,), fetch=True)
        user_review = None
        if session.get('role') == 'student':
            user_review = execute_query(conn, "SELECT * FROM review WHERE student_id=%s AND book_id=%s",
                                        (session['user_id'], book_id), fetchone=True)
        return render_template('books/detail.html', book=book, authors=authors,
                               keywords=keywords, reviews=reviews, courses=courses,
                               user_review=user_review)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('books.browse'))
    finally:
        if conn: conn.close()

@books_bp.route('/<int:book_id>/review', methods=['POST'])
@login_required
def add_review(book_id):
    if session.get('role') != 'student':
        flash('Only students can write reviews.', 'danger')
        return redirect(url_for('books.detail', book_id=book_id))
    rating = request.form.get('rating')
    review_text = request.form.get('review_text', '').strip()
    conn = None
    try:
        conn = get_db_connection()
        existing = execute_query(conn, "SELECT review_id FROM review WHERE student_id=%s AND book_id=%s",
                                 (session['user_id'], book_id), fetchone=True)
        if existing:
            execute_query(conn, "UPDATE review SET rating=%s, review_text=%s WHERE student_id=%s AND book_id=%s",
                          (rating, review_text, session['user_id'], book_id))
        else:
            execute_query(conn, "INSERT INTO review (student_id,book_id,rating,review_text) VALUES (%s,%s,%s,%s)",
                          (session['user_id'], book_id, rating, review_text))
        avg = execute_query(conn, "SELECT AVG(rating) as avg FROM review WHERE book_id=%s", (book_id,), fetchone=True)
        execute_query(conn, "UPDATE book SET avg_rating=%s WHERE book_id=%s", (avg['avg'], book_id))
        conn.commit()
        flash('Review submitted!', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    finally:
        if conn: conn.close()
    return redirect(url_for('books.detail', book_id=book_id))
