import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router, ActivatedRoute } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

interface Category {
  id: string;
  name: string;
  subcategories: { id: string; name: string }[];
}

interface TicketSummary {
  id: string;
  ticket_number: string;
  title: string;
  priority: string;
  status: string;
  category_name?: string;
  assignee_name?: string;
  created_at: string;
}

@Component({
  selector: 'app-ticket-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="view-panel animate-fade">
      <div class="view-header">
        <div>
          <h1 class="view-title">Ticket Registry</h1>
          <p class="view-desc">Filter, inspect, and manage service tickets across departments</p>
        </div>
        <button class="btn btn-primary" *ngIf="auth.isUser()" (click)="openCreateModal()">
          <span class="material-symbols-outlined">add</span>
          <span>Create Ticket</span>
        </button>
      </div>

      <!-- Filters Bar -->
      <div class="filters-bar">
        <div class="search-input-wrap">
          <span class="material-symbols-outlined search-icon">search</span>
          <input type="text" class="search-input" placeholder="Search by title, number, or keyword..." [(ngModel)]="searchQuery" (input)="loadTickets()">
        </div>
        <div class="filter-dropdowns">
          <select class="form-input" [(ngModel)]="statusFilter" (change)="loadTickets()" title="Filter by status">
            <option value="">All Statuses</option>
            <option value="pending_admin_approval">Pending Admin Approval</option>
            <option value="open">Open</option>
            <option value="approved">Approved</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
            <option value="reopened">Reopened</option>
            <option value="archived">Archived (2-Month Retention)</option>
          </select>
        </div>
      </div>

      <!-- Ticket Retention Policy Banner -->
      <div class="retention-info-bar mb-4">
        <span class="material-symbols-outlined retention-icon">inventory_2</span>
        <span class="retention-text">
          <strong>Ticket Retention Policy:</strong> User tickets are actively retained for 2 months, after which they are moved to Archived status. Archived tickets can be renewed and reopened at any time.
        </span>
      </div>

      <!-- Tickets Table -->
      <div class="card-surface">
        <div class="table-container">
          <table class="mat-table">
            <thead>
              <tr>
                <th>Ticket #</th>
                <th>Title</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Assignee</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let t of ticketsList">
                <td><span class="ticket-num">{{ t.ticket_number }}</span></td>
                <td class="font-semibold">{{ t.title }}</td>
                <td><span class="category-chip">{{ t.category_name || 'General' }}</span></td>
                <td><span class="badge-priority priority-{{ t.priority }}">{{ t.priority }}</span></td>
                <td>
                  <div class="flex flex-col gap-1">
                    <span class="status-badge status-{{ t.status }}">{{ formatStatus(t.status) }}</span>
                    <span class="text-xs flex items-center gap-1 font-semibold"
                          [style.color]="t.status === 'resolved' ? 'var(--corona-green)' : (t.status === 'in_progress' ? 'var(--corona-blue)' : (t.status === 'reopened' ? 'var(--corona-red)' : 'var(--text-muted)'))">
                      <span class="material-symbols-outlined" style="font-size: 13px;">{{ getProcessStageIcon(t.status) }}</span>
                      {{ getProcessStageShort(t.status) }}
                    </span>
                  </div>
                </td>
                <td>{{ t.assignee_name || 'Unassigned' }}</td>
                <td>
                  <div class="flex items-center gap-2">
                    <button class="btn btn-sm btn-outlined" (click)="viewTicketDetails(t.id)">Inspect</button>
                    <button *ngIf="isManager() && (t.status === 'resolved' || t.status === 'closed')" class="btn btn-sm btn-danger-outlined" (click)="deleteTicket(t, $event)" title="Delete Resolved Ticket (Manager only)">
                      <span class="material-symbols-outlined text-sm">delete</span>
                      <span>Delete</span>
                    </button>
                    <button *ngIf="isManager() && t.status !== 'resolved' && t.status !== 'closed'" class="btn btn-sm btn-outlined btn-disabled-hint" disabled title="Tickets can only be deleted after they are resolved">
                      <span class="material-symbols-outlined text-sm">lock</span>
                      <span>Delete</span>
                    </button>
                  </div>
                </td>
              </tr>
              <tr *ngIf="!ticketsList.length">
                <td colspan="8" class="empty-state">No tickets matched the active filters.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- CREATE TICKET MODAL -->
    <div *ngIf="showCreateModal" class="modal-backdrop animate-fade">
      <div class="modal-dialog card-surface animate-scale modal-large">
        <div class="modal-header">
          <div>
            <h3 class="modal-title">Create Operational Maintenance Ticket</h3>
            <p class="text-sm text-muted">Select an activity, review prerequisites and downtime impact before submission</p>
          </div>
          <button class="icon-btn" (click)="closeCreateModal()">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <form (ngSubmit)="submitManualTicket()" class="modal-body">
          <!-- 1. Activity Selection -->
          <div class="form-group">
            <label class="form-label">Maintenance Activity</label>
            <select class="form-select font-semibold" [(ngModel)]="newTicket.activity_code" name="activity" (change)="onActivityChange()" required>
              <option value="APPLICATION_UI">Application UI (Online · No Downtime · Priority: Medium)</option>
              <option value="APPLICATION_VERSION">Application Version Maintenance (Offline · Planned Downtime · Priority: Critical)</option>
              <option value="CLIENT_DATA_TRANSFER">Client Data Transfer (Hybrid · User Lockout · Priority: High)</option>
              <option value="FILE_MANAGEMENT">File Management (Online · No Downtime · Priority: Medium)</option>
            </select>
          </div>

          <!-- 2. Operational Metadata & Prerequisite Details Box -->
          <div *ngIf="selectedActivityDef" class="activity-detail-card mb-4 animate-fade">
            <div class="activity-badges-row">
              <span class="activity-mode-badge mode-{{ selectedActivityDef.execution_mode | lowercase }}">
                <span class="material-symbols-outlined">bolt</span>
                Mode: {{ selectedActivityDef.execution_mode }}
              </span>
              <span class="activity-downtime-badge" [class.downtime-warn]="selectedActivityDef.downtime_required" [class.downtime-lockout]="selectedActivityDef.execution_mode === 'Hybrid'">
                <span class="material-symbols-outlined">{{ selectedActivityDef.downtime_required ? 'power_off' : 'lock_clock' }}</span>
                {{ selectedActivityDef.downtime_description }}
              </span>
              <span *ngIf="selectedActivityDef.restricted_operation" class="activity-restricted-badge">
                <span class="material-symbols-outlined">shield_lock</span>
                Admin Approval Required
              </span>
            </div>

            <!-- Customer Explanation & Analogy -->
            <div class="analogy-box">
              <p class="analogy-text"><strong>Overview:</strong> {{ selectedActivityDef.customer_summary }}</p>
              <p *ngIf="selectedActivityDef.customer_analogy" class="analogy-sub"><em>💡 {{ selectedActivityDef.customer_analogy }}</em></p>
            </div>

            <!-- Prerequisites Checklist -->
            <div *ngIf="selectedActivityDef.prerequisites?.length" class="prereq-section">
              <span class="prereq-title"><span class="material-symbols-outlined text-accent">checklist</span> Required Prerequisites:</span>
              <ul class="prereq-list">
                <li *ngFor="let p of selectedActivityDef.prerequisites">
                  <span class="material-symbols-outlined icon-check">check_circle</span>
                  <span>{{ p }}</span>
                </li>
              </ul>
            </div>

            <!-- Risk Warning Callout -->
            <div class="risk-warning-box" *ngIf="selectedActivityDef.risk_warning">
              <span class="material-symbols-outlined text-warning">warning</span>
              <div>
                <strong>Operational Risk Notice:</strong>
                <p class="text-sm mt-1">{{ selectedActivityDef.risk_warning }}</p>
              </div>
            </div>

            <!-- Mandatory Customer Confirmations -->
            <div class="confirmations-box">
              <label class="checkbox-label" *ngIf="selectedActivityDef.prerequisites?.length">
                <input type="checkbox" [(ngModel)]="prerequisitesConfirmed" name="prereqConfirm">
                <span>I confirm that all prerequisites for <strong>{{ selectedActivityDef.activity_name }}</strong> have been verified and completed.</span>
              </label>

              <label class="checkbox-label" *ngIf="selectedActivityDef.downtime_required || selectedActivityDef.execution_mode === 'Hybrid'">
                <input type="checkbox" [(ngModel)]="downtimeAcknowledged" name="downtimeConfirm">
                <span>I acknowledge and approve the scheduled <strong>{{ selectedActivityDef.downtime_description }}</strong> for this activity.</span>
              </label>

              <div class="form-group mt-2 mb-0" *ngIf="selectedActivityDef.downtime_required || selectedActivityDef.execution_mode === 'Hybrid'">
                <label class="form-label text-accent">Approved Maintenance Window / Downtime Schedule</label>
                <input type="text" class="form-input text-sm" placeholder="e.g. Saturday 11:00 PM - Sunday 02:00 AM UTC" [(ngModel)]="newTicket.prerequisites_notes" name="downtimeWindow">
              </div>
            </div>
          </div>

          <!-- 3. Ticket Details -->
          <div class="form-group">
            <label class="form-label">Ticket Title</label>
            <input type="text" class="form-input" placeholder="e.g. Upgrade Application runtime to v5.2 in Production" [(ngModel)]="newTicket.title" name="title" required>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Category</label>
              <select class="form-select" [(ngModel)]="newTicket.category_id" name="category" (change)="onCategoryChange()" required>
                <option value="">-- Select Category --</option>
                <option *ngFor="let c of categories" [value]="c.id">{{ c.name }}</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Priority</label>
              <select class="form-select" [(ngModel)]="newTicket.priority" name="priority">
                <option value="low">Low (Standard Maintenance)</option>
                <option value="medium">Medium (Normal Schedule)</option>
                <option value="high">High (Urgent Scheduled Window)</option>
                <option value="critical">Critical (Emergency Maintenance)</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Description & Change Details</label>
            <textarea class="form-textarea" rows="3" placeholder="Provide operational scope, source/target systems, and execution timeline..." [(ngModel)]="newTicket.description" name="description" required></textarea>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-outlined" (click)="closeCreateModal()">Cancel</button>
            <button type="submit" class="btn btn-primary" [disabled]="!canSubmitTicket()">
              <span class="material-symbols-outlined">send</span>
              Submit Ticket
            </button>
          </div>
        </form>
      </div>
    </div>
  `,
  styles: [`
    .view-panel { padding: 0; }
    .view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
    .view-title { font-family: var(--font-heading); font-size: 1.4rem; font-weight: 800; color: #ffffff; letter-spacing: -0.01em; }
    .view-desc { color: var(--text-muted); font-size: 0.82rem; margin-top: 2px; }
    
    .filters-bar { display: flex; gap: 14px; margin-bottom: 20px; align-items: center; }
    .search-input-wrap { flex: 1; position: relative; display: flex; align-items: center; }
    .search-icon { position: absolute; left: 14px; color: var(--text-muted); }
    .search-input { width: 100%; padding: 10px 16px 10px 42px; border-radius: var(--radius-sm); background: #000000; border: 1px solid var(--corona-border); color: #ffffff; font-family: inherit; font-size: 0.85rem; outline: none; }
    .search-input:focus { border-color: var(--corona-purple); }
    .filter-dropdowns { min-width: 200px; }
    
    .card-surface { background: var(--corona-surface); border: 1px solid var(--corona-border); border-radius: var(--radius-sm); padding: 20px; }
    .table-container { overflow-x: auto; }
    .mat-table { width: 100%; border-collapse: collapse; text-align: left; }
    .mat-table th { padding: 12px 14px; font-size: 0.72rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700; border-bottom: 1px solid var(--corona-border); letter-spacing: 0.05em; }
    .mat-table td { padding: 14px; font-size: 0.85rem; border-bottom: 1px solid rgba(255, 255, 255, 0.03); vertical-align: middle; }
    .mat-table tr:hover td { background: rgba(255, 255, 255, 0.02); }
    
    .ticket-num { font-weight: 700; color: var(--corona-purple); font-family: var(--font-heading); }
    .category-chip { display: inline-block; white-space: nowrap; padding: 4px 10px; border-radius: 4px; background: #000000; border: 1px solid var(--corona-border); font-size: 0.75rem; color: var(--text-light); font-weight: 600; }
    
    .status-badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.68rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; }
    .status-open { background: rgba(255, 171, 0, 0.15); color: var(--corona-orange); }
    .status-assigned { background: rgba(143, 95, 232, 0.15); color: var(--corona-purple); }
    .status-in_progress { background: rgba(0, 144, 231, 0.15); color: var(--corona-blue); }
    .status-escalated { background: rgba(252, 66, 74, 0.15); color: var(--corona-red); }
    .status-resolved { background: rgba(0, 210, 91, 0.15); color: var(--corona-green); }
    .status-closed { background: rgba(108, 114, 147, 0.15); color: var(--text-muted); }
    .status-cancelled { background: rgba(252, 66, 74, 0.15); color: var(--corona-red); }
    .status-pending_manager_routing { background: rgba(255, 171, 0, 0.15); color: var(--corona-orange); }
    .status-pending_admin_approval { background: rgba(252, 66, 74, 0.15); color: var(--corona-red); }
    .status-approved { background: rgba(0, 210, 91, 0.15); color: var(--corona-green); }
    .status-rejected { background: rgba(252, 66, 74, 0.15); color: var(--corona-red); }
    .status-routed { background: rgba(143, 95, 232, 0.15); color: var(--corona-purple); }
    .status-reopened { background: rgba(143, 95, 232, 0.15); color: var(--corona-purple); }
    .status-archived { background: rgba(255, 171, 0, 0.15); color: var(--corona-orange); border: 1px dashed var(--corona-orange); }

    .retention-info-bar {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 16px;
      border-radius: var(--radius-sm);
      background: #000000;
      border: 1px solid var(--corona-border);
      font-size: 0.8rem;
      color: var(--text-muted);
    }
    .retention-icon { color: var(--corona-orange); font-size: 20px; }
    .retention-text strong { color: #ffffff; }
    .mb-4 { margin-bottom: 16px; }
    .priority-low { color: var(--corona-green); }
    .priority-medium { color: var(--corona-orange); }
    .priority-high { color: var(--corona-red); }
    .priority-critical { color: #ff0055; text-shadow: 0 0 8px rgba(255, 0, 85, 0.4); }
    
    .btn { padding: 8px 16px; border-radius: var(--radius-sm); font-family: inherit; font-weight: 600; font-size: 0.85rem; border: 1px solid transparent; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: var(--transition); }
    .btn-primary { background: var(--corona-green); color: #000; font-weight: 700; }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-outlined { background: transparent; border-color: var(--corona-border); color: #ffffff; }
    .btn-outlined:hover { background: rgba(255, 255, 255, 0.05); border-color: var(--corona-purple); }
    .btn-danger-outlined { background: transparent; border-color: rgba(252, 66, 74, 0.3); color: var(--corona-red); }
    .btn-danger-outlined:hover { background: rgba(252, 66, 74, 0.15); border-color: var(--corona-red); }
    .btn-disabled-hint { opacity: 0.4; cursor: not-allowed; }
    .btn-sm { padding: 5px 10px; font-size: 0.75rem; }
    
    .modal-backdrop { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(8px); z-index: 1000; display: grid; place-items: center; padding: 20px; }
    .modal-dialog { width: min(720px, 100%); max-height: 90vh; background: var(--corona-surface); border: 1px solid var(--corona-border); border-radius: var(--radius-sm); display: flex; flex-direction: column; padding: 24px; overflow-y: auto; box-shadow: var(--shadow-card); }
    .modal-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 18px; border-bottom: 1px solid var(--corona-border); padding-bottom: 14px; }
    .modal-title { font-family: var(--font-heading); font-size: 1.2rem; font-weight: 700; color: #ffffff; }
    .icon-btn { background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 6px; border-radius: 4px; display: grid; place-items: center; }
    .icon-btn:hover { color: #ffffff; background: rgba(255, 255, 255, 0.05); }
    
    .activity-detail-card { background: #000000; border: 1px solid var(--corona-border); border-radius: var(--radius-sm); padding: 16px; margin-bottom: 16px; }
    .activity-badges-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
    .activity-mode-badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; background: rgba(143, 95, 232, 0.15); color: var(--corona-purple); border: 1px solid rgba(143, 95, 232, 0.3); }
    .activity-mode-badge .material-symbols-outlined { font-size: 16px; }
    .activity-downtime-badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; background: rgba(0, 210, 91, 0.15); color: var(--corona-green); border: 1px solid rgba(0, 210, 91, 0.3); }
    .activity-downtime-badge.downtime-warn { background: rgba(252, 66, 74, 0.15); color: var(--corona-red); border: 1px solid rgba(252, 66, 74, 0.3); }
    .activity-downtime-badge.downtime-lockout { background: rgba(255, 171, 0, 0.15); color: var(--corona-orange); border: 1px solid rgba(255, 171, 0, 0.3); }
    .activity-downtime-badge .material-symbols-outlined { font-size: 16px; }
    .activity-restricted-badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; background: rgba(255, 171, 0, 0.15); color: var(--corona-orange); border: 1px solid rgba(255, 171, 0, 0.3); }
    .activity-restricted-badge .material-symbols-outlined { font-size: 16px; }
    
    .analogy-box { background: var(--corona-surface); padding: 12px 14px; border-radius: var(--radius-sm); border-left: 3px solid var(--corona-purple); margin-bottom: 12px; font-size: 0.85rem; line-height: 1.5; color: #d1d5db; }
    .analogy-sub { color: var(--text-muted); margin-top: 4px; font-size: 0.78rem; }
    
    .prereq-section { margin-bottom: 12px; }
    .prereq-title { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px; }
    .prereq-title .material-symbols-outlined { font-size: 18px; }
    .prereq-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
    .prereq-list li { display: flex; align-items: flex-start; gap: 8px; font-size: 0.82rem; color: #ffffff; line-height: 1.4; }
    .icon-check { font-size: 16px; color: var(--corona-green); flex-shrink: 0; margin-top: 2px; }
    
    .risk-warning-box { display: flex; align-items: flex-start; gap: 10px; background: rgba(255, 171, 0, 0.08); border: 1px solid rgba(255, 171, 0, 0.3); padding: 10px 14px; border-radius: var(--radius-sm); color: #ffffff; font-size: 0.82rem; margin-bottom: 12px; }
    .risk-warning-box .material-symbols-outlined { font-size: 20px; flex-shrink: 0; color: var(--corona-orange); }
    
    .confirmations-box { display: flex; flex-direction: column; gap: 8px; padding-top: 8px; border-top: 1px solid var(--corona-border); }
    .checkbox-label { display: flex; align-items: flex-start; gap: 10px; font-size: 0.82rem; color: #ffffff; cursor: pointer; line-height: 1.4; }
    .checkbox-label input { margin-top: 3px; accent-color: var(--corona-green); width: 16px; height: 16px; }
    
    .form-group { margin-bottom: 14px; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .form-label { display: block; font-size: 0.72rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; }
    .form-input, .form-textarea, .form-select { width: 100%; padding: 8px 12px; border-radius: var(--radius-sm); background: #000000; border: 1px solid var(--corona-border); color: #ffffff; font-family: inherit; font-size: 0.85rem; outline: none; }
    .modal-footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }
    
    .font-semibold { font-weight: 600; color: #ffffff; }
    .text-muted { color: var(--text-muted); }
    .text-sm { font-size: 0.8rem; }
    .empty-state { text-align: center; color: var(--text-muted); padding: 24px; }
    
    .animate-fade { animation: fadeIn 0.2s ease-out; }
    .animate-scale { animation: scaleIn 0.2s ease-out; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes scaleIn { from { opacity: 0; transform: scale(0.96); } to { opacity: 1; transform: scale(1); } }
  `]
})
export class TicketListComponent implements OnInit {
  api = inject(ApiService);
  auth = inject(AuthService);
  router = inject(Router);
  route = inject(ActivatedRoute);
  cdr = inject(ChangeDetectorRef);

  isManager(): boolean {
    const role = (this.auth.userRole() || '').toLowerCase();
    return role === 'manager' || role === 'admin' || this.auth.isManager();
  }

  ticketsList: TicketSummary[] = [];
  searchQuery = '';
  statusFilter = '';

  showCreateModal = false;
  newTicket = {
    title: '',
    activity_code: 'APPLICATION_UI',
    category_id: '',
    priority: 'medium',
    description: '',
    execution_mode: 'Online',
    downtime_required: false,
    downtime_acknowledged: false,
    prerequisites_confirmed: false,
    prerequisites_notes: '',
  };

  activities: any[] = [];
  selectedActivityDef: any = null;
  prerequisitesConfirmed = false;
  downtimeAcknowledged = false;

  categories: Category[] = [];

  ngOnInit() {
    this.loadTickets();
    this.loadActivities();
    this.route.queryParams.subscribe(params => {
      if (params['create'] === 'true') {
        this.openCreateModal();
        this.router.navigate([], { queryParams: { create: null }, queryParamsHandling: 'merge' });
      }
    });
  }

  async loadActivities() {
    try {
      const res = await this.api.get('/api/categories/activities');
      if (res.ok) {
        this.activities = await res.json();
        this.onActivityChange();
      }
    } catch (e) { console.error(e); }
  }

  async loadTickets() {
    try {
      let url = '/api/tickets?page=1&per_page=50';
      if (this.searchQuery) url += `&search=${encodeURIComponent(this.searchQuery)}`;
      if (this.statusFilter) url += `&status=${encodeURIComponent(this.statusFilter)}`;
      const res = await this.api.get(url);
      if (res.ok) {
        const data = await res.json();
        this.ticketsList = data.items || [];
        this.cdr.detectChanges();
      }
    } catch (e) { console.error(e); }
  }

  viewTicketDetails(id: string) {
    this.router.navigate(['/tickets', id]);
  }

  async openCreateModal() {
    this.showCreateModal = true;
    this.prerequisitesConfirmed = false;
    this.downtimeAcknowledged = false;
    if (this.categories.length === 0) {
      try {
        const res = await this.api.get('/api/categories');
        if (res.ok) {
          this.categories = await res.json();
          if (this.categories.length && !this.newTicket.category_id) {
            this.newTicket.category_id = this.categories[0].id;
          }
        }
      } catch (e) { console.error(e); }
    }
    if (this.activities.length === 0) {
      await this.loadActivities();
    } else {
      this.onActivityChange();
    }
  }

  closeCreateModal() {
    this.showCreateModal = false;
    this.newTicket = {
      title: '',
      activity_code: 'APPLICATION_UI',
      category_id: this.categories[0]?.id || '',
      priority: 'medium',
      description: '',
      execution_mode: 'Online',
      downtime_required: false,
      downtime_acknowledged: false,
      prerequisites_confirmed: false,
      prerequisites_notes: '',
    };
    this.prerequisitesConfirmed = false;
    this.downtimeAcknowledged = false;
  }

  onActivityChange() {
    this.selectedActivityDef = this.activities.find(a => a.activity_code === this.newTicket.activity_code) || null;
    this.prerequisitesConfirmed = false;
    this.downtimeAcknowledged = false;

    if (this.selectedActivityDef) {
      this.newTicket.execution_mode = this.selectedActivityDef.execution_mode;
      this.newTicket.downtime_required = this.selectedActivityDef.downtime_required;

      // Mode-based default priority: Online -> medium, Hybrid -> high, Offline -> critical
      if (this.selectedActivityDef.execution_mode === 'Offline') {
        this.newTicket.priority = 'critical';
        this.newTicket.title = 'Application Version Maintenance';
      } else if (this.selectedActivityDef.execution_mode === 'Hybrid') {
        this.newTicket.priority = 'high';
        this.newTicket.title = 'Client Data Transfer';
      } else {
        this.newTicket.priority = 'medium';
        if (this.newTicket.activity_code === 'FILE_MANAGEMENT') {
          this.newTicket.title = 'File Management Operations';
        } else {
          this.newTicket.title = 'Application UI Maintenance';
        }
      }

      // Map matching category
      if (this.categories.length) {
        const match = this.categories.find(c =>
          c.name.toLowerCase().includes(this.selectedActivityDef.activity_name.toLowerCase().split(' ')[0])
        );
        if (match) this.newTicket.category_id = match.id;
        else this.newTicket.category_id = this.categories[0].id;
      }
    }
  }

  onCategoryChange() {
    // category selection hook
  }

  canSubmitTicket(): boolean {
    if (
      !this.newTicket.title?.trim() ||
      !this.newTicket.category_id ||
      !this.newTicket.priority?.trim() ||
      !this.newTicket.description?.trim()
    ) {
      return false;
    }
    if (this.selectedActivityDef) {
      if (this.selectedActivityDef.prerequisites?.length && !this.prerequisitesConfirmed) {
        return false;
      }
      if ((this.selectedActivityDef.downtime_required || this.selectedActivityDef.execution_mode === 'Hybrid') && !this.downtimeAcknowledged) {
        return false;
      }
    }
    return true;
  }

  async submitManualTicket() {
    if (!this.newTicket.title?.trim()) {
      alert('⚠️ Ticket Title is mandatory.');
      return;
    }
    if (!this.newTicket.category_id) {
      alert('⚠️ Category is mandatory. Please select a category.');
      return;
    }
    if (!this.newTicket.priority) {
      alert('⚠️ Priority is mandatory. Please select a priority level.');
      return;
    }
    if (!this.newTicket.description?.trim()) {
      alert('⚠️ Issue Description is mandatory.');
      return;
    }

    try {
      const payload = {
        ...this.newTicket,
        prerequisites_confirmed: this.prerequisitesConfirmed,
        downtime_acknowledged: this.downtimeAcknowledged,
      };

      const res = await this.api.post('/api/tickets', payload);
      if (!res.ok) {
        const err = await res.json();
        alert('Error creating ticket: ' + (err.error?.message || 'Failed'));
        return;
      }
      this.closeCreateModal();
      this.loadTickets();
    } catch (e: any) { alert(e.message); }
  }

  async deleteTicket(ticket: TicketSummary, event: Event) {
    event.stopPropagation();
    const confirmed = confirm(`Are you sure you want to permanently delete ticket ${ticket.ticket_number} ("${ticket.title}")?\n\nThis action cannot be undone.`);
    if (!confirmed) return;

    try {
      const res = await this.api.delete(`/api/tickets/${ticket.id}`);
      if (!res.ok) {
        const err = await res.json();
        alert('Error deleting ticket: ' + (err.error?.message || err.detail?.message || 'Failed to delete ticket'));
        return;
      }
      this.loadTickets();
    } catch (e: any) {
      alert('Error deleting ticket: ' + e.message);
    }
  }

  getProcessStageShort(status: string): string {
    switch (status) {
      case 'resolved': return 'Resolved';
      case 'in_progress': return 'In Progress';
      case 'assigned': return 'Assigned';
      case 'pending_admin_approval': return 'Approval Required';
      case 'approved': return 'Approved';
      case 'reopened': return 'Reopened';
      case 'closed': return 'Closed';
      default: return 'Queued';
    }
  }

  getProcessStageIcon(status: string): string {
    switch (status) {
      case 'resolved': return 'task_alt';
      case 'in_progress': return 'engineering';
      case 'assigned': return 'assignment_ind';
      case 'pending_admin_approval': return 'shield_lock';
      case 'approved': return 'verified';
      case 'reopened': return 'priority_high';
      case 'closed': return 'check_circle';
      default: return 'pending';
    }
  }

  formatStatus(status: string): string {
    return status ? status.replaceAll('_', ' ') : '';
  }
}
