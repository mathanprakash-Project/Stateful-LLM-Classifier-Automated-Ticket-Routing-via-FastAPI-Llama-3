import { Component, OnInit, OnDestroy, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
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
  imports: [CommonModule, RouterModule, FormsModule],
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
            <div class="rs-header-row">
              <span class="rs-title">Select Profile to Switch (Password Required)</span>
              <div class="role-filter-pills">
                <button type="button" class="rf-pill" [class.active-pill]="selectedRoleFilter === 'all'" (click)="selectedRoleFilter = 'all'">All (13)</button>
                <button type="button" class="rf-pill" [class.active-pill]="selectedRoleFilter === 'manager'" (click)="selectedRoleFilter = 'manager'">Manager (1)</button>
                <button type="button" class="rf-pill" [class.active-pill]="selectedRoleFilter === 'admin'" (click)="selectedRoleFilter = 'admin'">Admins (2)</button>
                <button type="button" class="rf-pill" [class.active-pill]="selectedRoleFilter === 'agent'" (click)="selectedRoleFilter = 'agent'">Employees (3)</button>
                <button type="button" class="rf-pill" [class.active-pill]="selectedRoleFilter === 'user'" (click)="selectedRoleFilter = 'user'">Users (7)</button>
              </div>
            </div>

            <div class="role-grid">
              <div 
                *ngFor="let p of getFilteredProfiles()" 
                class="role-card" 
                (click)="selectProfileToSwitch(p)"
              >
                <div class="role-card-header">
                  <div class="flex items-center gap-2">
                    <strong class="role-user-name">{{ p.name }}</strong>
                  </div>
                  <span class="role-card-badge" [ngClass]="p.roleClass">{{ p.role }}</span>
                </div>
                <span class="role-user-email">{{ p.email }}</span>
                <p class="role-desc">{{ p.desc }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- PASSWORD VALIDATION MODAL FOR PROFILE SWITCH -->
      <div class="role-modal-backdrop" *ngIf="showPasswordModal" (click)="showPasswordModal = false">
        <div class="modal-box-corona animate-pop" (click)="$event.stopPropagation()" style="max-width: 440px;">
          <div class="role-modal-header">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-warning" style="font-size: 20px;">lock</span>
              <span>Validate Password to Switch</span>
            </div>
            <button class="icon-close-btn" (click)="showPasswordModal = false">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <div class="role-current-box" *ngIf="targetProfile" style="margin-bottom: 16px;">
            <span class="rc-label">Switching To Account</span>
            <div class="rc-info">
              <div class="rc-avatar">{{ targetProfile.name.charAt(0) }}</div>
              <div>
                <strong class="rc-name">{{ targetProfile.name }}</strong>
                <div class="rc-meta">
                  <span class="rc-email">{{ targetProfile.email }}</span>
                  <span class="badge-role-tag" [ngClass]="targetProfile.roleClass">{{ targetProfile.role }}</span>
                </div>
              </div>
            </div>
          </div>

          <form (submit)="executeSwitch($event)" class="password-form-section">
            <p class="text-sm text-muted mb-3" style="font-size: 0.83rem; line-height: 1.4;">
              Enter the password for <strong>{{ targetProfile?.email }}</strong> to authenticate profile access:
            </p>

            <div class="form-group mb-3">
              <label class="form-label" style="display: block; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px;">Account Password</label>
              <div class="search-pill" style="margin: 0; background: #000000; border: 1px solid var(--corona-border); display: flex; align-items: center; padding: 8px 12px; gap: 8px; border-radius: var(--radius-sm);">
                <span class="material-symbols-outlined search-icon">key</span>
                <input 
                  [type]="showPasswordText ? 'text' : 'password'" 
                  [(ngModel)]="switchPassword" 
                  name="switchPassword" 
                  placeholder="Enter password..." 
                  class="search-input" 
                  style="flex: 1; background: transparent; border: none; color: #ffffff; font-size: 0.88rem; outline: none;" 
                  autofocus 
                  required 
                />
                <button type="button" class="icon-btn-mini" (click)="showPasswordText = !showPasswordText" title="Toggle password visibility">
                  <span class="material-symbols-outlined text-sm">{{ showPasswordText ? 'visibility_off' : 'visibility' }}</span>
                </button>
              </div>
              <div style="margin-top: 6px; display: flex; justify-content: space-between; align-items: center;">
                <span class="demo-hint-text">Demo password: <code>password123</code></span>
              </div>
            </div>

            <!-- Error Banner -->
            <div *ngIf="switchError" class="auth-error-banner animate-fade mb-3">
              <span class="material-symbols-outlined text-sm">error</span>
              <span>{{ switchError }}</span>
            </div>

            <div class="flex justify-end gap-2 mt-4">
              <button type="button" class="btn-cancel" (click)="showPasswordModal = false">Cancel</button>
              <button type="submit" class="btn-create-project" [disabled]="!switchPassword || isAuthenticating">
                <span class="material-symbols-outlined" *ngIf="!isAuthenticating">verified_user</span>
                <span *ngIf="isAuthenticating">Authenticating...</span>
                <span *ngIf="!isAuthenticating">Verify & Switch</span>
              </button>
            </div>
          </form>
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

          <!-- User Profile Dropdown Pill with Right Corner 3-Dots Profile Switcher -->
          <div class="corona-user-dropdown" *ngIf="auth.user() as user">
            <div class="user-avatar-wrap">
              <div class="user-avatar-circle">{{ user.name.charAt(0) }}</div>
              <span class="online-indicator"></span>
            </div>
            <div class="user-dropdown-meta">
              <span class="dropdown-user-name">{{ user.name }}</span>
              <span class="dropdown-role-label">{{ auth.roleDisplayName() }}</span>
            </div>
            
            <!-- 3-Dots Button for Profile Switching (Right Corner) -->
            <button class="icon-switch-profile-btn" (click)="showRoleModal = true" title="Switch User Profile & Roles">
              <span class="material-symbols-outlined">more_vert</span>
            </button>

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
          <!-- Top User Mini Card in Sidebar (Clean, without 3-dots) -->
          <div class="sidebar-user-card" *ngIf="auth.user() as user">
            <div class="sidebar-avatar-wrap">
              <div class="sidebar-avatar-img">{{ user.name.charAt(0) }}</div>
              <span class="online-indicator-lg"></span>
            </div>
            <div class="sidebar-user-info">
              <span class="sidebar-name">{{ user.name }}</span>
              <span class="sidebar-role-tag">{{ auth.roleDisplayName() }}</span>
            </div>
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

            <a routerLink="/ticket-status" routerLinkActive="active" class="corona-nav-item">
              <div class="nav-icon-circle icon-cyan">
                <span class="material-symbols-outlined">track_changes</span>
              </div>
              <span class="nav-label">Ticket Status</span>
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
              <span class="nav-pill-badge">{{ getActiveModelName() }}</span>
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

        <!-- PROACTIVE RESOLVED TICKET NOTIFICATION POPUP MODAL (For User login) -->
        <div class="role-modal-backdrop" *ngIf="resolvedNotificationTicket" (click)="dismissResolvedPopup()">
          <div class="role-modal-card animate-pop" (click)="$event.stopPropagation()" style="max-width: 480px;">
            <div class="role-modal-header" style="border-bottom: 1px solid rgba(0, 210, 91, 0.2);">
              <div class="role-modal-title flex items-center gap-2">
                <span class="material-symbols-outlined text-green" style="font-size: 24px;">task_alt</span>
                <span style="color: var(--corona-green);">Ticket Resolved!</span>
              </div>
              <button class="icon-close-btn" (click)="dismissResolvedPopup()">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            <div style="padding: 16px 0;">
              <p style="font-size: 0.9rem; color: #ffffff; margin: 0 0 12px 0; line-height: 1.5;">
                Your maintenance request has been successfully completed and resolved by the support team.
              </p>
              <div style="background: #000000; border: 1px solid var(--corona-border); border-radius: var(--radius-sm); padding: 12px; margin-bottom: 12px;">
                <div style="font-size: 0.75rem; color: var(--corona-purple); font-weight: 700;">{{ resolvedNotificationTicket.ticket_number }}</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #ffffff; margin: 2px 0;">{{ resolvedNotificationTicket.title }}</div>
                <div style="font-size: 0.78rem; color: var(--text-muted);">Category: {{ resolvedNotificationTicket.category_name || resolvedNotificationTicket.category?.name || 'Application Support' }}</div>
              </div>
              <p style="font-size: 0.78rem; color: var(--text-muted); margin: 0;">
                You can review the completion verification, close the ticket, or reopen if further maintenance is required.
              </p>
            </div>

            <div class="flex justify-end gap-2 pt-3 border-t" style="border-color: var(--corona-border);">
              <button class="btn-cancel" (click)="dismissResolvedPopup()">Dismiss</button>
              <button class="btn-create-project" (click)="viewResolvedTicket(resolvedNotificationTicket.id)">
                <span class="material-symbols-outlined">visibility</span> Inspect Ticket
              </button>
            </div>
          </div>
        </div>

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

    .icon-switch-profile-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      display: grid;
      place-items: center;
      padding: 6px;
      border-radius: 4px;
      transition: var(--transition);
    }
    .icon-switch-profile-btn:hover {
      background: rgba(255, 255, 255, 0.08);
      color: #ffffff;
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
    .icon-cyan { background-color: rgba(0, 210, 91, 0.15); color: var(--corona-green); }
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
      width: 92%;
      max-width: 860px;
      max-height: 88vh;
      overflow-y: auto;
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
    .rs-header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 12px;
    }
    .rs-title {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-muted);
      display: block;
      margin: 0;
    }

    .role-filter-pills {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }

    .rf-pill {
      background: #000000;
      border: 1px solid var(--corona-border);
      color: var(--text-muted);
      font-size: 0.72rem;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 20px;
      cursor: pointer;
      transition: var(--transition);
    }
    .rf-pill:hover {
      border-color: var(--corona-purple);
      color: #ffffff;
    }
    .rf-pill.active-pill {
      background: var(--corona-purple);
      border-color: var(--corona-purple);
      color: #ffffff;
    }

    .role-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 12px;
      max-height: 380px;
      overflow-y: auto;
      padding-right: 4px;
    }

    .role-card {
      background: #000000;
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 14px;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      gap: 4px;
      transition: var(--transition);
    }
    .role-card:hover {
      border-color: var(--corona-purple);
      background: rgba(143, 95, 232, 0.05);
      transform: translateY(-1px);
    }

    .role-card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .role-card-badge {
      font-size: 0.7rem;
      font-weight: 700;
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

    .btn-cancel {
      background: transparent;
      border: 1px solid var(--corona-border);
      color: var(--text-muted);
      font-weight: 600;
      font-size: 0.82rem;
      padding: 8px 16px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: var(--transition);
    }
    .btn-cancel:hover { background: rgba(255, 255, 255, 0.05); color: #ffffff; }

    .icon-btn-mini {
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      display: grid;
      place-items: center;
      padding: 2px;
    }
    .icon-btn-mini:hover { color: #ffffff; }
    .demo-hint-text {
      font-size: 0.72rem;
      color: var(--text-muted);
    }
    .demo-hint-text code {
      background: #000000;
      border: 1px solid var(--corona-border);
      padding: 1px 4px;
      border-radius: 3px;
      color: var(--corona-purple);
    }

    .auth-error-banner {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      background: rgba(252, 66, 74, 0.12);
      border: 1px solid var(--corona-red);
      border-radius: var(--radius-sm);
      font-size: 0.8rem;
      color: var(--corona-red);
      font-weight: 600;
    }

    .animate-pop { animation: popIn 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
    .animate-toast { animation: toastIn 0.3s ease-out; }
    .animate-fade { animation: fadeIn 0.2s ease-out; }
    @keyframes popIn { from { opacity: 0; transform: scale(0.94); } to { opacity: 1; transform: scale(1); } }
    @keyframes toastIn { from { opacity: 0; transform: translateX(40px); } to { opacity: 1; transform: translateX(0); } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
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
  showPasswordModal = false;
  targetProfile: any = null;
  switchPassword = '';
  switchError = '';
  showPasswordText = false;
  isAuthenticating = false;

  selectedRoleFilter: string = 'all';

  availableProfiles = [
    // 1 Manager
    { name: 'Mathan', email: 'mathan@company.com', role: 'MANAGER', roleType: 'manager', icon: 'alt_route', roleClass: 'role-manager', desc: 'Governance over tickets, routes out-of-scope requests to DB/SM teams, reopens tickets, and deletes resolved tickets.' },

    // 2 Admins
    { name: 'Adhi', email: 'adhi@company.com', role: 'ADMIN', roleType: 'admin', icon: 'shield_person', roleClass: 'role-admin', desc: 'Full governance over system, approves restricted maintenance operations, assigns agents, and manages platform.' },
    { name: 'Giri', email: 'giri@company.com', role: 'ADMIN', roleType: 'admin', icon: 'shield_person', roleClass: 'role-admin', desc: 'System Administrator with operations oversight, approvals, and user governance.' },

    // 3 Employees
    { name: 'Eegan', email: 'eegan@company.com', role: 'EMPLOYEE', roleType: 'agent', icon: 'engineering', roleClass: 'role-employee', desc: 'Executes operational maintenance, starts work, resolves tickets, consults AI advisor, and adds work notes.' },
    { name: 'Hari', email: 'hari@company.com', role: 'EMPLOYEE', roleType: 'agent', icon: 'engineering', roleClass: 'role-employee', desc: 'Support Agent executing operational tasks, progress updates, and completion notes.' },
    { name: 'Basker', email: 'basker@company.com', role: 'EMPLOYEE', roleType: 'agent', icon: 'engineering', roleClass: 'role-employee', desc: 'Support Agent specialized in execution, verification, and resolution.' },

    // 7 Users
    { name: 'Venu', email: 'venu@company.com', role: 'USER', roleType: 'user', icon: 'person', roleClass: 'role-user', desc: 'Can create tickets, chat with AI triage agent, confirm ticket drafts, view status, and renew archived tickets.' },
    { name: 'Santhosh', email: 'santhosh@company.com', role: 'USER', roleType: 'user', icon: 'person', roleClass: 'role-user', desc: 'Submits application tickets, triage interaction, and status tracking.' },
    { name: 'Harsh', email: 'harsh@company.com', role: 'USER', roleType: 'user', icon: 'person', roleClass: 'role-user', desc: 'Submits maintenance requests, verifies activity, and communicates with agents.' },
    { name: 'Kasi', email: 'kasi@company.com', role: 'USER', roleType: 'user', icon: 'person', roleClass: 'role-user', desc: 'Creates tickets, checks resolutions, and renews archived requests.' },
    { name: 'Deepesh', email: 'deepesh@company.com', role: 'USER', roleType: 'user', icon: 'person', roleClass: 'role-user', desc: 'Submits support requests, reviews AI suggestions, and confirms drafts.' },
    { name: 'Manoj', email: 'manoj@company.com', role: 'USER', roleType: 'user', icon: 'person', roleClass: 'role-user', desc: 'Submits tickets and tracks progress across application queues.' },
    { name: 'Priya', email: 'priya@company.com', role: 'USER', roleType: 'user', icon: 'person', roleClass: 'role-user', desc: 'Creates requests and verifies operational maintenance resolutions.' },
  ];

  getFilteredProfiles() {
    if (this.selectedRoleFilter === 'all') return this.availableProfiles;
    return this.availableProfiles.filter(p => p.roleType === this.selectedRoleFilter);
  }

  private eventSource: EventSource | null = null;
  resolvedNotificationTicket: any = null;

  getActiveModelName(): string {
    const m = localStorage.getItem('preferred_ai_model');
    if (m === 'gpt-oss:120b-cloud') return 'GPT 120B';
    if (m === 'llama3.2:3b') return 'Llama 3.2';
    return 'Llama 3.2';
  }

  ngOnInit() {
    this.initSSE();
    this.triggerLoadingAnimation();
    this.checkUserResolvedTickets();
  }

  async checkUserResolvedTickets() {
    if (!this.auth.isUser()) return;
    try {
      const res = await fetch('/api/tickets?status=resolved', {
        headers: {
          'Authorization': `Bearer ${this.auth.token()}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        const tickets = Array.isArray(data) ? data : (data.items || []);
        for (const t of tickets) {
          const key = `notified_resolved_toast_${t.id}`;
          if (!localStorage.getItem(key)) {
            // Proactive one-time top-right toast on first login
            this.toastService.showResolved(t.ticket_number, t.title);
            localStorage.setItem(key, 'true');
            this.cdr.detectChanges();
            break;
          }
        }
      }
    } catch (e) {}
  }

  dismissResolvedPopup() {
    if (this.resolvedNotificationTicket) {
      localStorage.setItem(`dismissed_resolved_popup_${this.resolvedNotificationTicket.id}`, 'true');
      this.resolvedNotificationTicket = null;
      this.cdr.detectChanges();
    }
  }

  viewResolvedTicket(id: string) {
    this.dismissResolvedPopup();
    this.router.navigate([`/tickets/${id}`]);
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

  selectProfileToSwitch(profile: any) {
    this.targetProfile = profile;
    this.switchPassword = '';
    this.switchError = '';
    this.showPasswordText = false;
    this.showRoleModal = false;
    this.showPasswordModal = true;
  }

  async executeSwitch(event?: Event) {
    if (event) event.preventDefault();
    if (!this.targetProfile || !this.switchPassword || this.isAuthenticating) return;

    this.isAuthenticating = true;
    this.switchError = '';
    this.cdr.detectChanges();

    const res = await this.auth.login(this.targetProfile.email, this.switchPassword);
    this.isAuthenticating = false;

    if (!res.success) {
      this.switchError = res.error || 'Invalid password. Please verify credentials and try again.';
      this.cdr.detectChanges();
      return;
    }

    this.showPasswordModal = false;
    this.switchPassword = '';
    this.toastService.show(
      'Profile Switched',
      `Authenticated successfully as ${this.targetProfile.name}`,
      'success'
    );
    this.triggerLoadingAnimation();
    this.checkUserResolvedTickets();
    this.router.navigate(['/dashboard']);
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
            this.checkUserResolvedTickets();
          }
        } catch (e) {}
      });
      this.eventSource.addEventListener('ticket_resolved', (event: any) => {
        try {
          const data = JSON.parse(event.data);
          this.toastService.showResolved(data.ticket_number || 'TKT', data.title || 'Support ticket resolved');
          this.checkUserResolvedTickets();
        } catch (e) {}
      });
    } catch (e) { console.error(e); }
  }
}
