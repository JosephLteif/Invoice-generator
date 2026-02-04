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

4.  **Initialize the Database**:
    ```bash
    # Initialize the database migration repository (if not exists)
    flask db init 
    
    # Generate migration script (if models changed)
    flask db migrate -m "Initial migration"
    
    # Apply migrations
    flask db upgrade
    ```

5.  **Run the application**:
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

## Building an Executable

To create a standalone executable for distribution:

1.  **Install PyInstaller** (if not already installed):
    ```bash
    pip install pyinstaller
    ```

2.  **Build the Executable**:
    Run the following command in the project root:
    ```bash
    python -m PyInstaller --name "InvoiceGenerator" --onefile --windowed --add-data "templates;templates" --add-data "static;static" --add-data "migrations;migrations" app.py
    ```

3.  **Locate the Output**:
    The executable will be generated in the `dist` folder:
    `dist\InvoiceGenerator.exe`

4.  **Distribution**:
    You can zip and send `InvoiceGenerator.exe`. It does not require Python to be installed on the target machine.

## Docker Deployment

To build and push the Docker image to Docker Hub manually:

1.  **Build the image**:
    ```bash
    docker-compose build
    ```

2.  **Tag the image**:
    ```bash
    docker tag invoice-generator-app:latest josephlteif/invoice-generator:latest
    ```

3.  **Push to Docker Hub**:
    ```bash
    docker push josephlteif/invoice-generator:latest
    ```

4.  **On your Server**:
    - Update your Portainer stack or run `docker pull josephlteif/invoice-generator:latest`.
    - Restart the container.
