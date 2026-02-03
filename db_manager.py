import sqlite3
import datetime

import sys
import os

DB_NAME = "invoices.db"

def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as python script
        return os.path.dirname(os.path.abspath(__file__))

def get_db_path():
    return os.path.join(get_base_path(), DB_NAME)

def get_connection():
    return sqlite3.connect(get_db_path())

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Clients Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            email TEXT,
            phone TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Invoices Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            invoice_number TEXT UNIQUE NOT NULL,
            date_issued DATE,
            due_date DATE,
            status TEXT DEFAULT 'Draft',
            total_amount REAL,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    ''')

    # Migration: Add vat_exempt column if it doesn't exist
    try:
        cursor.execute('SELECT vat_exempt FROM invoices LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE invoices ADD COLUMN vat_exempt BOOLEAN DEFAULT 0')

    # Settings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Initialize default settings if empty
    cursor.execute('SELECT count(*) FROM settings')
    if cursor.fetchone()[0] == 0:
        defaults = [
            ("sender_name", "Your Name"),
            ("sender_address_line1", "Address Line 1"),
            ("sender_address_line2", "City"),
            ("sender_address_line3", "Country"),
            ("sender_email", "email@example.com"),
            ("sender_phone", "+1 234 567 890"),
            ("bank_iban", "LB00 0000 0000 0000 0000 0000 0000"),
            ("bank_branch", "Bank Branch"),
            ("bank_swift", "SWIFTCODE"),
            ("vat_percentage", "11")
        ]
        cursor.executemany('INSERT INTO settings (key, value) VALUES (?, ?)', defaults)
    
    conn.commit()
    conn.close()

def add_client(name, address, email, phone, category):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO clients (name, address, email, phone, category)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, address, email, phone, category))
    conn.commit()
    conn.close()

def get_clients():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients')
    clients = cursor.fetchall()
    conn.close()
    return clients

def get_client(client_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
    client = cursor.fetchone()
    conn.close()
    return client

def create_invoice(client_id, invoice_number, date_issued, due_date, items, vat_exempt=False):
    # items is a list of tuples/dicts: (description, quantity, rate)
    conn = get_connection()
    cursor = conn.cursor()
    
    total_amount = sum(item['quantity'] * item['rate'] for item in items)
    
    try:
        cursor.execute('''
            INSERT INTO invoices (client_id, invoice_number, date_issued, due_date, status, total_amount, vat_exempt)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (client_id, invoice_number, date_issued, due_date, 'Draft', total_amount, vat_exempt))
        
        invoice_id = cursor.lastrowid
        
        for item in items:
            amount = item['quantity'] * item['rate']
            cursor.execute('''
                INSERT INTO invoice_items (invoice_id, description, quantity, rate, amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (invoice_id, item['description'], item['quantity'], item['rate'], amount))
            
        conn.commit()
        return invoice_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_invoices():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT i.id, i.invoice_number, c.name, i.date_issued, i.status, i.total_amount, i.vat_exempt
        FROM invoices i
        JOIN clients c ON i.client_id = c.id
        ORDER BY i.date_issued DESC
    ''')
    invoices = cursor.fetchall()
    conn.close()
    return invoices

