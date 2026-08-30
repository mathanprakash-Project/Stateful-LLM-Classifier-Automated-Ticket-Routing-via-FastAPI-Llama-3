import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-ticket-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="view-panel animate-fade" *ngIf="selectedTicket">
      <div class="view-header flex justify-between items-center">
        <div class="flex items-center gap-3">
          <button class="icon-btn" (click)="goBack()">
            <span class="material-symbols-outlined">arrow_back</span>
          </button>
          <div class="ticket-header-meta">
            <span class="ticket-lg-num">{{ selectedTicket.ticket_number }}</span>
            <span class="status-badge status-{{ selectedTicket.status }}">{{ formatStatus(selectedTicket.status) }}</span>
            <span class="badge-priority priority-{{ selectedTicket.priority }}">{{ selectedTicket.priority }}</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <!-- Close button for resolved ticket -->
          <button *ngIf="selectedTicket.status === 'resolved'" class="btn btn-sm btn-primary" (click)="closeTicket()" title="Close Ticket">
            <span class="material-symbols-outlined">lock</span>
            <span>Close Ticket</span>
          </button>
          <!-- Reopen button for closed/resolved ticket -->
          <button *ngIf="selectedTicket.status === 'closed'" class="btn btn-sm btn-outlined" (click)="reopenTicket()" title="Reopen Ticket">
            <span class="material-symbols-outlined">replay</span>
            <span>Reopen Ticket</span>
          </button>
          <!-- Delete button for manager/admin when status is resolved/closed -->
          <button *ngIf="isManagerOrAdmin() && (selectedTicket.status === 'resolved' || selectedTicket.status === 'closed')" class="btn btn-sm btn-danger" (click)="deleteTicket()" title="Delete Resolved Ticket (Manager only)">
            <span class="material-symbols-outlined">delete</span>
            <span>Delete Ticket</span>
          </button>
          <!-- Disabled delete indicator when not resolved yet -->
          <button *ngIf="isManagerOrAdmin() && selectedTicket.status !== 'resolved' && selectedTicket.status !== 'closed'" class="btn btn-sm btn-outlined btn-disabled-hint" disabled title="Tickets can only be deleted after they are resolved">
            <span class="material-symbols-outlined">lock</span>
            <span>Delete (Resolve first)</span>
          </button>
        </div>
      </div>

      <div class="card-surface">
        <h2 class="text-xl font-bold mb-2">{{ selectedTicket.title }}</h2>
        <div class="text-muted text-sm mb-4">
          Category: <strong class="text-main">{{ selectedTicket.category?.name || 'General' }}</strong> • 
          Created by: <strong class="text-main">{{ selectedTicket.creator?.full_name || 'User' }}</strong> • 
          Current Assignee: <strong class="text-main">{{ selectedTicket.assignee?.full_name || 'Unassigned' }}</strong>
        </div>

        <!-- Operational Maintenance Metadata Banner -->
        <div class="operational-banner card-subtle p-4 mb-5 animate-fade">
          <div class="flex flex-wrap gap-2 items-center mb-3">
            <span class="activity-badge">
              <span class="material-symbols-outlined">settings_suggest</span>
              {{ selectedTicket.activity_code?.replace('_', ' ') }}
            </span>
            <span class="op-mode-pill mode-{{ (selectedTicket.execution_mode || 'Online') | lowercase }}">
              <span class="material-symbols-outlined">bolt</span>
              Mode: {{ selectedTicket.execution_mode || 'Online' }}
            </span>
            <span class="op-downtime-pill" [class.downtime-warn]="selectedTicket.downtime_required" [class.downtime-lockout]="selectedTicket.execution_mode === 'Hybrid'">
              <span class="material-symbols-outlined">{{ selectedTicket.downtime_required ? 'power_off' : 'lock_clock' }}</span>
              {{ selectedTicket.downtime_required ? 'Planned Downtime' : (selectedTicket.execution_mode === 'Hybrid' ? 'User Lockout' : 'No Downtime') }}
            </span>
            <span *ngIf="selectedTicket.prerequisites_confirmed" class="prereq-badge success">
              <span class="material-symbols-outlined">task_alt</span>
              Prerequisites Verified
            </span>
            <span *ngIf="selectedTicket.downtime_acknowledged" class="prereq-badge success">
              <span class="material-symbols-outlined">event_available</span>
              Downtime Approved
            </span>
            <span *ngIf="selectedTicket.requires_admin_approval" class="restriction-badge warn">
              <span class="material-symbols-outlined">shield_lock</span>
              Admin Approval Required
            </span>
            <span *ngIf="selectedTicket.technical_scope === 'out_of_application_scope'" class="restriction-badge info">
              <span class="material-symbols-outlined">open_in_new</span>
              Outside Application Scope
            </span>
            <span *ngIf="selectedTicket.routed_to_team" class="activity-badge">
              <span class="material-symbols-outlined">route</span>
              Routed: {{ selectedTicket.routed_to_team }}
            </span>
          </div>

          <div class="text-xs text-muted">
            <span *ngIf="selectedTicket.prerequisites_confirmed">Requester confirmed that global compatibility checks, backups, and maintenance windows were verified prior to request.</span>
            <span *ngIf="!selectedTicket.prerequisites_confirmed">Standard maintenance request.</span>
          </div>
        </div>

        <div class="card-subtle p-4 mb-6">
          <h4 class="text-xs uppercase font-bold text-muted mb-2">Description & Scope</h4>
          <p class="whitespace-pre-wrap leading-relaxed">{{ selectedTicket.description }}</p>
        </div>

        <!-- ROLE ACTION PANELS -->

        <!-- 1. ADMIN ACTIONS -->
        <div class="admin-action-panel mb-6 animate-fade" *ngIf="isAdmin() && selectedTicket.status === 'pending_admin_approval'">
          <h4 class="form-label text-warning"><span class="material-symbols-outlined">shield</span> Admin Governance: Review Restricted Operation</h4>
          <p class="text-sm text-muted mb-3">This high-impact operation requires Administrator sign-off. Once approved, assign an Agent (Employee) to execute the work.</p>
          <div class="flex gap-2">
            <button class="btn btn-success" (click)="approveOperation()"><span class="material-symbols-outlined">check_circle</span> Approve Operation</button>
            <button class="btn btn-danger" (click)="rejectOperation()"><span class="material-symbols-outlined">cancel</span> Reject Operation</button>
          </div>
        </div>

        <!-- 2. ADMIN ASSIGNMENT PANEL (For approved tickets or open tickets) -->
        <div class="admin-action-panel mb-6 animate-fade" *ngIf="isAdmin() && selectedTicket.status === 'approved'">
          <h4 class="form-label text-success"><span class="material-symbols-outlined">verified</span> Approved — Ready for Agent Assignment</h4>
          <p class="text-sm text-muted mb-3">Assign this approved maintenance ticket to an Agent (Employee) to perform and complete the activity.</p>
          <div class="flex gap-2 items-center">
            <select class="form-select flex-1" [(ngModel)]="targetAssigneeEmail">
              <option value="">-- Select Agent (Employee) --</option>
              <option *ngFor="let u of availableAgents" [value]="u.id">
                {{ u.name }} ({{ u.email }})
              </option>
            </select>
            <button class="btn btn-primary" (click)="assignToSelectedAgent()" [disabled]="!targetAssigneeEmail">
              <span class="material-symbols-outlined">person_add</span> Assign to Agent
            </button>
          </div>
        </div>

        <!-- 3. MANAGER ROUTING PANEL (For out-of-scope tickets) -->
        <div class="admin-action-panel mb-6 animate-fade" *ngIf="isManagerOrAdmin() && selectedTicket.status === 'pending_manager_routing'">
          <h4 class="form-label text-info"><span class="material-symbols-outlined">alt_route</span> Manager Governance: Out-of-Scope Routing</h4>
          <p class="text-sm text-muted mb-3">This issue is outside Application Support scope. Route it to the appropriate specialized infrastructure team.</p>
          <div class="flex gap-2 items-center">
            <select class="form-select" [(ngModel)]="routeTeam">
              <option value="">-- Select Target Team --</option>
              <option value="INFRASTRUCTURE">Infrastructure / Systems Engineering</option>
              <option value="DATABASE">Database Administrators (DBA)</option>
              <option value="NETWORK">Network Operations & Security</option>
              <option value="SECURITY">Enterprise Infosec & Compliance</option>
              <option value="APPLICATION_SUPPORT">Application Support</option>
            </select>
            <button class="btn btn-primary" (click)="routeTicket()" [disabled]="!routeTeam">
              <span class="material-symbols-outlined">send</span> Route Ticket
            </button>
          </div>
        </div>

        <!-- 4. AGENT (EMPLOYEE) EXECUTION CONTROLS -->
        <div class="admin-action-panel mb-6 animate-fade" *ngIf="isAgentOrStaff() && (selectedTicket.status === 'open' || selectedTicket.status === 'assigned' || selectedTicket.status === 'approved')">
          <h4 class="form-label text-accent"><span class="material-symbols-outlined">engineering</span> Employee / Agent Execution Panel</h4>
          <p class="text-sm text-muted mb-3">Pick up this maintenance activity to start work and progress it through execution.</p>
          <button class="btn btn-primary" (click)="startWork()">
            <span class="material-symbols-outlined">play_arrow</span> Start Work (In Progress)
          </button>
        </div>

        <div class="admin-action-panel mb-6 animate-fade" *ngIf="isAgentOrStaff() && selectedTicket.status === 'in_progress'">
          <h4 class="form-label text-success"><span class="material-symbols-outlined">build_circle</span> Activity In Progress</h4>
          <p class="text-sm text-muted mb-3">Enter operational completion notes to finish the activity and resolve this ticket.</p>
          <div class="flex flex-col gap-2">
            <textarea class="form-textarea" rows="2" placeholder="Describe work completed, verification steps taken..." [(ngModel)]="resolutionNotes"></textarea>
            <div class="flex justify-end gap-2">
              <button class="btn btn-success" (click)="completeWork()">
                <span class="material-symbols-outlined">check_circle</span> Complete & Resolve Ticket
              </button>
            </div>
          </div>
        </div>

        <!-- 5. RESOLVED GOVERNANCE PANEL -->
        <div class="admin-action-panel mb-6 animate-fade" *ngIf="selectedTicket.status === 'resolved'">
          <h4 class="form-label text-success flex items-center gap-2">
            <span class="material-symbols-outlined">task_alt</span> Operational Activity Resolved
          </h4>
          <p class="text-sm text-muted mb-3">This maintenance activity has been completed and verified. You can permanently close the ticket or, as a Manager, delete it.</p>
          <div class="flex gap-2 items-center flex-wrap">
            <button class="btn btn-primary" (click)="closeTicket()">
              <span class="material-symbols-outlined">lock</span> Close Ticket
            </button>
            <button *ngIf="isManagerOrAdmin()" class="btn btn-danger" (click)="deleteTicket()" title="Permanently Delete Ticket">
              <span class="material-symbols-outlined">delete</span> Delete Ticket (Manager)
            </button>
            <button class="btn btn-outlined" (click)="reopenTicket()" title="Reopen Ticket">
              <span class="material-symbols-outlined">replay</span> Reopen Ticket
            </button>
          </div>
        </div>

        <!-- 6. CLOSED TICKET PANEL -->
        <div class="admin-action-panel mb-6 animate-fade" *ngIf="selectedTicket.status === 'closed'">
          <h4 class="form-label text-muted flex items-center gap-2">
            <span class="material-symbols-outlined">lock</span> Ticket Closed & Archived
          </h4>
          <p class="text-sm text-muted mb-3">This ticket is closed. As a Manager, you can permanently delete it or reopen it if needed.</p>
          <div class="flex gap-2 items-center flex-wrap">
            <button *ngIf="isManagerOrAdmin()" class="btn btn-danger" (click)="deleteTicket()" title="Permanently Delete Ticket">
              <span class="material-symbols-outlined">delete</span> Delete Ticket (Manager)
            </button>
            <button class="btn btn-outlined" (click)="reopenTicket()" title="Reopen Ticket">
              <span class="material-symbols-outlined">replay</span> Reopen Ticket
            </button>
          </div>
        </div>

        <!-- Audit History Timeline -->
        <div class="timeline-section">
          <h4 class="text-xs uppercase font-bold text-muted mb-3">Audit History & Timeline</h4>
          <div class="timeline-stream">
            <div *ngFor="let h of selectedTicket.history" class="timeline-node">
              <div class="node-marker"></div>
              <div class="node-content">
                <span class="node-field">{{ h.field_name | uppercase }}:</span>
                <span class="node-old">{{ h.old_value || 'None' }}</span>
                <span class="material-symbols-outlined text-xs">arrow_forward</span>
                <span class="node-new">{{ h.new_value }}</span>
                <div class="node-time">{{ h.created_at | date:'medium' }} by {{ h.changed_by?.full_name || 'System' }}</div>
              </div>
            </div>
            <div *ngIf="!selectedTicket.history?.length" class="text-muted text-sm">No state transitions recorded.</div>
          </div>
        </div>

        <!-- Comments Section -->
        <div class="comments-section mt-6">
          <h4 class="text-xs uppercase font-bold text-muted mb-3">Comments Thread</h4>
          <div class="comments-list">
            <div *ngFor="let c of selectedTicket.comments" class="comment-bubble">
              <div class="comment-header">
                <strong>{{ c.author?.full_name || 'User' }}</strong>
                <span class="text-xs text-muted">{{ c.created_at | date:'short' }}</span>
              </div>
              <p>{{ c.content }}</p>
            </div>
          </div>

          <div class="add-comment-box mt-3 flex gap-2">
            <input type="text" class="form-input flex-1" placeholder="Write a comment or note..." [(ngModel)]="newCommentText" (keydown.enter)="addComment()">
            <button class="btn btn-primary" (click)="addComment()">Comment</button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .view-panel { padding: 28px 36px; max-width: 900px; margin: 0 auto; }
    .view-header { display: flex; align-items: center; margin-bottom: 24px; }
    
    .icon-btn { background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 6px; border-radius: var(--radius-full); display: grid; place-items: center; }
    .icon-btn:hover { background: var(--bg-subtle); color: var(--text-main); }
    
    .ticket-header-meta { display: flex; align-items: center; gap: 12px; }
    .ticket-lg-num { font-size: 1.5rem; font-weight: 700; color: var(--primary); font-family: var(--font-heading); }
    
    .card-surface { background: var(--bg-surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 32px; box-shadow: var(--shadow-sm); }
    .card-subtle { background: var(--bg-subtle); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); }
    .p-4 { padding: 16px; }
    
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
    
    .activity-info-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .activity-badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: var(--radius-full); background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); color: var(--primary); font-size: 0.78rem; font-weight: 700; text-transform: uppercase; }
    .activity-badge .material-symbols-outlined { font-size: 16px; }
    .restriction-badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: var(--radius-full); font-size: 0.78rem; font-weight: 700; }
    .restriction-badge.warn { background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.3); color: #fbbf24; }
    .restriction-badge.info { background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.3); color: #60a5fa; }
    .restriction-badge .material-symbols-outlined { font-size: 16px; }
    .operation-status-badge { display: inline-block; padding: 4px 10px; border-radius: var(--radius-full); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; background: var(--bg-subtle); border: 1px solid var(--border); color: var(--text-dim); }

    .operational-banner { background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-md); }
    .op-mode-pill { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: var(--radius-full); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; background: rgba(99, 102, 241, 0.12); color: var(--primary); border: 1px solid rgba(99, 102, 241, 0.3); }
    .op-mode-pill .material-symbols-outlined { font-size: 14px; }
    .op-downtime-pill { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: var(--radius-full); font-size: 0.72rem; font-weight: 700; background: rgba(16, 185, 129, 0.12); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .op-downtime-pill.downtime-warn { background: rgba(239, 68, 68, 0.12); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .op-downtime-pill.downtime-lockout { background: rgba(245, 158, 11, 0.12); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .op-downtime-pill .material-symbols-outlined { font-size: 14px; }
    .prereq-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: var(--radius-full); font-size: 0.72rem; font-weight: 700; background: rgba(16, 185, 129, 0.12); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .prereq-badge .material-symbols-outlined { font-size: 14px; }

    .admin-action-panel { background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 18px; }
    .admin-action-panel h4 { display: flex; align-items: center; gap: 8px; }
    .admin-action-panel h4 .material-symbols-outlined { font-size: 20px; }

    .btn-success { background: linear-gradient(135deg, var(--success), #059669); color: #fff; border: none; }
    .btn-danger { background: linear-gradient(135deg, var(--danger), #dc2626); color: #fff; border: none; }
    .text-warning { color: var(--warning); }
    .text-info { color: var(--info); }
    .text-success { color: var(--success); }
    
    .badge-priority { font-size: 0.75rem; font-weight: 800; text-transform: uppercase; }
    .priority-low { color: #34d399; }
    .priority-medium { color: #fbbf24; }
    .priority-high { color: #f87171; }
    .priority-critical { color: #ff0055; text-shadow: 0 0 10px rgba(255, 0, 85, 0.4); }
    
    .form-label { display: block; font-size: 0.75rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; margin-bottom: 6px; }
    .form-select, .form-input, .form-textarea { padding: 8px 12px; border-radius: var(--radius-md); background: var(--bg-surface-elevated); border: 1px solid var(--border); color: var(--text-main); font-family: inherit; font-size: 0.88rem; outline: none; }
    .btn { padding: 9px 16px; border-radius: var(--radius-md); font-family: inherit; font-weight: 600; font-size: 0.85rem; border: 1px solid transparent; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; transition: var(--transition); }
    .btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-hover)); color: #fff; }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-outlined { background: transparent; border-color: var(--border); color: var(--text-main); }
    .btn-outlined:hover { background: var(--bg-subtle); }
    .btn-danger { background: #ef4444; color: #fff; border-color: #dc2626; }
    .btn-danger:hover { background: #dc2626; }
    .btn-disabled-hint { opacity: 0.4; cursor: not-allowed; }
    .btn-sm { padding: 7px 12px; font-size: 0.78rem; }
    
    .timeline-stream { border-left: 2px solid var(--border); margin-left: 12px; padding-left: 16px; display: flex; flex-direction: column; gap: 14px; }
    .timeline-node { position: relative; font-size: 0.82rem; }
    .node-marker { position: absolute; left: -21px; top: 4px; width: 8px; height: 8px; border-radius: 50%; background: var(--primary); }
    .node-field { font-weight: 700; color: var(--text-dim); }
    .node-new { font-weight: 700; color: var(--accent); }
    .node-time { font-size: 0.7rem; color: var(--text-dim); margin-top: 2px; }
    
    .comments-list { display: flex; flex-direction: column; gap: 12px; }
    .comment-bubble { background: var(--bg-subtle); padding: 12px 16px; border-radius: var(--radius-md); font-size: 0.88rem; border: 1px solid var(--border-subtle); }
    .comment-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
    
    .text-main { color: var(--text-main); }
    .text-muted { color: var(--text-muted); }
    .text-accent { color: var(--accent); }
    .text-sm { font-size: 0.8rem; }
    .text-xs { font-size: 0.7rem; }
    .text-xl { font-size: 1.25rem; }
    .font-bold { font-weight: 700; }
    .uppercase { text-transform: uppercase; }
    .mb-2 { margin-bottom: 8px; }
    .mb-3 { margin-bottom: 12px; }
    .mb-4 { margin-bottom: 16px; }
    .mb-5 { margin-bottom: 20px; }
    .mb-6 { margin-bottom: 24px; }
    .mt-3 { margin-top: 12px; }
    .mt-6 { margin-top: 24px; }
    .flex { display: flex; }
    .flex-col { flex-direction: column; }
    .flex-wrap { flex-wrap: wrap; }
    .justify-end { justify-content: flex-end; }
    .items-center { align-items: center; }
    .gap-2 { gap: 8px; }
    .gap-3 { gap: 12px; }
    .flex-1 { flex: 1; }
    .whitespace-pre-wrap { white-space: pre-wrap; }
    .leading-relaxed { line-height: 1.6; }
    
    .animate-fade { animation: fadeIn 0.25s ease-out; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  `]
})
export class TicketDetailComponent implements OnInit {
  api = inject(ApiService);
  route = inject(ActivatedRoute);
  router = inject(Router);
  cdr = inject(ChangeDetectorRef);
  auth = inject(AuthService);

  selectedTicket: any = null;
  targetStatus = '';
  targetAssigneeEmail = '';
  newCommentText = '';
  routeTeam = '';
  resolutionNotes = '';

  availableAgents: any[] = [];

  isAdmin(): boolean {
    const role = (this.auth.userRole() || '').toLowerCase();
    return role === 'admin' || this.auth.isAdmin();
  }

  isManagerOrAdmin(): boolean {
    const role = (this.auth.userRole() || '').toLowerCase();
    return role === 'manager' || role === 'admin' || this.auth.isManager();
  }

  isAgentOrStaff(): boolean {
    const role = (this.auth.userRole() || '').toLowerCase();
    return role === 'agent' || role === 'manager' || role === 'admin' || this.auth.isAgent();
  }

  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.loadTicketDetails(id);
      }
    });
    this.loadTeamMembers();
  }

  async loadTeamMembers() {
    try {
      const res = await this.api.get('/api/users/agents');
      if (res.ok) {
        this.availableAgents = await res.json();
      } else {
        // Fallback default agents if endpoint not present
        this.availableAgents = [
          { id: '3c8f8b88-1234-4b5b-8000-000000000002', email: 'bob@company.com', name: 'Bob (Support Agent)' },
          { id: '3c8f8b88-1234-4b5b-8000-000000000003', email: 'alice@company.com', name: 'Alice (Support Manager)' },
          { id: '3c8f8b88-1234-4b5b-8000-000000000001', email: 'admin@company.com', name: 'Admin Root' },
        ];
      }
    } catch (e) {
      this.availableAgents = [
        { id: '3c8f8b88-1234-4b5b-8000-000000000002', email: 'bob@company.com', name: 'Bob (Support Agent)' },
        { id: '3c8f8b88-1234-4b5b-8000-000000000003', email: 'alice@company.com', name: 'Alice (Support Manager)' },
      ];
    }
  }

  goBack() {
    this.router.navigate(['/tickets']);
  }

  async loadTicketDetails(id: string) {
    try {
      const res = await this.api.get(`/api/tickets/${id}`);
      if (res.ok) {
        this.selectedTicket = await res.json();
        this.targetStatus = this.selectedTicket.status;
        this.targetAssigneeEmail = this.selectedTicket.assigned_to_id || '';
        this.cdr.detectChanges();
      }
    } catch (e) { console.error(e); }
  }

  async approveOperation() {
    if (!this.selectedTicket) return;
    try {
      const res = await this.api.post(`/api/tickets/${this.selectedTicket.id}/approve`, {});
      if (!res.ok) {
        const err = await res.json();
        alert(err.error?.message || 'Failed to approve operation');
        return;
      }
      this.loadTicketDetails(this.selectedTicket.id);
    } catch (e: any) { alert(e.message); }
  }

  async rejectOperation() {
    const reason = prompt('Enter rejection reason:');
    if (!reason) return;
    try {
      const res = await this.api.post(`/api/tickets/${this.selectedTicket.id}/reject`, { reason });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error?.message || 'Failed to reject operation');
        return;
      }
      this.loadTicketDetails(this.selectedTicket.id);
    } catch (e: any) { alert(e.message); }
  }

  async assignToSelectedAgent() {
    if (!this.selectedTicket || !this.targetAssigneeEmail) return;
    try {
      const res = await this.api.post(`/api/tickets/${this.selectedTicket.id}/assign`, {
        agent_id: this.targetAssigneeEmail
      });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error?.message || 'Failed to assign ticket');
        return;
      }
      this.loadTicketDetails(this.selectedTicket.id);
    } catch (e: any) { alert(e.message); }
  }

  async startWork() {
    if (!this.selectedTicket) return;
    try {
      const res = await this.api.post(`/api/tickets/${this.selectedTicket.id}/start-work`, {});
      if (!res.ok) {
        const err = await res.json();
        alert(err.error?.message || 'Failed to start work');
        return;
      }
      this.loadTicketDetails(this.selectedTicket.id);
    } catch (e: any) { alert(e.message); }
  }

  async completeWork() {
    if (!this.selectedTicket) return;
    try {
      const res = await this.api.post(`/api/tickets/${this.selectedTicket.id}/complete-work`, {
        notes: this.resolutionNotes || 'Operational maintenance executed and verified successfully.'
      });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error?.message || 'Failed to complete ticket');
        return;
      }
      this.resolutionNotes = '';
      this.loadTicketDetails(this.selectedTicket.id);
    } catch (e: any) { alert(e.message); }
  }

  async routeTicket() {
    if (!this.selectedTicket || !this.routeTeam) return;
    try {
      const res = await this.api.post(`/api/tickets/${this.selectedTicket.id}/route`, { target_team: this.routeTeam });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error?.message || 'Failed to route ticket');
        return;
      }
      this.loadTicketDetails(this.selectedTicket.id);
    } catch (e: any) { alert(e.message); }
  }

  async addComment() {
    if (!this.selectedTicket || !this.newCommentText.trim()) return;
    try {
      const res = await this.api.post(`/api/tickets/${this.selectedTicket.id}/comments`, {
        content: this.newCommentText.trim()
      });
      if (res.ok) {
        this.newCommentText = '';
        this.loadTicketDetails(this.selectedTicket.id);
      }
    } catch (e) { console.error(e); }
  }

  async closeTicket() {
    if (!this.selectedTicket) return;
    try {
      const res = await this.api.patch(`/api/tickets/${this.selectedTicket.id}`, { status: 'closed' });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error?.message || err.detail?.message || 'Failed to close ticket');
        return;
      }
      this.loadTicketDetails(this.selectedTicket.id);
    } catch (e: any) { alert(e.message); }
  }

  async reopenTicket() {
    if (!this.selectedTicket) return;
    try {
      const res = await this.api.patch(`/api/tickets/${this.selectedTicket.id}`, { status: 'reopened' });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error?.message || err.detail?.message || 'Failed to reopen ticket');
        return;
      }
      this.loadTicketDetails(this.selectedTicket.id);
    } catch (e: any) { alert(e.message); }
  }

  async deleteTicket() {
    if (!this.selectedTicket) return;
    const confirmed = confirm(`Are you sure you want to permanently delete ticket ${this.selectedTicket.ticket_number} ("${this.selectedTicket.title}")?\n\nThis action cannot be undone.`);
    if (!confirmed) return;

    try {
      const res = await this.api.delete(`/api/tickets/${this.selectedTicket.id}`);
      if (!res.ok) {
        const err = await res.json();
        alert('Error deleting ticket: ' + (err.error?.message || err.detail?.message || 'Failed to delete ticket'));
        return;
      }
      this.router.navigate(['/tickets']);
    } catch (e: any) {
      alert('Error deleting ticket: ' + e.message);
    }
  }

  formatStatus(status: string): string {
    return status ? status.replaceAll('_', ' ') : '';
  }
}
