import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api';
import { Client, Invoice, InvoiceItem } from '../../models/models';

@Component({
  selector: 'app-invoice-form',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './invoice-form.html',
  styleUrl: './invoice-form.css',
})
export class InvoiceForm implements OnInit {
  invoice: Invoice = {
    client_id: 0,
    invoice_number: '',
    date_issued: new Date().toISOString().split('T')[0],
    due_date: '',
    status: 'Draft',
    vat_exempt: false,
    vat_exempt_reason: '',
    items: []
  };
  clients: Client[] = [];
  isEditMode = false;
  defaultReason = '';

  constructor(
    private api: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    // Load clients
    this.api.getClients().subscribe(data => {
      this.clients = data;
      this.cdr.detectChanges();
    });

    // Load settings for default vat reason
    this.api.getSettings().subscribe(settings => {
      this.defaultReason = settings.default_vat_exempt_reason || '';
      this.cdr.detectChanges();
    });

    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.isEditMode = true;
      this.api.getInvoice(+id).subscribe(data => {
        // Map backend response to Invoice model if needed. 
        // Backend returns:
        // { id, client_id, invoice_number, date_issued (str OR Date?), due_date, status, total_amount, vat_exempt, line_items: [tuple] }
        // Wait, `get_invoice_by_id` in app.py returns dict with `line_items` as list of tuples!
        // `(i.id, i.invoice_id, i.description, i.quantity, i.rate, i.amount)`
        // I need to map `line_items` to `items` dict array.

        const backendData: any = data;
        this.invoice = {
          id: backendData.id,
          client_id: backendData.client_id,
          invoice_number: backendData.invoice_number,
          date_issued: this.formatDate(backendData.date_issued), // might be strings or Date objects depending on Flask json encoder
          due_date: this.formatDate(backendData.due_date),
          status: backendData.status,
          vat_exempt: backendData.vat_exempt,
          vat_exempt_reason: backendData.vat_exempt_reason,
          items: backendData.line_items ? backendData.line_items.map((item: any) => ({
            id: item[0],
            invoice_id: item[1],
            description: item[2],
            quantity: item[3],
            rate: item[4],
            amount: item[5]
          })) : []
        };
        this.cdr.detectChanges();
      });
    } else {
      // Set default due date (14 days from now)
      const today = new Date();
      const due = new Date();
      due.setDate(today.getDate() + 14);
      this.invoice.due_date = due.toISOString().split('T')[0];

      // Add one empty item by default
      this.addItem();
    }
  }

  formatDate(dateVal: any): string {
    if (!dateVal) return '';
    // If it's a string like "Fri, 27 Oct 2023 ...", we might need parsing.
    // But Flask jsonify with default encoder usually outputs standard format or if using custom...
    // `app.py`: `inv.date_issued.isoformat()` in list view.
    // `get_invoice_by_id`: returns `invoice.date_issued` directly.
    // Flask `jsonify` handles `date` objects by converting to RFC 1123 string by default? 
    // Or ISO string?
    // Actually `jsonify` might not serialize `date` objects automatically without custom encoder or `isoformat()`.
    // Let's check `app.py` again. `get_invoice_by_id` returns the dict returned by `db_manager.get_invoice_by_id`.
    // `db_manager.get_invoice_by_id` puts `invoice.date_issued` (Date object) into the dict.
    // `jsonify` in `app.py` serializes this.
    // Standard `jsonify` handles datetimes, but usually results in specific format strings.
    // If it's "Fri, 05 Nov ...", we need to convert to "YYYY-MM-DD" for input[type=date].

    const d = new Date(dateVal);
    // Format to YYYY-MM-DD
    return d.toISOString().split('T')[0];
  }

  onClientChange(): void {
    if (!this.invoice.invoice_number && this.invoice.client_id && !this.isEditMode) {
      this.api.getNextInvoiceNumber(this.invoice.client_id).subscribe(data => {
        if (data && data.invoice_number) {
          this.invoice.invoice_number = data.invoice_number;
          this.cdr.detectChanges();
        }
      });
    }
  }

  onVatExemptChange(): void {
    if (this.invoice.vat_exempt && !this.invoice.vat_exempt_reason) {
      this.invoice.vat_exempt_reason = this.defaultReason;
    }
  }

  addItem(): void {
    if (!this.invoice.items) {
      this.invoice.items = [];
    }
    this.invoice.items.push({
      description: '',
      quantity: 1,
      rate: 0
    });
  }

  removeItem(index: number): void {
    if (this.invoice.items) {
      this.invoice.items.splice(index, 1);
    }
  }

  refreshDates(): void {
    const today = new Date();
    const due = new Date();
    due.setDate(today.getDate() + 14);
    this.invoice.date_issued = today.toISOString().split('T')[0];
    this.invoice.due_date = due.toISOString().split('T')[0];
  }

  trackByIndex(index: number, item: any): any {
    return index;
  }

  onSubmit(): void {
    if (this.isEditMode) {
      this.api.updateInvoice(this.invoice.id!, this.invoice).subscribe(() => {
        this.router.navigate(['/dashboard']);
      });
    } else {
      this.api.createInvoice(this.invoice).subscribe(() => {
        this.router.navigate(['/dashboard']);
      });
    }
  }
}
