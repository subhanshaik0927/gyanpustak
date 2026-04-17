import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'gyanpustak-secret-key-2025')

app.jinja_env.globals['enumerate'] = enumerate

from routes.auth import auth_bp
from routes.student import student_bp
from routes.books import books_bp
from routes.cart import cart_bp
from routes.orders import orders_bp
from routes.tickets import tickets_bp
from routes.admin import admin_bp
from routes.support import support_bp
from routes.superadmin import superadmin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(books_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(tickets_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(support_bp)
app.register_blueprint(superadmin_bp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=False)
