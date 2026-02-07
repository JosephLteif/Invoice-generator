import { Routes } from '@angular/router';
import { Dashboard } from './components/dashboard/dashboard';
import { ClientList } from './components/client-list/client-list';
import { ClientForm } from './components/client-form/client-form';
import { InvoiceForm } from './components/invoice-form/invoice-form';
import { Settings } from './components/settings/settings';

export const routes: Routes = [
    { path: 'dashboard', component: Dashboard },
    { path: 'clients', component: ClientList },
    { path: 'clients/new', component: ClientForm },
    { path: 'clients/:id/edit', component: ClientForm },
    { path: 'clients/:id/invoices', component: ClientList }, // Use ClientList for client invoices view
    { path: 'invoices/new', component: InvoiceForm },
    { path: 'invoices/:id/edit', component: InvoiceForm },
    { path: 'settings', component: Settings },
    { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
];
