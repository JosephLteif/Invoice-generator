from flask import Flask, render_template, request, redirect, url_for, send_file
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
from models import db

# Adjust template_folder and static_folder for PyInstaller
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)

app.secret_key = 'super_secret_key_for_invoices_123'

# Database Config
def get_db_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        return os.path.join(base_path, 'invoices.db')
    else:
        # In production (Docker), use the instance folder which is volume-mapped
        if os.environ.get('FLASK_ENV') == 'production':
            # Ensure instance path exists
            os.makedirs(app.instance_path, exist_ok=True)
            return os.path.join(app.instance_path, 'invoices.db')
            
        # In dev, use the local directory (or instance if desired, but user has data in root)
        base_path = os.path.dirname(os.path.abspath(__file__))
        # Check if instance db exists, else use root. 
        # Actually, for simplicity and to match the user's existing "invoices.db" in root:
        return os.path.join(base_path, 'invoices.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{get_db_path()}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

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

@app.route('/')
def dashboard():
    invoices = db_manager.get_invoices()
    return render_template('index.html', invoices=invoices)

@app.route('/clients', methods=['GET', 'POST'])
def clients():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        email = request.form.get('email')
        phone = request.form.get('phone')
        category = request.form.get('category')
        db_manager.add_client(name, address, email, phone, category)
        return redirect(url_for('clients'))
    
    clients = db_manager.get_clients()
    return render_template('clients.html', clients=clients)

@app.route('/invoices/new', methods=['GET', 'POST'])
def create_invoice():
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        invoice_number = request.form.get('invoice_number')
        date_issued_str = request.form.get('date_issued')
        due_date_str = request.form.get('due_date')
        
        date_issued = datetime.datetime.strptime(date_issued_str, '%Y-%m-%d').date() if date_issued_str else datetime.date.today()
        due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else date_issued + datetime.timedelta(days=14)
        vat_exempt = request.form.get('vat_exempt') == 'true'
        
        # Process Items
        descriptions = request.form.getlist('description[]')
        quantities = request.form.getlist('quantity[]')
        rates = request.form.getlist('rate[]')
        
        items = []
        for i in range(len(descriptions)):
            if descriptions[i]: # Only add if description is present
                items.append({
                    'description': descriptions[i],
                    'quantity': float(quantities[i]),
                    'rate': float(rates[i])
                })
        
        if items:
            db_manager.create_invoice(
                client_id, invoice_number, date_issued, due_date, items, vat_exempt
            )
            return redirect(url_for('dashboard'))
            
    clients = db_manager.get_clients()
    return render_template('create_invoice.html', clients=clients, today=datetime.date.today())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        settings_dict = {
            'sender_name': request.form.get('sender_name'),
            'sender_address_line1': request.form.get('sender_address_line1'),
            'sender_address_line2': request.form.get('sender_address_line2'),
            'sender_address_line3': request.form.get('sender_address_line3'),
            'sender_email': request.form.get('sender_email'),
            'sender_phone': request.form.get('sender_phone'),
            'bank_iban': request.form.get('bank_iban'),
            'bank_account_holder': request.form.get('bank_account_holder'),
            'bank_swift': request.form.get('bank_swift'),
            'vat_percentage': request.form.get('vat_percentage'),
            'tax_id': request.form.get('tax_id'),
        }
        db_manager.update_settings(settings_dict)
        return redirect(url_for('settings'))

    current_settings = db_manager.get_settings()
    return render_template('settings.html', settings=current_settings)

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

@app.route('/settings/import', methods=['POST'])
def import_data():
    if 'file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No file selected", 400
        
    if file:
        try:
            data = json.load(file)
            success, message = db_manager.import_data(data)
            if success:
                return redirect(url_for('settings'))
            else:
                return f"Error importing data: {message}", 500
        except json.JSONDecodeError:
            return "Invalid JSON file", 400
            
    return redirect(url_for('settings'))

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
    folder_path = os.path.join(base_dir, "invoices", safe_client_name)
    os.makedirs(folder_path, exist_ok=True)
    
    filename = f"{invoice_number}.pdf"
    full_path = os.path.join(folder_path, filename)
    
    # Generate
    pdf = InvoicePDF(invoice_data, settings)
    pdf.generate(full_path)
    
    return send_file(full_path, as_attachment=True)

@app.route('/invoices/<invoice_number>/pay')
def mark_paid(invoice_number):
    db_manager.update_invoice_status(invoice_number, "Paid")
    return redirect(url_for('dashboard'))

@app.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
def edit_client(client_id):
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        email = request.form.get('email')
        phone = request.form.get('phone')
        category = request.form.get('category')
        db_manager.update_client(client_id, name, address, email, phone, category)
        return redirect(url_for('clients'))
    
    client = db_manager.get_client(client_id)
    return render_template('edit_client.html', client=client)

@app.route('/clients/<int:client_id>/delete')
def delete_client(client_id):
    db_manager.delete_client(client_id)
    return redirect(url_for('clients'))

@app.route('/invoices/<int:invoice_id>/delete')
def delete_invoice(invoice_id):
    db_manager.delete_invoice(invoice_id)
    return redirect(url_for('dashboard'))

@app.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
def edit_invoice(invoice_id):
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        invoice_number = request.form.get('invoice_number')
        date_issued_str = request.form.get('date_issued')
        due_date_str = request.form.get('due_date')
        
        date_issued = datetime.datetime.strptime(date_issued_str, '%Y-%m-%d').date() if date_issued_str else datetime.date.today()
        due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else date_issued + datetime.timedelta(days=14)
        vat_exempt = request.form.get('vat_exempt') == 'true'
        
        descriptions = request.form.getlist('description[]')
        quantities = request.form.getlist('quantity[]')
        rates = request.form.getlist('rate[]')
        
        items = []
        for i in range(len(descriptions)):
            if descriptions[i]: 
                items.append({
                    'description': descriptions[i],
                    'quantity': float(quantities[i]),
                    'rate': float(rates[i])
                })
        
        if items:
            db_manager.update_invoice(
                invoice_id, client_id, invoice_number, date_issued, due_date, items, vat_exempt
            )
            return redirect(url_for('dashboard'))

    invoice = db_manager.get_invoice_by_id(invoice_id)
    clients = db_manager.get_clients()
    return render_template('edit_invoice.html', invoice=invoice, clients=clients)

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
