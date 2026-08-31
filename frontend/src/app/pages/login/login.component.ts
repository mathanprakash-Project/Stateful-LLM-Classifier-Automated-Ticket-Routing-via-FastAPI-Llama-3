import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="login-wrapper">
      <div class="login-card animate-scale">
        <div class="brand-logo">
          <div class="brand-row">
            <span class="brand-title">SupportHub</span>
            <span class="brand-badge">AI</span>
          </div>
          <span class="brand-subtitle">Autonomous IT Support & Governance Platform</span>
        </div>
        
        <form (ngSubmit)="onSubmit()" class="login-form">
          <div class="form-group">
            <label class="form-label">Email Address</label>
            <input type="email" class="form-input" [(ngModel)]="email" name="email" required placeholder="name@company.com">
          </div>
          
          <div class="form-group">
            <label class="form-label">Password</label>
            <div class="password-wrapper">
              <input [type]="showPassword ? 'text' : 'password'" class="form-input" [(ngModel)]="password" name="password" required placeholder="••••••••">
              <button type="button" class="icon-btn eye-btn" (click)="showPassword = !showPassword">
                <span class="material-symbols-outlined">{{ showPassword ? 'visibility_off' : 'visibility' }}</span>
              </button>
            </div>
          </div>

          <div *ngIf="error" class="error-msg">
            <span class="material-symbols-outlined">error</span>
            {{ error }}
          </div>

          <button type="submit" class="btn btn-primary btn-login" [disabled]="loading || !email || !password">
            <span *ngIf="loading" class="spinner"></span>
            <span *ngIf="!loading">Sign In</span>
          </button>
        </form>
      </div>
    </div>
  `,
  styles: [`
    .login-wrapper {
      display: grid;
      place-items: center;
      min-height: 100vh;
      background: var(--bg-app);
      color: var(--text-main);
    }
    .login-card {
      width: 100%;
      max-width: 400px;
      padding: 40px;
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-md);
    }
    .brand-logo {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      margin-bottom: 32px;
      text-align: center;
    }
    .logo-icon {
      font-size: 48px;
      color: var(--primary);
      filter: drop-shadow(0 0 12px rgba(var(--primary-rgb), 0.5));
    }
    .brand-row {
      display: flex;
      align-items: center;
      gap: 8px;
      justify-content: center;
    }
    .brand-title {
      font-family: var(--font-heading);
      font-size: 1.6rem;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.02em;
    }
    .brand-badge {
      font-size: 0.8rem;
      background: linear-gradient(135deg, var(--primary), var(--accent));
      color: #fff;
      padding: 2px 8px;
      border-radius: var(--radius-full);
      font-weight: 800;
    }
    .brand-subtitle {
      display: block;
      font-size: 0.85rem;
      color: var(--text-dim);
      margin-top: 4px;
    }
    .login-form {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .form-label {
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--text-dim);
      text-transform: uppercase;
    }
    .form-input {
      width: 100%;
      padding: 12px 16px;
      border-radius: var(--radius-md);
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border);
      color: var(--text-main);
      font-family: inherit;
      font-size: 0.95rem;
      outline: none;
      transition: var(--transition);
    }
    .form-input:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.2);
    }
    .password-wrapper {
      position: relative;
      display: flex;
      align-items: center;
    }
    .eye-btn {
      position: absolute;
      right: 12px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      padding: 4px;
      border-radius: var(--radius-full);
    }
    .eye-btn:hover {
      color: var(--text-main);
    }
    .btn-login {
      width: 100%;
      padding: 14px;
      font-size: 1rem;
      justify-content: center;
      margin-top: 10px;
    }
    .error-msg {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--danger);
      background: rgba(239, 68, 68, 0.1);
      padding: 12px;
      border-radius: var(--radius-md);
      font-size: 0.85rem;
      font-weight: 600;
    }
    .spinner {
      width: 20px;
      height: 20px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      border-top-color: #fff;
      animation: spin 1s ease-in-out infinite;
    }
    .btn-primary {
      background: linear-gradient(135deg, var(--primary), var(--primary-hover));
      color: #fff;
      border: none;
      border-radius: var(--radius-md);
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      transition: var(--transition);
    }
    .btn-primary:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }
    .animate-scale { animation: scaleIn 0.3s ease-out; }
    @keyframes scaleIn { from { opacity: 0; transform: scale(0.96); } to { opacity: 1; transform: scale(1); } }
    @keyframes spin { to { transform: rotate(360deg); } }
  `]
})
export class LoginComponent {
  authService = inject(AuthService);
  router = inject(Router);

  email = '';
  password = '';
  showPassword = false;
  loading = false;
  error = '';

  async onSubmit() {
    this.loading = true;
    this.error = '';
    const res = await this.authService.login(this.email, this.password);
    this.loading = false;
    if (res.success) {
      this.router.navigate(['/dashboard']);
    } else {
      this.error = res.error || 'Login failed';
    }
  }
}
