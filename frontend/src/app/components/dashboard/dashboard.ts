import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api';
import { Invoice } from '../../models/models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit {
  invoices: Invoice[] = [];
  statusFilter: string = 'All';
  statuses: string[] = ['All', 'Draft', 'Paid', 'Sent', 'Overdue'];

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) { }

  ngOnInit(): void {
    const params = new URLSearchParams(window.location.search);
    const status = params.get('status');
    if (status) {
      this.statusFilter = status;
    }
    this.loadInvoices();
  }

  loadInvoices(): void {
    this.api.getInvoices(this.statusFilter).subscribe(data => {
      this.invoices = data;
      this.cdr.detectChanges();
    });
  }

  onFilterChange(): void {
    // Update URL without reloading? Or just load data.
    // For now, simple load.
    this.loadInvoices();
  }

  updateStatus(invoice: Invoice, newStatus: string): void {
    if (invoice.invoice_number) {
      this.api.updateInvoiceStatus(invoice.invoice_number, newStatus).subscribe(() => {
        invoice.status = newStatus as any;
      });
    }
  }

  deleteInvoice(id: number): void {
    if (confirm('Are you sure you want to delete this invoice?')) {
      this.api.deleteInvoice(id).subscribe(() => {
        this.invoices = this.invoices.filter(i => i.id !== id);
      });
    }
  }
}
