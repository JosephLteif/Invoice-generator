import sys
import datetime
import db_manager
from pdf_builder import InvoicePDF

def print_menu():
    print("\n--- Invoice Generator ---")
    print("1. Add Client")
    print("2. List Clients")
    print("3. Create Invoice")
    print("4. List Invoices")
    print("5. Generate PDF for Invoice")
    print("6. Mark Invoice as Paid")
    print("7. Exit")
    print("-------------------------")

def add_client_flow():
    print("\n[Add Client]")
    name = input("Name: ")
    address = input("Address (use \\n for newlines): ").replace("\\n", "\n")
    email = input("Email: ")
    phone = input("Phone: ")
    category = input("Category (e.g., Corporate, Personal): ")
    
    db_manager.add_client(name, address, email, phone, category)
    print("Client added successfully!")

def list_clients_flow():
    print("\n[List Clients]")
    clients = db_manager.get_clients()
    for c in clients:
        print(f"ID: {c[0]} | Name: {c[1]} | Category: {c[5]}")

def create_invoice_flow():
    print("\n[Create Invoice]")
    # Select Client
    list_clients_flow()
    try:
        client_id = int(input("Enter Client ID: "))
    except ValueError:
        print("Invalid Client ID")
        return

    # Basic Info
    invoice_number = input("Invoice Number (e.g., INV-001): ")
    date_str = input("Date Issued (YYYY-MM-DD) [Today]: ")
    if not date_str:
        date_issued = datetime.date.today()
    else:
        date_issued = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    
    due_str = input("Due Date (YYYY-MM-DD) [14 days from now]: ")
    if not due_str:
        due_date = date_issued + datetime.timedelta(days=14)
    else:
        due_date = datetime.datetime.strptime(due_str, "%Y-%m-%d").date()

    # Items
    items = []
    print("Enter items (leave Description empty to finish):")
    while True:
        desc = input("Description: ")
        if not desc:
            break
        try:
            qty = float(input("Quantity: "))
            rate = float(input("Rate: "))
            items.append({
                "description": desc,
                "quantity": qty,
                "rate": rate
            })
        except ValueError:
            print("Invalid number format, try again.")
    
    if items:
        db_manager.create_invoice(
            client_id, invoice_number, date_issued, due_date, items
        )
        print("Invoice created successfully!")
    else:
        print("No items added. Invoice cancelled.")

def list_invoices_flow():
    print("\n[List Invoices]")
    invoices = db_manager.get_invoices()
    for inv in invoices:
        # id, number, client_name, date, status, total
        print(f"#{inv[1]} | {inv[2]} | {inv[3]} | {inv[4]} | ${inv[5]:.2f}")

def generate_pdf_flow():
    print("\n[Generate PDF]")
    invoice_number = input("Enter Invoice Number: ")
    invoice_data = db_manager.get_invoice_details(invoice_number)
    
    if invoice_data:
        filename = f"Invoice_{invoice_number}.pdf"
        pdf = InvoicePDF(invoice_data)
        pdf.generate(filename)
        print(f"PDF generated: {filename}")
    else:
        print("Invoice not found.")

def mark_paid_flow():
    print("\n[Mark Paid]")
    invoice_number = input("Enter Invoice Number: ")
    db_manager.update_invoice_status(invoice_number, "Paid")
    print(f"Invoice {invoice_number} marked as Paid.")

def main():
    db_manager.init_db()
    
    while True:
        print_menu()
        choice = input("Select an option: ")
        
        if choice == '1':
            add_client_flow()
        elif choice == '2':
            list_clients_flow()
        elif choice == '3':
            create_invoice_flow()
        elif choice == '4':
            list_invoices_flow()
        elif choice == '5':
            generate_pdf_flow()
        elif choice == '6':
            mark_paid_flow()
        elif choice == '7':
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
