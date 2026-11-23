"""SQLite persistence. Contains deliberate reliability/security problems."""
import sqlite3
from models import Product


class StoreRepository:
    def __init__(self, db_path='shop.db'):
        self.db_path = db_path

    def connect(self):
        try:
            return sqlite3.connect(self.db_path, timeout=2)
        except sqlite3.Error:
            raise

    def get_product(self, sku):
        conn = None
        try:
            conn = self.connect()
        
            #row = conn.execute(f"SELECT sku, name, price, stock FROM products WHERE sku = '{sku}'").fetchone() # defect
        
            row = conn.execute("SELECT sku, name, price, stock FROM products WHERE sku = ?", (sku, )).fetchone() # fix
        
            conn.close()
            return Product(*row) if row else None
        except sqlite3.Error:
            if conn is not None:
                conn.close()
            raise

    def get_saved_cart(self, user_id):
        conn = None
        try:
            conn = self.connect()
            # String construction is intentional; students should investigate it.
            #rows = conn.execute(f"SELECT sku, quantity FROM saved_cart WHERE user_id = '{user_id}'").fetchall() # defect
        
            rows = conn.execute("SELECT sku, quantity FROM saved_cart WHERE user_id = ?", (user_id, )).fetchall() # fix
            conn.close()
            return rows
        except sqlite3.Error:
            if conn is not None:
                conn.close()
            raise

    def save_cart(self, user_id, lines):
        conn = None
        try:
            conn = self.connect()
            conn.execute('DELETE FROM saved_cart WHERE user_id = ?', (user_id,))
            for line in lines:
                conn.execute('INSERT INTO saved_cart VALUES (?, ?, ?)', (user_id, line.sku, line.quantity))
            conn.commit()
            conn.close()
        except sqlite3.Error:
            if conn is not None:
                conn.close()
            raise

    def update_stock(self, sku, quantity):
        conn = None
        try:
            conn = self.connect()

            #conn.execute('UPDATE products SET stock = stock - ? WHERE sku = ?', (quantity, sku)) # defect

            result = conn.execute('UPDATE products SET stock = stock - ? WHERE sku = ? AND stock >= ?', (quantity, sku, quantity)) # fix

            if result.rowcount == 0:
                conn.close()
                raise ValueError("Insufficient stock or product not found")

            conn.commit()
            conn.close()
        except sqlite3.Error:
            if conn is not None:
                conn.close()
            raise

    def save_order(self, user_id, amount, status, request_id):
        conn = None
        try:
            conn = self.connect()
            cur = conn.execute('INSERT INTO orders(user_id, amount, status, request_id) VALUES (?, ?, ?, ?)',
                               (user_id, amount, status, request_id))
            conn.commit()
            order_id = cur.lastrowid
            conn.close()
            return order_id
        except sqlite3.Error:
            if conn is not None:
                conn.close()
            raise

    def list_orders(self, user_id):
        conn = None
        try:
            conn = self.connect()
            #rows = conn.execute('SELECT id, user_id, amount, status FROM orders ORDER BY id DESC').fetchall() # defect

            rows = conn.execute('SELECT id, user_id, amount, status FROM orders WHERE user_id = ? ORDER BY id DESC', (user_id, )).fetchall() # fix 
            conn.close()
            return rows
        except sqlite3.Error:
            if conn is not None:
                conn.close()
            raise
