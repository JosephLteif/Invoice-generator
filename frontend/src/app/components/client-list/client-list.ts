import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api';
import { Client, Invoice } from '../../models/models';

@Component({
  selector: 'app-client-list',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './client-list.html',
  styleUrl: './client-list.css',
})
export class ClientList implements OnInit {
  clients: Client[] = [];
  client: Client | null = null;
  clientInvoices: Invoice[] = [];
  viewMode: 'list' | 'details' = 'list';
  statusFilter: string = 'All';
  statuses: string[] = ['All', 'Draft', 'Paid', 'Sent', 'Overdue'];

  constructor(
    private api: ApiService,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.viewMode = 'details';
        this.loadClientDetails(+id);
      } else {
        this.viewMode = 'list';
        this.loadClients();
      }
    });

    this.route.queryParams.subscribe(params => {
      if (params['status']) {
        this.statusFilter = params['status'];
        if (this.viewMode === 'details' && this.client) {
          this.loadClientInvoices(this.client.id!);
        }
      }
    });
  }

  loadClients(): void {
    this.api.getClients().subscribe(data => {
      this.clients = data;
      this.cdr.detectChanges();
    });
  }

  loadClientDetails(id: number): void {
    this.loadClientInvoices(id);
  }

  loadClientInvoices(id: number): void {
    this.api.getClientInvoices(id, this.statusFilter).subscribe(data => {
      this.client = data.client;
      this.clientInvoices = data.invoices;
      this.cdr.detectChanges();
    });
  }

  onFilterChange(): void {
    if (this.client) {
      this.loadClientInvoices(this.client.id!);
    }
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
        this.clientInvoices = this.clientInvoices.filter(i => i.id !== id);
      });
    }
  }

  deleteClient(id: number): void {
    if (confirm('Are you sure you want to delete this client?')) {
      this.api.deleteClient(id).subscribe(() => {
        this.clients = this.clients.filter(c => c.id !== id);
      });
    }
  }
}
