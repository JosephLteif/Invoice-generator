import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api';
import { Client } from '../../models/models';

@Component({
  selector: 'app-client-form',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './client-form.html',
  styleUrl: './client-form.css',
})
export class ClientForm implements OnInit {
  client: Client = {
    name: '',
    address: '',
    email: '',
    phone: '',
    category: ''
  };
  isEditMode = false;

  constructor(
    private api: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.isEditMode = true;
      this.api.getClient(+id).subscribe(data => {
        // Backend returns tuple for getClient: (id, name, address, email, phone, category, created_at)
        // I need to map it to object if ApiService doesn't do it.
        // Wait, app.py get_client returns tuple?
        // Yes: `return (c.id, c.name, ...)`
        // My ApiService.getClient returns `Observable<Client>`.
        // If backend returns tuple, Angular HttpClient will return array.
        // I should transform it or fix backend to return dict.
        // I fixed `get_clients` loop in `app.py` to handle both, but `get_client` (singular) logic in `manage_client` route (lines 411-427 in app.py) returns JSON dict!
        // "client is tuple ... return jsonify({...})"
        // So `manage_client` returns a DICT.
        // Perfect. ApiService will receive a dict matching Client interface.
        this.client = data;
        this.cdr.detectChanges();
      });
    }
  }

  onSubmit(): void {
    if (this.isEditMode) {
      this.api.updateClient(this.client.id!, this.client).subscribe(() => {
        this.router.navigate(['/clients']);
      });
    } else {
      this.api.createClient(this.client).subscribe(() => {
        this.router.navigate(['/clients']);
      });
    }
  }
}
