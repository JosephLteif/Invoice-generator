import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Client, Invoice, Settings } from '../models/models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = '/api';

  constructor(private http: HttpClient) { }

  // Invoices
  getInvoices(status: string = 'All'): Observable<Invoice[]> {
    return this.http.get<Invoice[]>(`${this.apiUrl}/invoices?status=${status}`);
  }

  getInvoice(id: number): Observable<Invoice> {
    return this.http.get<Invoice>(`${this.apiUrl}/invoices/${id}`);
  }

  createInvoice(invoice: Invoice): Observable<any> {
    return this.http.post(`${this.apiUrl}/invoices`, invoice);
  }

  updateInvoice(id: number, invoice: Invoice): Observable<any> {
    return this.http.put(`${this.apiUrl}/invoices/${id}`, invoice);
  }

  deleteInvoice(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/invoices/${id}`);
  }

  updateInvoiceStatus(invoiceNumber: string, status: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/invoices/${invoiceNumber}/status`, { status });
  }

  markInvoicePaid(invoiceNumber: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/invoices/${invoiceNumber}/pay`, {});
  }

  getNextInvoiceNumber(clientId: number): Observable<{ invoice_number: string }> {
    return this.http.get<{ invoice_number: string }>(`${this.apiUrl}/next-invoice-number?client_id=${clientId}`);
  }

  // Clients
  getClients(): Observable<Client[]> {
    return this.http.get<Client[]>(`${this.apiUrl}/clients`);
  }

  getClient(id: number): Observable<Client> {
    return this.http.get<Client>(`${this.apiUrl}/clients/${id}`);
  }

  createClient(client: Client): Observable<any> {
    return this.http.post(`${this.apiUrl}/clients`, client);
  }

  updateClient(id: number, client: Client): Observable<any> {
    return this.http.put(`${this.apiUrl}/clients/${id}`, client);
  }

  deleteClient(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/clients/${id}`);
  }

  getClientInvoices(clientId: number, status: string = 'All'): Observable<{ client: Client, invoices: Invoice[] }> {
    return this.http.get<{ client: Client, invoices: Invoice[] }>(`${this.apiUrl}/clients/${clientId}/invoices?status=${status}`);
  }

  // Settings
  getSettings(): Observable<Settings> {
    return this.http.get<Settings>(`${this.apiUrl}/settings`);
  }

  updateSettings(settings: Settings): Observable<any> {
    return this.http.post(`${this.apiUrl}/settings`, settings); // Backend uses POST for update based on implementation
  }

  testDiscordWebhook(webhookUrl: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/settings/test-discord`, { discord_webhook_url: webhookUrl });
  }

  importData(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/settings/import`, formData);
  }
}
