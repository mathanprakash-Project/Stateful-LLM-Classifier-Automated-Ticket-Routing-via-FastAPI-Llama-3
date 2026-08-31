import { Component, OnInit, OnDestroy, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ThemeService } from '../../services/theme.service';
import { ToastService } from '../../services/toast.service';

interface ResolutionToast {
  ticketNumber: string;
  title: string;
  timestamp: string;
}

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="corona-app-shell">
      
      <!-- LOADING SCREEN ANIMATION OVERLAY -->
      <div class="app-loading-screen" *ngIf="isLoading">
        <div class="loader-content animate-pop">
          <div class="loader-spinner-wrap">
            <div class="loader-ring ring-outer"></div>
            <div class="loader-ring ring-middle"></div>
            <div class="loader-ring ring-inner"></div>
            <div class="loader-center-dot"></div>
          </div>
          <div class="loader-brand">
            <span class="loader-brand-title">SupportHub <span class="loader-brand-badge">AI</span></span>
            <span class="loader-brand-sub">Synchronizing Autonomous Operations...</span>
          </div>
        </div>
      </div>

      <!-- RESOLVED TICKET NOTIFICATION TOAST POPUP -->
      <div class="toast-overlay" *ngIf="toastService.toast() as t">
        <div class="resolution-toast-card animate-toast">
          <div class="toast-icon-wrap">
            <span class="material-symbols-outlined toast-icon">task_alt</span>
          </div>
          <div class="toast-body">
            <div class="toast-header-row">
              <span class="toast-title">{{ t.title }}</span>
              <span class="toast-time">{{ t.timestamp }}</span>
            </div>
            <p class="toast-msg">{{ t.message }}</p>
            <span class="toast-subject" *ngIf="t.ticketNumber">Verified & Closed in Registry</span>
          </div>
          <button class="toast-close-btn" (click)="toastService.dismiss()">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
      </div>

      <!-- 3-DOTS USER ROLE & PROFILE MODAL -->
      <div class="role-modal-backdrop" *ngIf="showRoleModal" (click)="showRoleModal = false">
        <div class="role-modal-card animate-pop" (click)="$event.stopPropagation()">
          <div class="role-modal-header">
            <div class="role-modal-title">
              <span class="material-symbols-outlined text-purple">badge</span>
              <span>User Profiles & Roles</span>
            </div>
            <button class="icon-close-btn" (click)="showRoleModal = false">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <div class="role-current-box" *ngIf="auth.user() as u">
            <span class="rc-label">Active Logged-in Profile</span>
            <div class="rc-info">
              <div class="rc-avatar">{{ u.name.charAt(0) }}</div>
              <div>
                <strong class="rc-name">{{ u.name }}</strong>
                <div class="rc-meta">
                  <span class="rc-email">{{ u.email }}</span>
                  <span class="badge-role-tag role-{{ auth.userRole() }}">{{ auth.roleDisplayName() }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="role-switch-section">
            <span class="rs-title">Switch Demo Profile</span>
            <div class="role-grid">
              
              <!-- Profile: User -->
              <div class="role-card" [class.active-card]="auth.isUser()" (click)="switchAccount('john@company.com')">
                <div class="role-card-top">
                  <span class="material-symbols-outlined role-icon icon-user">person</span>
                  <span class="role-card-badge">USER</span>
                </div>
                <strong class="role-user-name">John Doe (Customer)</strong>
                <span class="role-user-email">john&#64;company.com</span>
                <p class="role-desc">Can create tickets, chat with AI triage agent, confirm ticket drafts, view status, and renew archived tickets.</p>
              </div>

              <!-- Profile: Employee (Agent) -->
              <div class="role-card" [class.active-card]="auth.isEmployee()" (click)="switchAccount('bob@company.com')">
                <div class="role-card-top">
                  <span class="material-symbols-outlined role-icon icon-employee">engineering</span>
                  <span class="role-card-badge">EMPLOYEE</span>
                </div>
                <strong class="role-user-name">Employee Bob (Support Agent)</strong>
                <span class="role-user-email">bob&#64;company.com</span>
                <p class="role-desc">Executes operational maintenance, starts work, resolves tickets, consults AI advisor, and adds work notes.</p>
              </div>

              <!-- Profile: Manager -->
              <div class="role-card" [class.active-card]="auth.userRole() === 'manager'" (click)="switchAccount('alice@company.com')">
                <div class="role-card-top">
                  <span class="material-symbols-outlined role-icon icon-manager">alt_route</span>
                  <span class="role-card-badge">MANAGER</span>
                </div>
                <strong class="role-user-name">Manager Alice (Support Lead)</strong>
                <span class="role-user-email">alice&#64;company.com</span>
                <p class="role-desc">Governance over tickets, routes out-of-scope requests to DB/SM teams, reopens tickets, and deletes resolved tickets.</p>
              </div>

              <!-- Profile: Admin -->
              <div class="role-card" [class.active-card]="auth.isAdmin()" (click)="switchAccount('admin@company.com')">
                <div class="role-card-top">
                  <span class="material-symbols-outlined role-icon icon-admin">shield_person</span>
                  <span class="role-card-badge">ADMIN</span>
                </div>
                <strong class="role-user-name">Admin Root (System Administrator)</strong>
                <span class="role-user-email">admin&#64;company.com</span>
                <p class="role-desc">Full governance over system, approves restricted maintenance operations, assigns agents, and manages platform.</p>
              </div>

            </div>
          </div>
        </div>
      </div>

      <!-- TOP HEADER NAVBAR (Cleaned: No dummy symbols or searchbars) -->
      <header class="corona-header">
        <div class="header-brand-section">
          <div class="corona-logo">
            <span class="corona-logo-text">SupportHub</span>
            <span class="corona-logo-sub">AI</span>
          </div>
        </div>

        <div class="header-actions-section">
          <!-- + Create Ticket button (Only for User profile) -->
          <button class="btn-create-project" *ngIf="auth.isUser()" (click)="openCreateModal()">
            <span class="material-symbols-outlined">add</span>
            <span>Create Ticket</span>
          </button>

          <!-- User Profile Dropdown Pill -->
          <div class="corona-user-dropdown" *ngIf="auth.user() as user">
            <div class="user-avatar-wrap">
              <div class="user-avatar-circle">{{ user.name.charAt(0) }}</div>
              <span class="online-indicator"></span>
            </div>
            <div class="user-dropdown-meta">
              <span class="dropdown-user-name">{{ user.name }}</span>
              <span class="dropdown-role-label">{{ auth.roleDisplayName() }}</span>
            </div>
            
            <button class="logout-mini-btn" (click)="logout()" title="Logout">
              <span class="material-symbols-outlined">logout</span>
            </button>
          </div>
        </div>
      </header>

      <!-- MAIN CONTAINER: SIDEBAR + CONTENT -->
      <div class="corona-body">
        
        <!-- CORONA SIDEBAR -->
        <aside class="corona-sidebar">
          <!-- Top User Mini Card in Sidebar with 3-Dots Role Inspector -->
          <div class="sidebar-user-card" *ngIf="auth.user() as user">
            <div class="sidebar-avatar-wrap">
              <div class="sidebar-avatar-img">{{ user.name.charAt(0) }}</div>
              <span class="online-indicator-lg"></span>
            </div>
            <div class="sidebar-user-info">
              <span class="sidebar-name">{{ user.name }}</span>
              <span class="sidebar-role-tag">{{ auth.roleDisplayName() }}</span>
            </div>
            <button class="sidebar-dots-btn" (click)="showRoleModal = true" title="View Roles & User Types">
              <span class="material-symbols-outlined">more_vert</span>
            </button>
          </div>

          <!-- Section Label: Navigation -->
          <div class="sidebar-section-header">Navigation</div>

          <nav class="corona-nav-menu">
            <a routerLink="/dashboard" routerLinkActive="active" class="corona-nav-item">
              <div class="nav-icon-circle icon-purple">
                <span class="material-symbols-outlined">speed</span>
              </div>
              <span class="nav-label">Dashboard</span>
            </a>

            <a routerLink="/tickets" routerLinkActive="active" class="corona-nav-item">
              <div class="nav-icon-circle icon-orange">
                <span class="material-symbols-outlined">receipt_long</span>
              </div>
              <span class="nav-label">All Tickets</span>
            </a>

            <a routerLink="/assistant" routerLinkActive="active" class="corona-nav-item">
              <div class="nav-icon-circle icon-blue">
                <span class="material-symbols-outlined">smart_toy</span>
              </div>
              <span class="nav-label">AI Assistant</span>
              <span class="nav-pill-badge">GPT 120B</span>
            </a>
          </nav>

          <!-- Section Label: Operations -->
          <div class="sidebar-section-header mt-4">System Status</div>
          <div class="sidebar-status-box">
            <div class="status-realtime-pill" [class.connected]="sseConnected">
              <span class="pulse-dot"></span>
              <span>{{ sseConnected ? 'Live Real-Time SSE' : 'Connecting...' }}</span>
            </div>
          </div>
        </aside>

        <!-- MAIN VIEW AREA -->
        <main class="corona-content">
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .corona-app-shell {
      display: flex;
      flex-direction: column;
      height: 100vh;
      width: 100vw;
      overflow: hidden;
      background-color: var(--corona-bg);
      color: var(--text-main);
    }

    /* TOP HEADER */
    .corona-header {
      height: 70px;
      background-color: var(--corona-surface);
      border-bottom: 1px solid var(--corona-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
      z-index: 100;
    }

    .header-brand-section {
      display: flex;
      align-items: center;
    }

    .corona-logo {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .corona-logo-text {
      font-family: var(--font-heading);
      font-size: 1.45rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #ffffff;
    }

    .corona-logo-sub {
      background: var(--corona-green);
      color: #000;
      font-size: 0.68rem;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 4px;
    }

    .header-actions-section {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .btn-create-project {
      background-color: var(--corona-green);
      color: #000000;
      font-weight: 700;
      font-size: 0.82rem;
      padding: 8px 16px;
      border-radius: var(--radius-sm);
      border: none;
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: var(--transition);
    }
    .btn-create-project:hover {
      background-color: #00bf52;
      box-shadow: var(--shadow-glow-green);
    }

    .corona-user-dropdown {
      display: flex;
      align-items: center;
      gap: 12px;
      background: #000000;
      border: 1px solid var(--corona-border);
      padding: 5px 14px;
      border-radius: var(--radius-sm);
    }

    .user-avatar-wrap {
      position: relative;
    }

    .user-avatar-circle {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--corona-purple), var(--corona-blue));
      color: #fff;
      display: grid;
      place-items: center;
      font-weight: 700;
      font-size: 0.88rem;
    }

    .online-indicator {
      position: absolute;
      bottom: 0;
      right: 0;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--corona-green);
      border: 1.5px solid #000;
    }

    .user-dropdown-meta {
      display: flex;
      flex-direction: column;
    }

    .dropdown-user-name {
      font-size: 0.85rem;
      font-weight: 700;
      color: #ffffff;
      line-height: 1.2;
    }

    .dropdown-role-label {
      font-size: 0.65rem;
      color: var(--corona-green);
      font-weight: 700;
      letter-spacing: 0.04em;
    }

    .logout-mini-btn {
      background: transparent;
      border: none;
      color: var(--corona-red);
      cursor: pointer;
      display: grid;
      place-items: center;
      padding: 6px;
      border-radius: 4px;
      transition: var(--transition);
    }
    .logout-mini-btn:hover {
      background: rgba(252, 66, 74, 0.15);
    }

    /* BODY & SIDEBAR */
    .corona-body {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    .corona-sidebar {
      width: 250px;
      background-color: var(--corona-surface);
      border-right: 1px solid var(--corona-border);
      display: flex;
      flex-direction: column;
      padding: 20px 14px;
      gap: 12px;
      overflow-y: auto;
    }

    .sidebar-user-card {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px;
      background-color: #000000;
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      margin-bottom: 12px;
    }

    .sidebar-avatar-wrap {
      position: relative;
    }

    .sidebar-avatar-img {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--corona-purple), var(--corona-blue));
      color: #fff;
      display: grid;
      place-items: center;
      font-weight: 800;
      font-size: 1rem;
    }

    .online-indicator-lg {
      position: absolute;
      bottom: 1px;
      right: 1px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--corona-green);
      border: 2px solid #000;
    }

    .sidebar-user-info {
      display: flex;
      flex-direction: column;
      flex: 1;
    }

    .sidebar-name {
      font-size: 0.88rem;
      font-weight: 700;
      color: #ffffff;
    }

    .sidebar-role-tag {
      font-size: 0.65rem;
      font-weight: 700;
      color: var(--corona-green);
      letter-spacing: 0.05em;
    }

    .sidebar-dots-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      display: grid;
      place-items: center;
      padding: 4px;
      border-radius: 4px;
      transition: var(--transition);
    }
    .sidebar-dots-btn:hover {
      background: rgba(255, 255, 255, 0.08);
      color: #ffffff;
    }

    .sidebar-section-header {
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      padding: 6px 12px 2px 12px;
    }

    .corona-nav-menu {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .corona-nav-item {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 10px 14px;
      border-radius: var(--radius-sm);
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.88rem;
      font-weight: 600;
      transition: var(--transition);
    }
    .corona-nav-item:hover {
      background: rgba(255, 255, 255, 0.04);
      color: #ffffff;
    }
    .corona-nav-item.active {
      background: #000000;
      color: #ffffff;
      border-left: 3px solid var(--corona-purple);
    }

    .nav-icon-circle {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      font-size: 18px;
    }
    .icon-purple { background-color: var(--corona-purple-bg); color: var(--corona-purple); }
    .icon-orange { background-color: var(--corona-orange-bg); color: var(--corona-orange); }
    .icon-blue { background-color: var(--corona-blue-bg); color: var(--corona-blue); }

    .nav-label { flex: 1; }

    .nav-pill-badge {
      font-size: 0.65rem;
      font-weight: 800;
      padding: 2px 6px;
      border-radius: 4px;
      background: linear-gradient(135deg, var(--corona-purple), var(--corona-blue));
      color: #ffffff;
    }

    .sidebar-status-box { padding: 4px 10px; }

    .status-realtime-pill {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      background: #000000;
      border: 1px solid var(--corona-border);
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-muted);
    }
    .status-realtime-pill.connected {
      color: var(--corona-green);
      border-color: rgba(0, 210, 91, 0.25);
    }

    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--corona-green);
      box-shadow: 0 0 8px var(--corona-green);
      animation: pulseAnim 2s infinite;
    }
    @keyframes pulseAnim {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.3); opacity: 0.4; }
    }

    .corona-content {
      flex: 1;
      overflow-y: auto;
      background-color: var(--corona-bg);
      padding: 24px;
    }

    /* LOADING SCREEN ANIMATION OVERLAY */
    .app-loading-screen {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.88);
      backdrop-filter: blur(8px);
      display: grid;
      place-items: center;
      z-index: 9999;
    }

    .loader-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 24px;
    }

    .loader-spinner-wrap {
      position: relative;
      width: 90px;
      height: 90px;
      display: grid;
      place-items: center;
    }

    .loader-ring {
      position: absolute;
      border-radius: 50%;
      border: 2px solid transparent;
    }
    .ring-outer {
      inset: 0;
      border-top-color: var(--corona-purple);
      border-right-color: var(--corona-purple);
      animation: spinClockwise 1.6s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
      box-shadow: 0 0 15px rgba(143, 95, 232, 0.4);
    }
    .ring-middle {
      inset: 12px;
      border-bottom-color: var(--corona-blue);
      border-left-color: var(--corona-blue);
      animation: spinCounterClockwise 1.2s linear infinite;
    }
    .ring-inner {
      inset: 24px;
      border-top-color: var(--corona-green);
      animation: spinClockwise 0.8s ease-in-out infinite;
    }
    .loader-center-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #ffffff;
      box-shadow: 0 0 12px #ffffff;
    }

    @keyframes spinClockwise { to { transform: rotate(360deg); } }
    @keyframes spinCounterClockwise { to { transform: rotate(-360deg); } }

    .loader-brand {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      text-align: center;
    }
    .loader-brand-title {
      font-family: var(--font-heading);
      font-size: 1.4rem;
      font-weight: 800;
      color: #ffffff;
    }
    .loader-brand-badge {
      background: var(--corona-green);
      color: #000000;
      font-size: 0.7rem;
      font-weight: 800;
      padding: 2px 6px;
      border-radius: 4px;
    }
    .loader-brand-sub {
      font-size: 0.8rem;
      color: var(--text-muted);
    }

    /* RESOLUTION TOAST NOTIFICATION POPUP */
    .toast-overlay {
      position: fixed;
      top: 24px;
      right: 24px;
      z-index: 10000;
    }

    .resolution-toast-card {
      background: #12151e;
      border: 1px solid var(--corona-green);
      box-shadow: 0 10px 30px rgba(0, 210, 91, 0.25);
      border-radius: var(--radius-sm);
      padding: 16px 20px;
      display: flex;
      align-items: flex-start;
      gap: 14px;
      max-width: 420px;
      color: #ffffff;
    }

    .toast-icon-wrap {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: rgba(0, 210, 91, 0.15);
      color: var(--corona-green);
      display: grid;
      place-items: center;
      flex-shrink: 0;
    }
    .toast-icon { font-size: 22px; }

    .toast-body { flex: 1; }
    .toast-header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 4px;
    }
    .toast-title {
      font-weight: 800;
      font-size: 0.92rem;
      color: var(--corona-green);
    }
    .toast-time {
      font-size: 0.7rem;
      color: var(--text-muted);
    }
    .toast-msg {
      font-size: 0.85rem;
      margin: 0 0 4px 0;
      line-height: 1.4;
    }
    .toast-subject {
      font-size: 0.75rem;
      color: var(--text-muted);
      display: block;
    }

    .toast-close-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      padding: 2px;
      display: grid;
      place-items: center;
    }
    .toast-close-btn:hover { color: #ffffff; }

    /* 3-DOTS ROLE & PROFILE SELECTOR MODAL */
    .role-modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(4px);
      display: grid;
      place-items: center;
      z-index: 10001;
    }

    .role-modal-card {
      background: var(--corona-surface);
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      width: 90%;
      max-width: 680px;
      padding: 24px;
      color: #ffffff;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8);
    }

    .role-modal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 20px;
      border-bottom: 1px solid var(--corona-border);
      padding-bottom: 14px;
    }
    .role-modal-title {
      font-size: 1.15rem;
      font-weight: 800;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .text-purple { color: var(--corona-purple); }

    .icon-close-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      padding: 4px;
      display: grid;
      place-items: center;
    }
    .icon-close-btn:hover { color: #ffffff; }

    .role-current-box {
      background: #000000;
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 14px 18px;
      margin-bottom: 20px;
    }
    .rc-label {
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-muted);
      display: block;
      margin-bottom: 8px;
    }
    .rc-info {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .rc-avatar {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--corona-purple), var(--corona-blue));
      display: grid;
      place-items: center;
      font-weight: 800;
      font-size: 1.1rem;
    }
    .rc-name { font-size: 1rem; color: #ffffff; }
    .rc-meta {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: 2px;
    }
    .rc-email { font-size: 0.8rem; color: var(--text-muted); }

    .badge-role-tag {
      font-size: 0.65rem;
      font-weight: 800;
      padding: 2px 8px;
      border-radius: 4px;
      text-transform: uppercase;
    }
    .role-user { background: rgba(0, 210, 91, 0.15); color: var(--corona-green); }
    .role-agent, .role-employee { background: rgba(0, 144, 231, 0.15); color: var(--corona-blue); }
    .role-manager { background: rgba(255, 171, 0, 0.15); color: var(--corona-orange); }
    .role-admin { background: rgba(143, 95, 232, 0.15); color: var(--corona-purple); }

    .role-switch-section { margin-top: 14px; }
    .rs-title {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-muted);
      display: block;
      margin-bottom: 12px;
    }

    .role-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }

    .role-card {
      background: #000000;
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 16px;
      cursor: pointer;
      transition: var(--transition);
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .role-card:hover {
      border-color: var(--corona-purple);
      background: rgba(143, 95, 232, 0.04);
      transform: translateY(-2px);
    }
    .role-card.active-card {
      border-color: var(--corona-green);
      background: rgba(0, 210, 91, 0.05);
      box-shadow: 0 0 12px rgba(0, 210, 91, 0.15);
    }

    .role-card-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 4px;
    }
    .role-icon { font-size: 24px; }
    .icon-user { color: var(--corona-green); }
    .icon-employee { color: var(--corona-blue); }
    .icon-manager { color: var(--corona-orange); }
    .icon-admin { color: var(--corona-purple); }

    .role-card-badge {
      font-size: 0.65rem;
      font-weight: 800;
      background: rgba(255, 255, 255, 0.08);
      padding: 2px 6px;
      border-radius: 4px;
      color: #ffffff;
    }

    .role-user-name { font-size: 0.88rem; color: #ffffff; }
    .role-user-email { font-size: 0.75rem; color: var(--text-muted); }
    .role-desc {
      font-size: 0.75rem;
      color: var(--text-muted);
      margin: 4px 0 0 0;
      line-height: 1.4;
    }

    .animate-pop { animation: popIn 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
    .animate-toast { animation: toastIn 0.3s ease-out; }
    @keyframes popIn { from { opacity: 0; transform: scale(0.94); } to { opacity: 1; transform: scale(1); } }
    @keyframes toastIn { from { opacity: 0; transform: translateX(40px); } to { opacity: 1; transform: translateX(0); } }
  `]
})
export class ShellComponent implements OnInit, OnDestroy {
  auth = inject(AuthService);
  theme = inject(ThemeService);
  router = inject(Router);
  cdr = inject(ChangeDetectorRef);
  toastService = inject(ToastService);

  sseConnected = false;
  isLoading = false;
  showRoleModal = false;
  private eventSource: EventSource | null = null;

  ngOnInit() {
    this.initSSE();
    this.triggerLoadingAnimation();
  }

  ngOnDestroy() {
    if (this.eventSource) this.eventSource.close();
  }

  triggerLoadingAnimation() {
    this.isLoading = true;
    setTimeout(() => {
      this.isLoading = false;
      this.cdr.detectChanges();
    }, 600);
  }

  logout() {
    this.auth.logout();
  }

  openCreateModal() {
    this.router.navigate(['/tickets'], { queryParams: { create: true } });
  }

  async switchAccount(email: string) {
    this.showRoleModal = false;
    this.isLoading = true;
    this.cdr.detectChanges();

    await this.auth.login(email, 'password123');
    setTimeout(() => {
      this.isLoading = false;
      this.cdr.detectChanges();
      this.router.navigate(['/dashboard']);
    }, 500);
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
      this.eventSource.addEventListener('ticket_updated', (event: any) => {
        try {
          const data = JSON.parse(event.data);
          if (data.status === 'resolved') {
            this.toastService.showResolved(data.ticket_number || 'TKT', data.title || 'Support ticket resolved');
          }
        } catch (e) {}
      });
      this.eventSource.addEventListener('ticket_resolved', (event: any) => {
        try {
          const data = JSON.parse(event.data);
          this.toastService.showResolved(data.ticket_number || 'TKT', data.title || 'Support ticket resolved');
        } catch (e) {}
      });
    } catch (e) { console.error(e); }
  }
}
