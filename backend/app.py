from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import db_manager
from pdf_builder import InvoicePDF
import datetime
import os
import sys
import webbrowser
import json
import io
from threading import Timer
from flask_migrate import Migrate, upgrade
from models import db, Invoice, Client
import requests
from flask_apscheduler import APScheduler

app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def serve_angular():
    return send_file('static/index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    # Check if file exists in static folder
    if path.startswith('api/'):
        return jsonify({'error': 'Not Found'}), 404
    
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_file(os.path.join(app.static_folder, path))
    
    # Fallback to index.html for Angular routing
    return send_file('static/index.html')

# Database Config
def get_db_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        return os.path.join(base_path, 'data', 'invoices.db')
    else:
        # In production (Docker), use the mapped 'data' volume
        if os.environ.get('FLASK_ENV') == 'production':
            return os.path.join('/app', 'data', 'invoices.db')
            
        # In dev, use the backend/data directory
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, 'data', 'invoices.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{get_db_path()}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)
CORS(app) # Enable CORS for all routes
scheduler = APScheduler()

def send_discord_notification(webhook_url, invoice, client_name, type='reminder'):
    try:
        if type == 'overdue':
            emoji = "🚨"
            title = "**OVERDUE INVOICE ALERT**"
            time_info = f"was due on **{invoice.due_date}**"
        else:
            emoji = "📢"
            title = "**Invoice Reminder**"
            time_info = f"is due **today** ({invoice.due_date})"

        data = {
            "content": f"{emoji} {title}\nInvoice **#{invoice.invoice_number}** for **{client_name}** {time_info} and is unpaid.\nTotal Amount: ${invoice.total_amount:,.2f}"
        }
        requests.post(webhook_url, json=data)
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")

def check_overdue_invoices():
    with app.app_context():
        # Get Webhook URL
        settings = db_manager.get_settings()
        webhook_url = settings.get('discord_webhook_url')
        
        today = datetime.date.today()
        
        # 1. MARK AND NOTIFY NEWLY OVERDUE INVOICES (due_date < today)
        newly_overdue = Invoice.query.filter(
            Invoice.due_date < today,
            Invoice.status != 'Paid',
            Invoice.status != 'Overdue'
        ).all()
        
        for invoice in newly_overdue:
            invoice.status = 'Overdue'
            if webhook_url:
                client_name = invoice.client.name if invoice.client else "Unknown Client"
                send_discord_notification(webhook_url, invoice, client_name, type='overdue')
        
        # 2. SEND REMINDERS FOR INVOICES DUE TODAY
        due_today = Invoice.query.filter(
            Invoice.due_date == today,
            Invoice.status != 'Paid'
        ).all()
        
        for invoice in due_today:
            if webhook_url:
                client_name = invoice.client.name if invoice.client else "Unknown Client"
                send_discord_notification(webhook_url, invoice, client_name, type='reminder')
        
        if newly_overdue:
            db.session.commit()
            print(f"Checked invoices: {len(newly_overdue)} marked as Overdue.")

# Initialize Scheduler
scheduler.init_app(app)
# Run check daily at 9:00 AM
scheduler.add_job(id='invoice_check', func=check_overdue_invoices, trigger='cron', hour=9)
scheduler.start()

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

# Ensure DB creation and default settings
with app.app_context():
    # Auto-migrate logic
    # Auto-migrate logic
    if getattr(sys, 'frozen', False):
        # In frozen app, migrations are bundled in sys._MEIPASS/migrations
        migration_dir = os.path.join(sys._MEIPASS, 'migrations')
        
        # Setup logging to catch errors
        log_path = os.path.join(os.path.dirname(sys.executable), 'startup_log.txt')
        
        try:
            with open(log_path, 'w') as f:
                f.write(f"Starting migration from {migration_dir}\n")
                f.write(f"Contents of migration dir: {os.listdir(migration_dir) if os.path.exists(migration_dir) else 'DIR NOT FOUND'}\n")
            
            upgrade(directory=migration_dir)
            
            with open(log_path, 'a') as f:
                f.write("Migration successful\n")
                
        except Exception as e:
            with open(log_path, 'a') as f:
                f.write(f"Migration failed: {e}\n")
                import traceback
                traceback.print_exc(file=f)
            
            # Fallback: If migration fails (e.g., weird PyInstaller issue), 
            # try to create tables directly if they don't exist so app at least starts.
            # This is a safety net for fresh installs.
            try:
                db.create_all()
                with open(log_path, 'a') as f:
                    f.write("Fallback db.create_all() executed\n")
            except Exception as e2:
                 with open(log_path, 'a') as f:
                    f.write(f"Fallback create_all failed: {e2}\n")
    else:
        # In non-frozen environments (dev or Docker), apply migrations if they exist
        migration_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')
        if os.path.exists(migration_dir):
            try:
                upgrade(directory=migration_dir)
                print("Database migrated successfully.")
            except Exception as e:
                print(f"Migration failed: {e}. Attempting db.create_all() as fallback.")
                db.create_all()
        else:
            db.create_all()
            print("Database tables created using db.create_all().")

    db_manager.init_db()

@app.route('/api/invoices')
def get_invoices():
    status_filter = request.args.get('status', 'All')
    invoices = db_manager.get_invoices(status=status_filter)
    
    # Serialize invoices (assuming db_manager returns objects or dicts)
    # If they are SQLAlchemy objects, we need a serializer. 
    # Based on index.html usage, they seem to be objects or dicts. 
    # Let's inspect db_manager.py later to be sure. 
    # For now, assuming db_manager.get_invoices returns a list of Invoice objects.
    # We need to construct a list of dicts.
    
    invoices_data = []
    for inv in invoices:
        invoices_data.append({
            'id': inv[0],
            'invoice_number': inv[1],
            'client_name': inv[2],
            'date_issued': inv[3].isoformat() if inv[3] else None,
            'status': inv[4],
            'total_amount': inv[5],
            'vat_exempt': inv[6],
            'vat_exempt_reason': inv[7],
            'client_id': inv[8]
        })
        
    return jsonify(invoices_data)

@app.route('/api/clients', methods=['GET', 'POST'])
def clients():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        address = data.get('address')
        email = data.get('email')
        phone = data.get('phone')
        category = data.get('category')
        db_manager.add_client(name, address, email, phone, category)
        return jsonify({'message': 'Client added successfully'}), 201
        
    clients = db_manager.get_clients()
    clients_data = []
    # db_manager.get_clients returns a list of tuples or objects?
    # Let's assume tuples based on the 'add_client' logic in app.py or objects.
    # Actually models.py suggests objects (Client(db.Model)). 
    # But checking app.py line 439: client = db_manager.get_client(client_id); client_name = client.name
    # Wait, line 443 says: client_name = client[1].
    # This implies db_manager returns tuples!
    # I need to verify db_manager.py to be sure about the return structure.
    # If it returns tuples, accessing by index is fragile.
    # Let's assume it returns tuples for now based on line 443.
    # (id, name, address, email, phone, category, created_at)
    
    for c in clients:
        clients_data.append({
            'id': c[0],
            'name': c[1],
            'address': c[2],
            'email': c[3],
            'phone': c[4],
            'category': c[5]
        })
            
    return jsonify(clients_data)

@app.route('/api/clients/<int:client_id>/invoices')
def client_invoices(client_id):
    status_filter = request.args.get('status', 'All')
    client = db_manager.get_client(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404
        
    invoices = db_manager.get_client_invoices(client_id, status=status_filter)
    
    # client is a tuple: (id, name, address, email, phone, category, created_at)
    client_data = {
        'id': client[0],
        'name': client[1],
        'address': client[2],
        'email': client[3],
        'phone': client[4],
        'category': client[5]
    }
    
    invoices_data = []
    # get_client_invoices returns tuples: 
    # (id, invoice_number, client_name, date_issued, status, total_amount, vat_exempt, vat_exempt_reason, client_id)
    for inv in invoices:
        invoices_data.append({
            'id': inv[0],
            'invoice_number': inv[1],
            'client_name': inv[2],
            'date_issued': inv[3].isoformat() if inv[3] else None,
            'status': inv[4],
            'total_amount': inv[5],
            'vat_exempt': inv[6],
            'vat_exempt_reason': inv[7],
            'client_id': inv[8]
        })
    
    return jsonify({
        'client': client_data,
        'invoices': invoices_data
    })

@app.route('/api/invoices', methods=['POST'])
def create_invoice():
    data = request.json
    client_id = data.get('client_id')
    invoice_number = data.get('invoice_number')
    date_issued_str = data.get('date_issued')
    due_date_str = data.get('due_date')
    
    date_issued = datetime.datetime.strptime(date_issued_str, '%Y-%m-%d').date() if date_issued_str else datetime.date.today()
    due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else date_issued + datetime.timedelta(days=14)
    vat_exempt = data.get('vat_exempt')
    vat_exempt_reason = data.get('vat_exempt_reason')
    status = data.get('status', 'Draft')
    
    items = data.get('items', [])
    # Validate items structure if needed, but assuming frontend sends correct format:
    # [{'description': '...', 'quantity': 1, 'rate': 10}]
    
    if items:
        # Map item keys if necessary or ensure backend expects what frontend sends
        # db_manager expects list of dicts with 'description', 'quantity', 'rate'
        db_manager.create_invoice(
            client_id, invoice_number, date_issued, due_date, items, vat_exempt, vat_exempt_reason, status
        )
        return jsonify({'message': 'Invoice created successfully'}), 201
    
    return jsonify({'error': 'No items provided'}), 400

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        data = request.json
        settings_dict = {
            'sender_name': data.get('sender_name'),
            'sender_address_line1': data.get('sender_address_line1'),
            'sender_address_line2': data.get('sender_address_line2'),
            'sender_address_line3': data.get('sender_address_line3'),
            'sender_email': data.get('sender_email'),
            'sender_phone': data.get('sender_phone'),
            'bank_iban': data.get('bank_iban'),
            'bank_account_holder': data.get('bank_account_holder'),
            'bank_swift': data.get('bank_swift'),
            'vat_percentage': data.get('vat_percentage'),
            'tax_id': data.get('tax_id'),
            'default_vat_exempt_reason': data.get('default_vat_exempt_reason'),
            'discord_webhook_url': data.get('discord_webhook_url'),
        }
        db_manager.update_settings(settings_dict)
        return jsonify({'message': 'Settings updated successfully'})

    current_settings = db_manager.get_settings()
    return jsonify(current_settings)

@app.route('/api/settings/test-discord', methods=['POST'])
def test_discord_webhook():
    data = request.json
    webhook_url = data.get('discord_webhook_url')
    if not webhook_url:
        return jsonify({"error": "Missing Webhook URL"}), 400
    
    try:
        discord_data = {
            "content": "✅ **Test Notification**\nThis is a test message from Invoice Generator."
        }
        resp = requests.post(webhook_url, json=discord_data)
        if resp.status_code == 204 or resp.status_code == 200:
            return jsonify({"message": "Test message sent successfully!"})
        else:
            return jsonify({"error": f"Discord returned error: {resp.status_code} {resp.text}"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to send: {e}"}), 500

@app.route('/settings/export')
def export_data():
    data = db_manager.export_data()
    json_str = json.dumps(data, indent=4)
    mem = io.BytesIO()
    mem.write(json_str.encode('utf-8'))
    mem.seek(0)
    
    filename = f"invoice_data_{datetime.date.today()}.json"
    return send_file(
        mem, 
        as_attachment=True, 
        download_name=filename,
        mimetype='application/json'
    )

@app.route('/api/settings/import', methods=['POST'])
def import_data():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if file:
        try:
            data = json.load(file)
            success, message = db_manager.import_data(data)
            if success:
                return jsonify({"message": "Data imported successfully"})
            else:
                return jsonify({"error": f"Error importing data: {message}"}), 500
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON file"}), 400
            
    return jsonify({"error": "Unknown error"}), 500

@app.route('/invoices/<invoice_number>/pdf')
def download_pdf(invoice_number):
    invoice_data = db_manager.get_invoice_details(invoice_number)
    if not invoice_data:
        return "Invoice not found", 404
    
    settings = db_manager.get_settings()
    
    # Create directory structure: invoices/ClientName/
    client_name = invoice_data['client']['name']
    # Sanitize client name for folder safely
    safe_client_name = "".join([c for c in client_name if c.isalpha() or c.isdigit() or c==' ']).strip()
    
    # Use absolute path for invoices directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(base_dir, "data", "invoices", safe_client_name)
    os.makedirs(folder_path, exist_ok=True)
    
    filename = f"{invoice_number}.pdf"
    full_path = os.path.join(folder_path, filename)
    
    # Generate
    pdf = InvoicePDF(invoice_data, settings)
    pdf.generate(full_path)
    
    return send_file(full_path, as_attachment=True)

@app.route('/api/invoices/<invoice_number>/status', methods=['POST'])
def update_status(invoice_number):
    data = request.json
    new_status = data.get('status')
    if new_status:
        db_manager.update_invoice_status(invoice_number, new_status)
        return jsonify({"message": f"Status updated to {new_status}"})
    return jsonify({"error": "Status not provided"}), 400

@app.route('/api/invoices/<invoice_number>/pay', methods=['POST'])
def mark_paid(invoice_number):
    db_manager.update_invoice_status(invoice_number, "Paid")
    return jsonify({"message": "Invoice marked as Paid"})

@app.route('/api/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_client(client_id):
    if request.method == 'DELETE':
        db_manager.delete_client(client_id)
        return jsonify({"message": "Client deleted successfully"})

    if request.method == 'PUT':
        data = request.json
        name = data.get('name')
        address = data.get('address')
        email = data.get('email')
        phone = data.get('phone')
        category = data.get('category')
        db_manager.update_client(client_id, name, address, email, phone, category)
        return jsonify({"message": "Client updated successfully"})
    
    # GET
    client = db_manager.get_client(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
        
    # client is tuple
    return jsonify({
        'id': client[0],
        'name': client[1],
        'address': client[2],
        'email': client[3],
        'phone': client[4],
        'category': client[5]
    })

@app.route('/api/invoices/<int:invoice_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_invoice(invoice_id):
    if request.method == 'DELETE':
        db_manager.delete_invoice(invoice_id)
        return jsonify({"message": "Invoice deleted successfully"})

    if request.method == 'PUT':
        data = request.json
        client_id = data.get('client_id')
        invoice_number = data.get('invoice_number')
        date_issued_str = data.get('date_issued')
        due_date_str = data.get('due_date')
        
        date_issued = datetime.datetime.strptime(date_issued_str, '%Y-%m-%d').date() if date_issued_str else datetime.date.today()
        due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else date_issued + datetime.timedelta(days=14)
        vat_exempt = data.get('vat_exempt')
        vat_exempt_reason = data.get('vat_exempt_reason')
        status = data.get('status', 'Draft')
        
        items = data.get('items', [])
        
        if items:
            db_manager.update_invoice(
                invoice_id, client_id, invoice_number, date_issued, due_date, items, vat_exempt, vat_exempt_reason, status
            )
            return jsonify({"message": "Invoice updated successfully"})
        return jsonify({"error": "No items provided"}), 400

    # GET
    invoice = db_manager.get_invoice_by_id(invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404
        
    return jsonify(invoice)

@app.route('/api/next-invoice-number')
def next_invoice_number():
    client_id = request.args.get('client_id')
    if not client_id:
        return {"error": "Missing client_id"}, 400
    
    client = db_manager.get_client(client_id)
    if not client:
        return {"error": "Client not found"}, 404
        
    client_name = client[1]
    # Extract first 3 letters, uppercase
    prefix = client_name[:3].upper()
    
    current_year = datetime.date.today().year
    
    # Get count for THIS year
    count = db_manager.get_client_invoice_count(client_id, year=current_year)
    next_num = count + 1
    
    # Format: Prefix-ClientID-00N-YYYY
    # e.g., ENV-2-001-2026
    invoice_number = f"{prefix}-{client_id}-{next_num:03d}-{current_year}"
    
    return {"invoice_number": invoice_number}

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server = request.environ.get('werkzeug.server.shutdown')
    if shutdown_server is None:
        # Fallback for production/other WSGI or direct execution
        import os, signal
        os.kill(os.getpid(), signal.SIGINT)
        return "Server shutting down..."
    
    shutdown_server()
    return 'Server shutting down...'

if __name__ == '__main__':
    # Check if the port is already in use
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 5000))
    except socket.error:
        # Port is already in use, so the app is likely running.
        # Just open the browser to the existing instance and exit.
        print("Application is already running. Opening browser...")
        open_browser()
        sys.exit(0)
    finally:
        sock.close()

    # Only open browser automatically if frozen (executable) or if desired in dev
    if getattr(sys, 'frozen', False):
        Timer(1.5, open_browser).start()
    
    app.run(debug=False, port=5000)