def get_invoice_details(invoice_number):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM invoices WHERE invoice_number = ?
    ''', (invoice_number,))
    invoice = cursor.fetchone()
    
    if not invoice:
        conn.close()
        return None
        
    invoice_id = invoice[0]
    client_id = invoice[1]
    # invoice schema: id, client_id, invoice_number, date_issued, due_date, status, total_amount, vat_exempt(index 7 if exists)
    
    # Check if vat_exempt is in the row (column index 7)
    vat_exempt = False
    if len(invoice) > 7:
        vat_exempt = bool(invoice[7])

    cursor.execute('SELECT * FROM invoice_items WHERE invoice_id = ?', (invoice_id,))
    items = cursor.fetchall()
    
    cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
    client = cursor.fetchone()
    
    conn.close()
    
    # Return a structured dictionary
    return {
        'id': invoice[0],
        'client': {
            'name': client[1],
            'address': client[2],
            'email': client[3],
            'phone': client[4]
        },
        'invoice_number': invoice[2],
        'date_issued': invoice[3],
        'due_date': invoice[4],
        'status': invoice[5],
        'total_amount': invoice[6],
        'vat_exempt': vat_exempt,
        'line_items': items
    }

def update_invoice_status(invoice_number, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE invoices SET status = ? WHERE invoice_number = ?', (new_status, invoice_number))
    conn.commit()
    conn.close()


def update_client(client_id, name, address, email, phone, category):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE clients 
        SET name = ?, address = ?, email = ?, phone = ?, category = ?
        WHERE id = ?
    ''', (name, address, email, phone, category, client_id))
    conn.commit()
    conn.close()

def delete_client(client_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))
    conn.commit()
    conn.close()

def delete_invoice(invoice_id):
    conn = get_connection()
    cursor = conn.cursor()
    # Delete items first
    cursor.execute('DELETE FROM invoice_items WHERE invoice_id = ?', (invoice_id,))
    cursor.execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
    conn.commit()
    conn.close()

def get_invoice_by_id(invoice_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM invoices WHERE id = ?', (invoice_id,))
    invoice = cursor.fetchone()
    
    if not invoice:
        conn.close()
        return None
        
    client_id = invoice[1]
    
    # Check if vat_exempt is in the row (column index 7)
    vat_exempt = False
    if len(invoice) > 7:
        vat_exempt = bool(invoice[7])
    
    cursor.execute('SELECT * FROM invoice_items WHERE invoice_id = ?', (invoice_id,))
    items = cursor.fetchall()
    
    cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
    client = cursor.fetchone()
    
    conn.close()
    
    return {
        'id': invoice[0],
        'client_id': client[0],
        'client': {
            'name': client[1],
            'address': client[2],
            'email': client[3],
            'phone': client[4]
        },
        'invoice_number': invoice[2],
        'date_issued': invoice[3],
        'due_date': invoice[4],
        'status': invoice[5],
        'total_amount': invoice[6],
        'vat_exempt': vat_exempt,
        'line_items': items
    }

def update_invoice(invoice_id, client_id, invoice_number, date_issued, due_date, items, vat_exempt=False):
    conn = get_connection()
    cursor = conn.cursor()
    
    total_amount = sum(item['quantity'] * item['rate'] for item in items)
    
    try:
        # Update Header
        cursor.execute('''
            UPDATE invoices 
            SET client_id=?, invoice_number=?, date_issued=?, due_date=?, total_amount=?, status='Draft', vat_exempt=?
            WHERE id=?
        ''', (client_id, invoice_number, date_issued, due_date, total_amount, vat_exempt, invoice_id))
        
        # Delete old items
        cursor.execute('DELETE FROM invoice_items WHERE invoice_id = ?', (invoice_id,))
        
        # Insert new items
        for item in items:
            amount = item['quantity'] * item['rate']
            cursor.execute('''
                INSERT INTO invoice_items (invoice_id, description, quantity, rate, amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (invoice_id, item['description'], item['quantity'], item['rate'], amount))
            
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_settings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM settings')
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def update_settings(settings_dict):
    conn = get_connection()
    cursor = conn.cursor()
    for key, value in settings_dict.items():
        cursor.execute('REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def get_client_invoice_count(client_id, year=None):
    conn = get_connection()
    cursor = conn.cursor()
    if year:
        # Filter by year. SQLite strftime('%Y', date_column) returns year string
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE client_id = ? AND strftime('%Y', date_issued) = ?", (client_id, str(year)))
    else:
        cursor.execute('SELECT COUNT(*) FROM invoices WHERE client_id = ?', (client_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

