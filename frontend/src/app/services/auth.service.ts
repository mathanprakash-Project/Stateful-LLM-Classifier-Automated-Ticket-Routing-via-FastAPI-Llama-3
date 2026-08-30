import { Injectable, signal, computed } from '@angular/core';
import { Router } from '@angular/router';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  roles: string[];
  permissions: string[];
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private _token = signal<string | null>(sessionStorage.getItem('access_token'));
  private _user = signal<AuthUser | null>(null);

  token = this._token.asReadonly();
  user = this._user.asReadonly();
  isAuthenticated = computed(() => !!this._token());
  userRole = computed(() => (this._user()?.roles?.[0] ?? 'user').toLowerCase());
  isAdmin = computed(() => this.userRole() === 'admin');
  isManager = computed(() => this.userRole() === 'manager' || this.userRole() === 'admin');
  isAgent = computed(() => this.userRole() === 'agent' || this.userRole() === 'manager' || this.userRole() === 'admin');

  constructor(private router: Router) {
    if (this._token()) {
      this.loadProfile();
    }
  }

  async login(email: string, password: string): Promise<{ success: boolean; error?: string }> {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      if (!res.ok) {
        const err = await res.json();
        return { success: false, error: err.error?.message || 'Invalid credentials' };
      }
      const data = await res.json();
      this._token.set(data.access_token);
      sessionStorage.setItem('access_token', data.access_token);
      
      this._user.set({
        id: data.user?.id || 'id1',
        email: data.user?.email || email,
        name: data.user?.full_name || email,
        roles: (data.user?.roles || ['user']).map((r: string) => r.toLowerCase()),
        permissions: []
      });
      await this.loadProfile();
      return { success: true };
    } catch (e: any) {
      return { success: false, error: 'Network error. Please try again.' };
    }
  }

  async loadProfile(): Promise<void> {
    try {
      const res = await fetch('/api/auth/me', {
        headers: this.getAuthHeaders()
      });
      if (res.ok) {
        const profile = await res.json();
        this._user.set({
          id: profile.id,
          email: profile.email,
          name: profile.full_name,
          roles: (profile.roles || ['user']).map((r: string) => r.toLowerCase()),
          permissions: profile.permissions || []
        });
      } else if (res.status === 401) {
        this.logout();
      }
    } catch (e) {
      // Silent fail
    }
  }

  logout(): void {
    this._token.set(null);
    this._user.set(null);
    sessionStorage.removeItem('access_token');
    this.router.navigate(['/login']);
  }

  getAuthHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
      ...(this._token() ? { 'Authorization': `Bearer ${this._token()}` } : {})
    };
  }
}
