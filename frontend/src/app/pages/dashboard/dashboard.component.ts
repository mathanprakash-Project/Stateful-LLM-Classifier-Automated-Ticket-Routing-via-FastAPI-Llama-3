import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

interface TicketSummary {
  id: string;
  ticket_number: string;
  title: string;
  priority: string;
  status: string;
  category_name?: string;
  creator_name?: string;
  assignee_name?: string;
  created_at: string;
  updated_at: string;
}

interface DashboardStats {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  closed_tickets: number;
  pending_routing_tickets?: number;
  pending_approval_tickets?: number;
  recent_tickets: TicketSummary[];
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="view-panel animate-fade">
      <div class="view-header">
        <div>
          <h1 class="view-title">{{ dashboardTitle }}</h1>
          <p class="view-desc">Live status of support operations, SLA metrics, and incoming workload</p>
        </div>
        <button class="btn btn-outlined" (click)="loadDashboard()">
          <span class="material-symbols-outlined">refresh</span>
          <span>Refresh</span>
        </button>
      </div>

      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-icon-wrap icon-total">
            <span class="material-symbols-outlined">folder_open</span>
          </div>
          <div class="kpi-info">
            <span class="kpi-label">Total Tickets</span>
            <span class="kpi-value">{{ dashboardStats?.total_tickets || 0 }}</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon-wrap icon-open">
            <span class="material-symbols-outlined">error_outline</span>
          </div>
          <div class="kpi-info">
            <span class="kpi-label">Open / Unresolved</span>
            <span class="kpi-value text-amber">{{ dashboardStats?.open_tickets || 0 }}</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon-wrap icon-progress">
            <span class="material-symbols-outlined">autorenew</span>
          </div>
          <div class="kpi-info">
            <span class="kpi-label">In Progress</span>
            <span class="kpi-value text-accent">{{ dashboardStats?.in_progress_tickets || 0 }}</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon-wrap icon-resolved">
            <span class="material-symbols-outlined">check_circle</span>
          </div>
          <div class="kpi-info">
            <span class="kpi-label">Resolved</span>
            <span class="kpi-value text-green">{{ dashboardStats?.resolved_tickets || 0 }}</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon-wrap icon-closed">
            <span class="material-symbols-outlined">lock</span>
          </div>
          <div class="kpi-info">
            <span class="kpi-label">Closed</span>
            <span class="kpi-value text-muted">{{ dashboardStats?.closed_tickets || 0 }}</span>
          </div>
        </div>

        <!-- Manager: Pending Routing -->
        <div class="kpi-card" *ngIf="auth.isManager() || auth.isAdmin()">
          <div class="kpi-icon-wrap icon-routing">
            <span class="material-symbols-outlined">alt_route</span>
          </div>
          <div class="kpi-info">
            <span class="kpi-label">Pending Routing</span>
            <span class="kpi-value text-orange">{{ dashboardStats?.pending_routing_tickets || 0 }}</span>
          </div>
        </div>

        <!-- Admin: Pending Approval -->
        <div class="kpi-card" *ngIf="auth.isAdmin()">
          <div class="kpi-icon-wrap icon-approval">
            <span class="material-symbols-outlined">gavel</span>
          </div>
          <div class="kpi-info">
            <span class="kpi-label">Pending Approval</span>
            <span class="kpi-value text-yellow">{{ dashboardStats?.pending_approval_tickets || 0 }}</span>
          </div>
        </div>
      </div>

