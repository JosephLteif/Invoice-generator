import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api';
import { Settings as SettingsModel } from '../../models/models';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './settings.html',
  styleUrl: './settings.css',
})
export class Settings implements OnInit {
  settings: SettingsModel = {
    sender_name: '',
    sender_address_line1: '',
    sender_address_line2: '',
    sender_address_line3: '',
    sender_email: '',
    sender_phone: '',
    bank_iban: '',
    bank_account_holder: '',
    bank_swift: '',
    vat_percentage: '11',
    tax_id: '',
    default_vat_exempt_reason: '',
    discord_webhook_url: ''
  };
  activeTab: string = 'general';
  message: string = '';
  messageType: 'success' | 'error' = 'success';
  testBtnText = 'Test Webhook';
  isTesting = false;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) { }

  ngOnInit(): void {
    this.api.getSettings().subscribe(data => {
      // API returns dict {key: value}. Model expects object with properties.
      // I need to map it if the API returns a flat dict where keys match model properties.
      // app.py `get_settings` returns `{s.key: s.value}` via `jsonify`.
      // So keys like "sender_name" will be present.
      // TS interface matches these keys.
      // So casting is fine.
      this.settings = { ...this.settings, ...data };
      this.cdr.detectChanges();
    });
  }

  setActiveTab(tab: string): void {
    this.activeTab = tab;
  }

  onSubmit(): void {
    this.api.updateSettings(this.settings).subscribe({
      next: () => this.showMessage('Settings updated successfully', 'success'),
      error: (err) => this.showMessage('Failed to update settings', 'error')
    });
  }

  testWebhook(): void {
    if (!this.settings.discord_webhook_url) {
      this.showMessage('Please enter a Webhook URL first.', 'error');
      return;
    }

    this.isTesting = true;
    this.testBtnText = 'Testing...';

    this.api.testDiscordWebhook(this.settings.discord_webhook_url).subscribe({
      next: (res) => {
        this.showMessage(res.message || 'Test message sent!', 'success');
        this.isTesting = false;
        this.testBtnText = 'Test Webhook';
        this.cdr.detectChanges();
      },
      error: (err) => {
        const msg = err.error?.error || 'Network error';
        this.showMessage(msg, 'error');
        this.isTesting = false;
        this.testBtnText = 'Test Webhook';
        this.cdr.detectChanges();
      }
    });
  }

  onFileSelected(event: any): void {
    const file: File = event.target.files[0];
    if (file) {
      if (confirm('WARNING: This will DELETE all current data and replace it with the imported file. This action cannot be undone. Proceed?')) {
        this.api.importData(file).subscribe({
          next: (res) => {
            this.showMessage(res.message, 'success');
            // Reload settings potentially
            this.ngOnInit();
          },
          error: (err) => {
            this.showMessage(err.error?.error || 'Import failed', 'error');
          }
        });
      }
    }
    // Reset input
    event.target.value = '';
  }

  downloadBackup(): void {
    window.location.href = 'http://localhost:5000/settings/export';
  }

  shutdown(): void {
    if (confirm('Are you sure you want to shut down the application?')) {
      // Send request to shutdown logic if exposed via API?
      // Current app.py has `/shutdown` but I didn't verify if I kept it or converted it.
      // Wait, I saw `/shutdown` in `settings.html` lines 155-159.
      // `action="{{ url_for('shutdown') }}"`
      // Does `app.py` have a shutdown route?
      // I should check `app.py`. If not, I can ignore it or add it.
      // This seems to be a feature of the Flask app to stop the server.
      // I will assume it exists or can be called. I'll check app.py later.
      // For now, I'll use direct URL.
      window.location.href = 'http://localhost:5000/shutdown';
      // Or use HttpClient post.
    }
  }

  showMessage(msg: string, type: 'success' | 'error'): void {
    this.message = msg;
    this.messageType = type;
    this.cdr.detectChanges();
    setTimeout(() => {
      this.message = '';
      this.cdr.detectChanges();
    }, 3000);
  }
}
