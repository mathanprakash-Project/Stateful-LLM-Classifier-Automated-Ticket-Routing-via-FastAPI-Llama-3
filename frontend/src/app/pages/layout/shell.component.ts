import { Component, OnInit, OnDestroy, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ThemeService } from '../../services/theme.service';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="app-shell" [class.dark]="theme.isDarkTheme()" [class.light]="!theme.isDarkTheme()">
      
      <!-- TOP HEADER -->
      <header class="app-header">
        <div class="header-left">
          <div class="brand-logo">
            <span class="material-symbols-outlined logo-icon">token</span>
            <div class="brand-text">
              <span class="brand-title">SupportHub <span class="brand-badge">AI</span></span>
              <span class="brand-subtitle">Autonomous IT Operations</span>
            </div>
          </div>
        </div>

        <div class="header-right">
          <!-- Real-time Live Badge -->
          <div class="status-pill" [class.connected]="sseConnected">
            <span class="pulse-dot"></span>
            <span>{{ sseConnected ? 'Live Real-Time' : 'Connecting...' }}</span>
          </div>

          <!-- Theme Switcher -->
          <button class="icon-btn theme-toggle" (click)="theme.toggleTheme()" [title]="theme.isDarkTheme() ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
            <span class="material-symbols-outlined">{{ theme.isDarkTheme() ? 'light_mode' : 'dark_mode' }}</span>
          </button>

          <!-- User Info & Logout -->
          <div class="user-info-wrapper">
            <span class="material-symbols-outlined user-icon">account_circle</span>
            <div class="user-details">
              <span class="user-name">{{ auth.user()?.name }}</span>
              <span class="user-role">{{ auth.userRole() | uppercase }}</span>
            </div>
            <button class="icon-btn logout-btn" (click)="logout()" title="Logout">
              <span class="material-symbols-outlined">logout</span>
            </button>
          </div>
        </div>
      </header>

      <!-- BODY CONTAINER -->
      <div class="app-body">
        
        <!-- SIDEBAR -->
        <aside class="app-sidebar">
          <nav class="sidebar-nav">
            <a routerLink="/dashboard" routerLinkActive="active" class="nav-item">
              <span class="material-symbols-outlined">dashboard</span>
              <span>Dashboard</span>
            </a>
            <a routerLink="/tickets" routerLinkActive="active" class="nav-item">
              <span class="material-symbols-outlined">confirmation_number</span>
              <span>All Tickets</span>
            </a>
            <a routerLink="/assistant" routerLinkActive="active" class="nav-item">
              <span class="material-symbols-outlined">smart_toy</span>
              <span>AI Assistant</span>
              <span class="nav-badge-ai">GPT 120B</span>
            </a>
          </nav>

          <div class="sidebar-action">
            <button class="btn-create-ticket" (click)="openCreateModal()">
              <span class="material-symbols-outlined">add_circle</span>
              <span>New Ticket</span>
            </button>
          </div>

          <div class="sidebar-footer">
            <div class="current-user-card" *ngIf="auth.user() as user">
              <div class="avatar">{{ user.name.charAt(0) }}</div>
              <div class="user-meta">
                <span class="user-name">{{ user.name }}</span>
                <span class="user-role-badge badge-{{ auth.userRole() }}">{{ auth.userRole() }}</span>
              </div>
            </div>
          </div>
        </aside>

        <!-- MAIN VIEW AREA -->
        <main class="app-content">
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .app-shell {
      display: flex;
      flex-direction: column;
      height: 100vh;
      width: 100vw;
      overflow: hidden;
      background: var(--bg-app);
      color: var(--text-main);
    }
    .app-header {
      height: 64px;
      border-bottom: 1px solid var(--border);
      background: var(--bg-surface);
      backdrop-filter: blur(16px);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      z-index: 50;
    }
    .header-left, .header-right {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .brand-logo {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .logo-icon {
      font-size: 28px;
      color: var(--primary);
      filter: drop-shadow(0 0 8px rgba(var(--primary-rgb), 0.5));
    }
    .brand-title {
      font-family: var(--font-heading);
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .brand-badge {
      font-size: 0.65rem;
      background: linear-gradient(135deg, var(--primary), var(--accent));
      color: #fff;
      padding: 2px 6px;
      border-radius: var(--radius-full);
      font-weight: 800;
    }
    .brand-subtitle {
      display: block;
      font-size: 0.7rem;
      color: var(--text-dim);
    }
    .status-pill {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: var(--radius-full);
      background: var(--bg-subtle);
      border: 1px solid var(--border);
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-muted);
    }
    .status-pill.connected {
      color: var(--success);
      border-color: rgba(16, 185, 129, 0.3);
      background: rgba(16, 185, 129, 0.08);
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
      animation: pulseAnim 2s infinite;
    }
    @keyframes pulseAnim {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.3); opacity: 0.4; }
    }
    .icon-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      padding: 6px;
      border-radius: var(--radius-full);
      display: grid;
      place-items: center;
    }
    .icon-btn:hover { background: var(--bg-subtle); color: var(--text-main); }
    .user-info-wrapper {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 4px 10px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
    }
    .user-icon {
      color: var(--primary);
      font-size: 20px;
    }
    .user-details {
      display: flex;
      flex-direction: column;
      margin-right: 8px;
    }
    .user-name {
      font-size: 0.85rem;
      font-weight: 600;
    }
    .user-role {
      font-size: 0.65rem;
      color: var(--text-dim);
      font-weight: 700;
    }
    .logout-btn {
      color: var(--danger);
    }
    .logout-btn:hover {
      background: rgba(239, 68, 68, 0.1);
      color: var(--danger);
    }

    /* SIDEBAR */
    .app-body {
      display: flex;
      flex: 1;
      overflow: hidden;
    }
    .app-sidebar {
      width: 240px;
      border-right: 1px solid var(--border);
      background: var(--bg-surface);
      display: flex;
      flex-direction: column;
      padding: 20px 14px;
      gap: 16px;
    }
    .sidebar-nav {
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex: 1;
    }
    .nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 14px;
      border-radius: var(--radius-md);
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      transition: var(--transition);
      text-decoration: none;
    }
    .nav-item:hover {
      background: var(--bg-subtle);
      color: var(--text-main);
    }
    .nav-item.active {
      background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.15), rgba(var(--accent-rgb), 0.1));
      color: var(--primary);
      border-color: rgba(var(--primary-rgb), 0.3);
      box-shadow: var(--shadow-sm);
    }
    .nav-badge-ai {
      margin-left: auto;
      background: linear-gradient(135deg, var(--primary), var(--accent));
      color: #fff;
      padding: 2px 6px;
      border-radius: var(--radius-full);
      font-size: 0.65rem;
      font-weight: 700;
    }
    .btn-create-ticket {
      width: 100%;
      padding: 12px;
      border-radius: var(--radius-md);
      background: linear-gradient(135deg, var(--primary), var(--primary-hover));
      color: #fff;
      border: none;
      font-weight: 700;
      font-size: 0.88rem;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      cursor: pointer;
      box-shadow: 0 4px 14px rgba(var(--primary-rgb), 0.4);
      transition: var(--transition);
    }
    .btn-create-ticket:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(var(--primary-rgb), 0.5);
    }
    .current-user-card {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px;
      background: var(--bg-subtle);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
    }
    .avatar {
      width: 36px;
      height: 36px;
      border-radius: var(--radius-full);
      background: linear-gradient(135deg, var(--primary), var(--accent));
      color: #fff;
      display: grid;
      place-items: center;
      font-weight: 700;
    }
    .user-meta {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .user-name { font-size: 0.8rem; font-weight: 700; }
    .user-role-badge { font-size: 0.65rem; text-transform: uppercase; font-weight: 700; color: var(--text-dim); }

    .app-content {
      flex: 1;
      overflow-y: auto;
      padding: 0;
    }
  `]
})
export class ShellComponent implements OnInit, OnDestroy {
  auth = inject(AuthService);
  theme = inject(ThemeService);
  router = inject(Router);
  cdr = inject(ChangeDetectorRef);

  sseConnected = false;
  private eventSource: EventSource | null = null;

  ngOnInit() {
    this.initSSE();
  }

  ngOnDestroy() {
    if (this.eventSource) this.eventSource.close();
  }

  logout() {
    this.auth.logout();
  }

  openCreateModal() {
    // Navigate to tickets page with a query param to open modal, or we can use a service to communicate with ticket-list
    // For now we'll route to /tickets since the modal is there
    this.router.navigate(['/tickets'], { queryParams: { create: true } });
  }

  private initSSE() {
    try {
      this.eventSource = new EventSource('/api/events/stream');
      this.eventSource.onopen = () => {
        this.sseConnected = true;
        this.cdr.detectChanges();
      };
      this.eventSource.onerror = () => {
        this.sseConnected = false;
        this.cdr.detectChanges();
      };
      this.eventSource.addEventListener('ticket_created', () => {
        // We could emit a signal or subject here if needed to trigger reloads in children
      });
      this.eventSource.addEventListener('ticket_updated', () => {
        // We could emit a signal or subject here
      });
    } catch (e) { console.error(e); }
  }
}
