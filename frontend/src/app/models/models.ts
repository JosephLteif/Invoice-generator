export interface Client {
    id?: number;
    name: string;
    address: string;
    email: string;
    phone: string;
    category: string;
    created_at?: string;
}

export interface InvoiceItem {
    id?: number;
    invoice_id?: number;
    description: string;
    quantity: number;
    rate: number;
    amount?: number;
}

export interface Invoice {
    id?: number;
    client_id: number;
    invoice_number: string;
    date_issued: string;
    due_date: string;
    status: 'Draft' | 'Sent' | 'Paid' | 'Overdue';
    total_amount?: number;
    vat_exempt: boolean;
    vat_exempt_reason?: string;
    client_name?: string; // For dashboard display
    items?: InvoiceItem[];
}

export interface Settings {
    sender_name: string;
    sender_address_line1: string;
    sender_address_line2: string;
    sender_address_line3: string;
    sender_email: string;
    sender_phone: string;
    bank_iban: string;
    bank_account_holder: string;
    bank_swift: string;
    vat_percentage: string;
    tax_id: string;
    default_vat_exempt_reason: string;
    discord_webhook_url: string;
}
