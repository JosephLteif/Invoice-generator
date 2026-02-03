from models import db, Client, Invoice, InvoiceItem, Settings
from sqlalchemy import func, extract
from datetime import datetime

# No manually init_db needed, handled by Migrate/App
def init_db():
    # Helper to check/init default settings if needed
    if Settings.query.count() == 0:
        defaults = {
            "sender_name": "Your Name",
            "sender_address_line1": "Address Line 1",
            "sender_address_line2": "City",
            "sender_address_line3": "Country",
            "sender_email": "email@example.com",
            "sender_phone": "+1 234 567 890",
            "bank_iban": "LB00 0000 0000 0000 0000 0000 0000",
            "bank_branch": "Bank Branch",
            "bank_swift": "SWIFTCODE",
            "vat_percentage": "11"
        }
        for k, v in defaults.items():
            db.session.add(Settings(key=k, value=v))
        db.session.commit()

def add_client(name, address, email, phone, category):
    client = Client(name=name, address=address, email=email, phone=phone, category=category)
    db.session.add(client)
    db.session.commit()

def get_clients():
    # Return list of tuples to match old behavior: (id, name, address, email, phone, category, created_at)
    clients = Client.query.all()
    # Note: ensure order matches table definition in old db_manager if consumed by index
    return [(c.id, c.name, c.address, c.email, c.phone, c.category, c.created_at) for c in clients]

def get_client(client_id):
    c = Client.query.get(client_id)
    if c:
        return (c.id, c.name, c.address, c.email, c.phone, c.category, c.created_at)
    return None

def create_invoice(client_id, invoice_number, date_issued, due_date, items, vat_exempt=False):
    invoice = Invoice(
        client_id=client_id,
        invoice_number=invoice_number,
        date_issued=date_issued,
        due_date=due_date,
        status='Draft',
        # Calculate total
        total_amount=sum(i['quantity'] * i['rate'] for i in items),
        vat_exempt=vat_exempt
    )
    db.session.add(invoice)
    db.session.flush() # get ID
    
    for item_data in items:
        item = InvoiceItem(
            invoice_id=invoice.id,
            description=item_data['description'],
            quantity=item_data['quantity'],
            rate=item_data['rate'],
            amount=item_data['quantity'] * item_data['rate']
        )
        db.session.add(item)
    
    db.session.commit()
    return invoice.id

def get_invoices():
    results = db.session.query(Invoice, Client).join(Client).order_by(Invoice.date_issued.desc()).all()
    
    # Map to tuple structure expected by template
    invoices = []
    for inv, client in results:
        invoices.append((
            inv.id, 
            inv.invoice_number, 
            client.name, 
            inv.date_issued, 
            inv.status, 
            inv.total_amount, 
            inv.vat_exempt
        ))
    return invoices

def get_invoice_details(invoice_number):
    invoice = Invoice.query.filter_by(invoice_number=invoice_number).first()
    if not invoice:
        return None
    
    # Construct dict expected by pdf_builder and templates
    items = []
    for i in invoice.items:
        items.append((i.id, i.invoice_id, i.description, i.quantity, i.rate, i.amount))

    return {
        'id': invoice.id,
        'client': {
            'name': invoice.client.name,
            'address': invoice.client.address,
            'email': invoice.client.email,
            'phone': invoice.client.phone
        },
        'invoice_number': invoice.invoice_number,
        'date_issued': invoice.date_issued,
        'due_date': invoice.due_date,
        'status': invoice.status,
        'total_amount': invoice.total_amount,
        'vat_exempt': invoice.vat_exempt,
        'line_items': items
    }

def update_invoice_status(invoice_number, new_status):
    invoice = Invoice.query.filter_by(invoice_number=invoice_number).first()
    if invoice:
        invoice.status = new_status
        db.session.commit()

def update_client(client_id, name, address, email, phone, category):
    client = Client.query.get(client_id)
    if client:
        client.name = name
        client.address = address
        client.email = email
        client.phone = phone
        client.category = category
        db.session.commit()

def delete_client(client_id):
    client = Client.query.get(client_id)
    if client:
        db.session.delete(client)
        db.session.commit()

def delete_invoice(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if invoice:
        db.session.delete(invoice)
        db.session.commit()

def get_invoice_by_id(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return None
        
    items = []
    for i in invoice.items:
        items.append((i.id, i.invoice_id, i.description, i.quantity, i.rate, i.amount))
    
    return {
        'id': invoice.id,
        'client_id': invoice.client_id,
        'client': {
            'name': invoice.client.name,
            'address': invoice.client.address,
            'email': invoice.client.email,
            'phone': invoice.client.phone
        },
        'invoice_number': invoice.invoice_number,
        'date_issued': invoice.date_issued,
        'due_date': invoice.due_date,
        'status': invoice.status,
        'total_amount': invoice.total_amount,
        'vat_exempt': invoice.vat_exempt,
        'line_items': items
    }

def update_invoice(invoice_id, client_id, invoice_number, date_issued, due_date, items, vat_exempt=False):
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return

    invoice.client_id = client_id
    invoice.invoice_number = invoice_number
    invoice.date_issued = date_issued
    invoice.due_date = due_date
    invoice.total_amount = sum(i['quantity'] * i['rate'] for i in items)
    invoice.status = 'Draft'
    invoice.vat_exempt = vat_exempt
    
    # Replace items: simplest way is delete all and re-add
    for item in invoice.items:
        db.session.delete(item)
    
    for item_data in items:
        new_item = InvoiceItem(
            invoice_id=invoice.id,
            description=item_data['description'],
            quantity=item_data['quantity'],
            rate=item_data['rate'],
            amount=item_data['quantity'] * item_data['rate']
        )
        db.session.add(new_item)
        
    db.session.commit()

def get_settings():
    settings = Settings.query.all()
    return {s.key: s.value for s in settings}

def update_settings(settings_dict):
    for key, value in settings_dict.items():
        setting = Settings.query.get(key)
        if setting:
            setting.value = value
        else:
            db.session.add(Settings(key=key, value=value))
    db.session.commit()

def get_client_invoice_count(client_id, year=None):
    query = Invoice.query.filter_by(client_id=client_id)
    if year:
        query = query.filter(extract('year', Invoice.date_issued) == year)
    
    return query.count()
