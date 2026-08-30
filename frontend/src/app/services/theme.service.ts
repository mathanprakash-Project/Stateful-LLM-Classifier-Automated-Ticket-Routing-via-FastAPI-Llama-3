import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private _isDarkTheme = signal<boolean>(true);
  isDarkTheme = this._isDarkTheme.asReadonly();

  constructor() {
    this.loadTheme();
  }

  loadTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      this._isDarkTheme.set(savedTheme === 'dark');
    }
    this.applyThemeClass();
  }

  toggleTheme() {
    this._isDarkTheme.set(!this._isDarkTheme());
    localStorage.setItem('theme', this._isDarkTheme() ? 'dark' : 'light');
    this.applyThemeClass();
  }

  private applyThemeClass() {
    if (typeof document !== 'undefined') {
      document.body.className = this._isDarkTheme() ? 'theme-dark' : 'theme-light';
    }
  }
}
