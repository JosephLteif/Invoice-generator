from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String)
    email = db.Column(db.String)
    phone = db.Column(db.String)
    category = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    invoices = db.relationship('Invoice', backref='client', lazy=True)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    invoice_number = db.Column(db.String, unique=True, nullable=False)
    date_issued = db.Column(db.Date)
    due_date = db.Column(db.Date)
    status = db.Column(db.String, default='Draft')
    total_amount = db.Column(db.Float)
    vat_exempt = db.Column(db.Boolean, default=False)
    vat_exempt_reason = db.Column(db.String)
    
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade="all, delete-orphan")

class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    description = db.Column(db.String)
    quantity = db.Column(db.Float)
    rate = db.Column(db.Float)
    amount = db.Column(db.Float)

class Settings(db.Model):
    __tablename__ = 'settings'
    key = db.Column(db.String, primary_key=True)
    value = db.Column(db.String)
