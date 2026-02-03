# Invoice Generator

A simple and efficient Invoice Generator built with Python and Flask. Designed to create professional PDF invoices with support for client management, VAT handling, and export services.

## Features

- **Client Management**: Add, edit, and list clients.
- **Invoice Creation**: Create invoices with multiple line items.
- **Auto-Numbering**: Intelligent invoice numbering based on client and year.
- **PDF Generation**: Generate professional PDF invoices ready to send.
- **VAT Handling**: Configurable VAT percentage.
- **Export Services**: Special "VAT 0%" mode for export services with required legal notices.
- **Dashboard**: Track invoice status (Draft, Paid).

## Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd Invoice-generator
    ```

2.  **Create a virtual environment** (optional but recommended):
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application**:
    ```bash
    python app.py
    ```

5.  **Open in Browser**:
    Go to `http://127.0.0.1:5000`

## Configuration

When you first run the application, verify your settings:
1.  Go to the **Settings** page in the nav bar.
2.  Update your **Sender Information** (Name, Address, Email).
3.  Update your **Bank Details** (IBAN, Swift, Account Holder).

## Technologies

- **Flask**: Web framework.
- **SQLite**: Database.
- **ReportLab**: PDF generation.
- **HTML/CSS**: Frontend.

## License

[MIT License](LICENSE)