      <div class="card-surface mt-6">
        <div class="card-surface-header">
          <h2 class="card-title">Recent Support Activity</h2>
          <span class="live-tag"><span class="pulse-dot"></span> Auto-updating</span>
        </div>
        <div class="table-container">
          <table class="mat-table">
            <thead>
              <tr>
                <th>Ticket #</th>
                <th>Title</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Creator</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let t of dashboardStats?.recent_tickets">
                <td><span class="ticket-num">{{ t.ticket_number }}</span></td>
                <td class="font-semibold">{{ t.title }}</td>
                <td><span class="category-chip">{{ t.category_name || 'General' }}</span></td>
                <td><span class="badge-priority priority-{{ t.priority }}">{{ t.priority }}</span></td>
                <td><span class="status-badge status-{{ t.status }}">{{ formatStatus(t.status) }}</span></td>
                <td>{{ t.creator_name || 'User' }}</td>
                <td>
                  <div class="flex items-center gap-2">
                    <button class="btn btn-sm btn-outlined" (click)="viewTicketDetails(t.id)">Inspect</button>
                    <button *ngIf="isManager() && (t.status === 'resolved' || t.status === 'closed')" class="btn btn-sm btn-danger-outlined" (click)="deleteResolvedTicket(t, $event)" title="Delete Resolved Ticket (Manager only)">
                      <span class="material-symbols-outlined text-sm">delete</span>
                      <span>Delete</span>
                    </button>
                  </div>
                </td>
              </tr>
              <tr *ngIf="!dashboardStats?.recent_tickets?.length">
                <td colspan="7" class="empty-state">No recent activity found.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Manager Profile: Resolved Tickets Cleanup Panel -->
      <div class="card-surface mt-6 manager-cleanup-card" *ngIf="isManager()">
        <div class="card-surface-header">
          <div>
            <h2 class="card-title text-green flex items-center gap-2">
              <span class="material-symbols-outlined">delete_sweep</span>
              Manager Profile: Resolved Tickets Available for Deletion
            </h2>
            <p class="text-sm text-muted">As a Manager, you can permanently delete tickets once their operational activity is resolved.</p>
          </div>
        </div>
        <div class="table-container">
          <table class="mat-table">
            <thead>
              <tr>
                <th>Ticket #</th>
                <th>Title</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let t of resolvedTickets">
                <td><span class="ticket-num">{{ t.ticket_number }}</span></td>
                <td class="font-semibold">{{ t.title }}</td>
                <td><span class="category-chip">{{ t.category_name || 'General' }}</span></td>
                <td><span class="badge-priority priority-{{ t.priority }}">{{ t.priority }}</span></td>
                <td><span class="status-badge status-resolved">{{ formatStatus(t.status) }}</span></td>
                <td>
                  <button class="btn btn-sm btn-danger" (click)="deleteResolvedTicket(t, $event)" title="Permanently Delete Ticket">
                    <span class="material-symbols-outlined text-sm">delete</span>
                    <span>Delete Ticket</span>
                  </button>
                </td>
              </tr>
              <tr *ngIf="!resolvedTickets.length">
                <td colspan="6" class="empty-state">No resolved tickets pending manager deletion.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .view-panel {
      padding: 28px 36px;
      max-width: 1200px;
      margin: 0 auto;
    }
    .view-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 24px;
    }
    .view-title {
      font-family: var(--font-heading);
      font-size: 1.6rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .view-desc {
      color: var(--text-muted);
      font-size: 0.88rem;
      margin-top: 4px;
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 16px;
    }
    .kpi-card {
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: var(--shadow-sm);
      transition: var(--transition);
    }
    .kpi-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
    .kpi-icon-wrap { width: 48px; height: 48px; border-radius: var(--radius-md); display: grid; place-items: center; }
    .icon-total { background: rgba(99, 102, 241, 0.12); color: var(--primary); }
    .icon-open { background: rgba(245, 158, 11, 0.12); color: var(--warning); }
    .icon-progress { background: rgba(6, 182, 212, 0.12); color: var(--accent); }
    .icon-resolved { background: rgba(16, 185, 129, 0.12); color: var(--success); }
    .icon-closed { background: rgba(100, 116, 139, 0.12); color: var(--text-dim); }
    .icon-routing { background: rgba(249, 115, 22, 0.12); color: #f97316; }
    .icon-approval { background: rgba(234, 179, 8, 0.12); color: #eab308; }
    .kpi-info { display: flex; flex-direction: column; }
    .kpi-label { font-size: 0.75rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; }
    .kpi-value { font-family: var(--font-heading); font-size: 1.8rem; font-weight: 800; }
    
    .card-surface { background: var(--bg-surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 24px; box-shadow: var(--shadow-sm); }
    .card-surface-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
    .card-title { font-family: var(--font-heading); font-size: 1.1rem; font-weight: 700; }
    .live-tag { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: var(--success); font-weight: 600; }
    .pulse-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--success); box-shadow: 0 0 8px var(--success); animation: pulseAnim 2s infinite; }
    @keyframes pulseAnim { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.3); opacity: 0.4; } }
    
    .table-container { overflow-x: auto; }
    .mat-table { width: 100%; border-collapse: collapse; text-align: left; }
    .mat-table th { padding: 12px 16px; font-size: 0.75rem; text-transform: uppercase; color: var(--text-dim); font-weight: 700; border-bottom: 1px solid var(--border); }
    .mat-table td { padding: 14px 16px; font-size: 0.88rem; border-bottom: 1px solid var(--border-subtle); vertical-align: middle; }
    .mat-table tr:hover td { background: var(--bg-subtle); }
    
    .ticket-num { font-weight: 700; color: var(--primary); font-family: var(--font-heading); }
    .category-chip { padding: 4px 10px; border-radius: var(--radius-full); background: var(--bg-subtle); border: 1px solid var(--border); font-size: 0.75rem; font-weight: 600; }
    
    .status-badge { display: inline-block; padding: 4px 10px; border-radius: var(--radius-full); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
    .status-open { background: rgba(245, 158, 11, 0.12); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .status-assigned { background: rgba(168, 85, 247, 0.12); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
    .status-in_progress { background: rgba(6, 182, 212, 0.12); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.3); }
    .status-escalated { background: rgba(239, 68, 68, 0.12); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .status-resolved { background: rgba(16, 185, 129, 0.12); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .status-closed { background: rgba(100, 116, 139, 0.12); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.3); }
    .status-cancelled { background: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.2); }
    .status-pending_manager_routing { background: rgba(249, 115, 22, 0.12); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.3); }
    .status-pending_admin_approval { background: rgba(234, 179, 8, 0.12); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.3); }
    .status-approved { background: rgba(16, 185, 129, 0.12); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .status-rejected { background: rgba(239, 68, 68, 0.12); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .status-routed { background: rgba(59, 130, 246, 0.12); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .status-reopened { background: rgba(168, 85, 247, 0.12); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
    
    .badge-priority { font-size: 0.75rem; font-weight: 800; text-transform: uppercase; }
    .priority-low { color: #34d399; }
    .priority-medium { color: #fbbf24; }
    .priority-high { color: #f87171; }
    .priority-critical { color: #ff0055; text-shadow: 0 0 10px rgba(255, 0, 85, 0.4); }
    
    .btn { padding: 9px 16px; border-radius: var(--radius-md); font-family: inherit; font-weight: 600; font-size: 0.85rem; border: 1px solid transparent; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; transition: var(--transition); }
    .btn-outlined { background: transparent; border-color: var(--border); color: var(--text-main); }
    .btn-outlined:hover { background: var(--bg-subtle); }
    .btn-danger-outlined { background: transparent; border-color: rgba(239, 68, 68, 0.4); color: #f87171; }
    .btn-danger-outlined:hover { background: rgba(239, 68, 68, 0.15); border-color: #ef4444; color: #ff5555; }
    .btn-danger { background: #ef4444; color: #fff; border-color: #dc2626; }
    .btn-danger:hover { background: #dc2626; }
    .btn-sm { padding: 7px 12px; font-size: 0.78rem; }
    
    .manager-cleanup-card { border-left: 4px solid var(--success); }
    .flex { display: flex; }
    .items-center { align-items: center; }
    .gap-2 { gap: 8px; }
    
    .text-amber { color: var(--warning); }
    .text-accent { color: var(--accent); }
    .text-green { color: var(--success); }
    .text-muted { color: var(--text-muted); }
    .text-orange { color: #f97316; }
    .text-yellow { color: #eab308; }
    .font-semibold { font-weight: 600; }
    .mt-6 { margin-top: 24px; }
    .empty-state { text-align: center; color: var(--text-dim); padding: 24px; }
    
    .animate-fade { animation: fadeIn 0.25s ease-out; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  `]
})
export class DashboardComponent implements OnInit {
  api = inject(ApiService);
  auth = inject(AuthService);
  router = inject(Router);
  cdr = inject(ChangeDetectorRef);

  dashboardStats: DashboardStats | null = null;
  
  get dashboardTitle(): string {
    const role = this.auth.userRole();
    if (role === 'admin') return 'System Dashboard';
    if (role === 'manager') return 'Manager Profile Dashboard';
    return 'My Dashboard';
  }

  isManager(): boolean {
    const role = (this.auth.userRole() || '').toLowerCase();
    return role === 'manager' || role === 'admin' || this.auth.isManager();
  }

  get resolvedTickets(): TicketSummary[] {
    return (this.dashboardStats?.recent_tickets || []).filter(
      t => t.status === 'resolved' || t.status === 'closed'
    );
  }

  ngOnInit() {
    this.loadDashboard();
  }

  async loadDashboard() {
    try {
      const res = await this.api.get('/api/dashboard/stats');
      if (res.ok) {
        this.dashboardStats = await res.json();
        this.cdr.detectChanges();
      }
    } catch (e) { console.error(e); }
  }

  async deleteResolvedTicket(ticket: TicketSummary, event: Event) {
    event.stopPropagation();
    const confirmed = confirm(`Are you sure you want to permanently delete resolved ticket ${ticket.ticket_number} ("${ticket.title}")?\n\nThis action cannot be undone.`);
    if (!confirmed) return;

    try {
      const res = await this.api.delete(`/api/tickets/${ticket.id}`);
      if (!res.ok) {
        const err = await res.json();
        alert('Error deleting ticket: ' + (err.error?.message || err.detail?.message || 'Failed'));
        return;
      }
      this.loadDashboard();
    } catch (e: any) {
      alert('Error deleting ticket: ' + e.message);
    }
  }

  viewTicketDetails(id: string) {
    this.router.navigate(['/tickets', id]);
  }

  formatStatus(status: string): string {
    return status ? status.replaceAll('_', ' ') : '';
  }
}
