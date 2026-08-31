import { Injectable, signal } from '@angular/core';

export interface ToastMessage {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  title: string;
  message: string;
  ticketNumber?: string;
  timestamp: string;
}

@Injectable({ providedIn: 'root' })
export class ToastService {
  private _toast = signal<ToastMessage | null>(null);
  toast = this._toast.asReadonly();
  private timer: any = null;

  show(title: string, message: string, type: 'success' | 'info' | 'warning' | 'error' = 'success', ticketNumber?: string) {
    if (this.timer) clearTimeout(this.timer);
    
    this._toast.set({
      id: Math.random().toString(36).substring(2, 9),
      type,
      title,
      message,
      ticketNumber,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    });

    this.timer = setTimeout(() => {
      this.dismiss();
    }, 7000);
  }

  showResolved(ticketNumber: string, title: string) {
    this.show(
      'Ticket Resolved!',
      `Ticket #${ticketNumber} has been successfully completed and resolved.`,
      'success',
      ticketNumber
    );
  }

  dismiss() {
    if (this.timer) clearTimeout(this.timer);
    this._toast.set(null);
  }
}
