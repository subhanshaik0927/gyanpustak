import os
import mysql.connector
from mysql.connector import Error

import mysql.connector
from mysql.connector import Error
import os

def get_db_connection():
    socket_path = os.environ.get('MYSQL_SOCKET', '/tmp/mysql.sock')
    
    try:
        conn = mysql.connector.connect(
            unix_socket=socket_path,
            user=os.environ.get('MYSQL_USER'),
            password=os.environ.get('MYSQL_PASSWORD'),
            database=os.environ.get('MYSQL_DATABASE'),
            autocommit=False
        )
        return conn
    except Error:
        conn = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST'),
            port=int(os.environ.get('MYSQL_PORT')),
            user=os.environ.get('MYSQL_USER'),
            password=os.environ.get('MYSQL_PASSWORD'),
            database=os.environ.get('MYSQL_DATABASE'),
            autocommit=False
        )
        return conn
def execute_query(conn, query, params=None, fetch=False, fetchone=False):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetchone:
            return cursor.fetchone()
        if fetch:
            return cursor.fetchall()
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
