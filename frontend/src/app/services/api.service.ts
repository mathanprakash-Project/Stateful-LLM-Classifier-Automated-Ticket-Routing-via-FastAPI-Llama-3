import { Injectable, inject } from '@angular/core';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private authService = inject(AuthService);

  private async fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
    const headers = this.authService.getAuthHeaders();
    const res = await fetch(url, { ...options, headers: { ...headers, ...options.headers } });
    if (res.status === 401) {
      this.authService.logout();
    }
    return res;
  }

  async get(url: string): Promise<Response> {
    return this.fetchWithAuth(url, { method: 'GET' });
  }

  async post(url: string, body: any): Promise<Response> {
    return this.fetchWithAuth(url, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  }

  async patch(url: string, body: any): Promise<Response> {
    return this.fetchWithAuth(url, {
      method: 'PATCH',
      body: JSON.stringify(body)
    });
  }

  async delete(url: string): Promise<Response> {
    return this.fetchWithAuth(url, { method: 'DELETE' });
  }
}
