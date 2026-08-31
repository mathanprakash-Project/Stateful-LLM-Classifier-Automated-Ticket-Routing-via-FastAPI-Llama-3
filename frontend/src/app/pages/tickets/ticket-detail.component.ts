import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';

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
          <p class="text-sm text-muted mb-3">This high-impact operation requires Administrator sign-off. Once approved, assign an Employee to execute the work.</p>
          <div class="flex gap-2">
            <button class="btn btn-success" (click)="approveOperation()"><span class="material-symbols-outlined">check_circle</span> Approve Operation</button>
            <button class="btn btn-danger" (click)="rejectOperation()"><span class="material-symbols-outlined">cancel</span> Reject Operation</button>
          </div>
        </div>

        <!-- 2. ADMIN ASSIGNMENT PANEL (For approved tickets or open tickets) -->
        <div class="admin-action-panel mb-6 animate-fade" *ngIf="isAdmin() && selectedTicket.status === 'approved'">
          <h4 class="form-label text-success"><span class="material-symbols-outlined">verified</span> Approved — Ready for Agent Assignment</h4>
          <p class="text-sm text-muted mb-3">Assign this approved maintenance ticket to an Agent (Employee) to perform and complete the activity.</p>
          <h4 class="form-label text-success"><span class="material-symbols-outlined">verified</span> Approved — Ready for Employee Assignment</h4>
          <p class="text-sm text-muted mb-3">Assign this approved maintenance ticket to an Employee to perform and complete the activity.</p>
          <div class="flex gap-2 items-center">
            <select class="form-select flex-1" [(ngModel)]="targetAssigneeEmail">
              <option value="">-- Select Agent (Employee) --</option>
              <option value="">-- Select Employee --</option>
              <option *ngFor="let u of availableAgents" [value]="u.id">
                {{ u.name }} ({{ u.email }})
              </option>
            </select>
            <button class="btn btn-primary" (click)="assignToSelectedAgent()" [disabled]="!targetAssigneeEmail">
              <span class="material-symbols-outlined">person_add</span> Assign to Employee
            </button>
          </div>
        </div>

        <!-- 3. MANAGER ROUTING PANEL (For out-of-scope tickets) -->
        <div class="admin-action-panel mb-6 animate-fade" *ngIf="isManagerOrAdmin() && selectedTicket.status === 'pending_manager_routing'">
          <h4 class="form-label text-info"><span class="material-symbols-outlined">alt_route</span> Manager Governance: Out-of-Scope Routing</h4>
          <p class="text-sm text-muted mb-3">This issue is outside Application Support scope. Route it to the appropriate specialized infrastructure team.</p>
          <div class="flex gap-2 items-center">
            <select class="form-select" [(ngModel)]="routeTeam">
              <option value="">-- Select Target Team (DB / SM / Infrastructure) --</option>
              <option value="DB">🗄️ DB (Database Administrators / DBA)</option>
              <option value="SM">🖥️ SM (Server Management & Infrastructure)</option>
              <option value="NETWORK">🌐 Network Operations & Security</option>
              <option value="SECURITY">🔒 Enterprise Infosec & Compliance</option>
              <option value="APPLICATION_SUPPORT">💻 Application Support (Re-assign)</option>
            </select>
            <button class="btn btn-primary" (click)="routeTicket()" [disabled]="!routeTeam">
              <span class="material-symbols-outlined">send</span> Route Ticket
            </button>
          </div>
        </div>

        <!-- 3B. ROUTED TICKET STATUS BANNER -->
        <div class="admin-action-panel mb-6 animate-fade" *ngIf="selectedTicket.status === 'routed'">
          <h4 class="form-label text-info flex items-center gap-2">
            <span class="material-symbols-outlined">alt_route</span> Out-of-Scope: Ticket Successfully Routed
          </h4>
          <p class="text-sm text-muted mb-3">This request is outside Application Support scope and has been routed to the <strong>{{ selectedTicket.routed_to_team || 'External Team' }}</strong> team for execution.</p>
          <div class="flex gap-2 items-center flex-wrap" *ngIf="isManagerOrAdmin()">
            <button class="btn btn-outlined" (click)="reopenTicket()" title="Reopen or Reroute Ticket">
              <span class="material-symbols-outlined">replay</span> Reroute / Reopen
            </button>
            <button class="btn btn-danger" (click)="deleteTicket()" title="Permanently Delete Ticket">
              <span class="material-symbols-outlined">delete</span> Delete Ticket (Manager)
            </button>
          </div>
        </div>

        <!-- 4. EMPLOYEE EXECUTION CONTROLS -->
        <div class="admin-action-panel mb-6 animate-fade" *ngIf="isAgentOrStaff() && (selectedTicket.status === 'open' || selectedTicket.status === 'assigned' || selectedTicket.status === 'approved' || selectedTicket.status === 'reopened')">
          <h4 class="form-label text-accent"><span class="material-symbols-outlined">engineering</span> Employee Execution Panel <span *ngIf="selectedTicket.status === 'reopened'" class="badge-role-tag role-manager" style="margin-left: 8px;">Reopened Activity ({{ getReopenCount() }}/2)</span></h4>
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
            <span *ngIf="getReopenCount() > 0" class="badge-role-tag role-manager" style="margin-left: 8px;">Reopened {{ getReopenCount() }}/2 times</span>
          </h4>
          <p class="text-sm text-muted mb-3">This maintenance activity has been completed and verified. You can permanently close the ticket or, as a Manager, delete it.</p>
          <div class="flex gap-2 items-center flex-wrap">
            <button class="btn btn-primary" (click)="closeTicket()">
              <span class="material-symbols-outlined">lock</span> Close Ticket
            </button>
            <button *ngIf="isManagerOrAdmin()" class="btn btn-danger" (click)="deleteTicket()" title="Permanently Delete Ticket">
              <span class="material-symbols-outlined">delete</span> Delete Ticket (Manager)
            </button>
            <button *ngIf="getReopenCount() < 2" class="btn btn-outlined" (click)="reopenTicket()" title="Reopen Ticket (Attempt {{ getReopenCount() + 1 }} of 2)">
              <span class="material-symbols-outlined">replay</span> Reopen Ticket ({{ getReopenCount() }}/2)
            </button>
            <button *ngIf="getReopenCount() >= 2" class="btn btn-outlined btn-disabled-hint" disabled title="Maximum 2 reopens reached">
              <span class="material-symbols-outlined">lock</span> Max Reopens (2/2) Reached
            </button>
          </div>
        </div>

        <!-- 6. CLOSED TICKET PANEL -->
        <div class="admin-action-panel mb-6 animate-fade" *ngIf="selectedTicket.status === 'closed'">
          <h4 class="form-label text-muted flex items-center gap-2">
            <span class="material-symbols-outlined">lock</span> Ticket Closed
            <span *ngIf="getReopenCount() > 0" class="badge-role-tag role-manager" style="margin-left: 8px;">Reopened {{ getReopenCount() }}/2 times</span>
          </h4>
          <p class="text-sm text-muted mb-3">This ticket is closed. As a Manager, you can permanently delete it or reopen it if needed.</p>
          <div class="flex gap-2 items-center flex-wrap">
            <button *ngIf="isManagerOrAdmin()" class="btn btn-danger" (click)="deleteTicket()" title="Permanently Delete Ticket">
              <span class="material-symbols-outlined">delete</span> Delete Ticket (Manager)
            </button>
            <button *ngIf="getReopenCount() < 2" class="btn btn-outlined" (click)="reopenTicket()" title="Reopen Ticket (Attempt {{ getReopenCount() + 1 }} of 2)">
              <span class="material-symbols-outlined">replay</span> Reopen Ticket ({{ getReopenCount() }}/2)
            </button>
            <button *ngIf="getReopenCount() >= 2" class="btn btn-outlined btn-disabled-hint" disabled title="Maximum 2 reopens reached">
              <span class="material-symbols-outlined">lock</span> Max Reopens (2/2) Reached
            </button>
          </div>
        </div>

        <!-- 7. ARCHIVED 2-MONTH RETENTION PANEL -->
        <div class="admin-action-panel mb-6 animate-fade" *ngIf="selectedTicket.status === 'archived'">
          <h4 class="form-label text-warning flex items-center gap-2">
            <span class="material-symbols-outlined">inventory_2</span> Ticket Archived (2-Month Retention Window)
          </h4>
          <p class="text-sm text-muted mb-3">This ticket was retained for 2 months and automatically transitioned to Archived status. You can renew and reopen it at any time to resume support.</p>
          <div class="flex gap-2 items-center flex-wrap">
            <button class="btn btn-primary" (click)="renewTicket()">
              <span class="material-symbols-outlined">restart_alt</span> Renew & Reopen Ticket
            </button>
            <button *ngIf="isManagerOrAdmin()" class="btn btn-danger" (click)="deleteTicket()" title="Permanently Delete Ticket">
              <span class="material-symbols-outlined">delete</span> Delete Ticket (Manager)
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

      <!-- REOPEN CONFIRMATION & CROSS-CHECK MODAL -->
      <div *ngIf="showReopenModal" class="modal-backdrop animate-fade" (click)="showReopenModal = false">
        <div class="modal-dialog card-surface animate-pop" (click)="$event.stopPropagation()" style="max-width: 520px; border: 1px solid var(--corona-orange);">
          <div class="modal-header flex justify-between items-center pb-3 border-b" style="border-color: var(--corona-border);">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined" style="font-size: 26px; color: var(--corona-orange);">warning</span>
              <h3 class="modal-title" style="font-size: 1.1rem; color: #ffffff; margin: 0;">Cross-Check Before Reopen</h3>
            </div>
            <button class="icon-btn" (click)="showReopenModal = false">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <div class="modal-body" style="padding: 18px 0;">
            <div class="p-3 mb-3" style="background: rgba(255, 171, 0, 0.12); border: 1px solid var(--corona-orange); border-radius: var(--radius-sm);">
              <p style="font-size: 0.9rem; font-weight: 700; color: var(--corona-orange); margin: 0 0 6px 0;">
                ⚠️ Please cross-check the ticket before it is reopened!
              </p>
              <p style="font-size: 0.82rem; color: #ffffff; margin: 0; line-height: 1.4;">
                <strong>Policy Notice:</strong> A resolved ticket can only be reopened a <strong>maximum of 2 times</strong>.
                <br />
                This action will be <strong>reopen attempt {{ getReopenCount() + 1 }} of 2</strong>.
              </p>
            </div>

            <p style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.5; margin: 0;">
              Once reopened, support employees can pick up the ticket, perform maintenance again, and resolve it upon verification.
            </p>
          </div>

          <div class="modal-footer flex justify-end gap-2 pt-3 border-t" style="border-color: var(--corona-border);">
            <button class="btn btn-outlined" (click)="showReopenModal = false">Cancel</button>
            <button class="btn btn-primary" (click)="confirmReopen()">
              <span class="material-symbols-outlined">replay</span> Confirm & Reopen Ticket
            </button>
          </div>
        </div>
      </div>

    </div>
  `,
  styles: [`
    .view-panel { padding: 0; max-width: 960px; margin: 0 auto; }
    .view-header { display: flex; align-items: center; margin-bottom: 20px; }
    
    .icon-btn { background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 6px; border-radius: 4px; display: grid; place-items: center; }
    .icon-btn:hover { background: rgba(255, 255, 255, 0.05); color: #ffffff; }
    
    .ticket-header-meta { display: flex; align-items: center; gap: 12px; }
    .ticket-lg-num { font-size: 1.4rem; font-weight: 800; color: var(--corona-purple); font-family: var(--font-heading); }
    
    .card-surface { background: var(--corona-surface); border: 1px solid var(--corona-border); border-radius: var(--radius-sm); padding: 24px; }
    .card-subtle { background: #000000; border: 1px solid var(--corona-border); border-radius: var(--radius-sm); }
    .p-4 { padding: 16px; }
    
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
    
    .activity-info-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .activity-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 4px; background: rgba(143, 95, 232, 0.15); border: 1px solid rgba(143, 95, 232, 0.3); color: var(--corona-purple); font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
    .activity-badge .material-symbols-outlined { font-size: 16px; }
    .restriction-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
    .restriction-badge.warn { background: rgba(255, 171, 0, 0.15); border: 1px solid rgba(255, 171, 0, 0.3); color: var(--corona-orange); }
    .restriction-badge.info { background: rgba(0, 144, 231, 0.15); border: 1px solid rgba(0, 144, 231, 0.3); color: var(--corona-blue); }
    .restriction-badge .material-symbols-outlined { font-size: 16px; }
    .operation-status-badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; background: #000; border: 1px solid var(--corona-border); color: var(--text-muted); }

    .operational-banner { background: #000000; border: 1px solid var(--corona-border); border-radius: var(--radius-sm); }
    .op-mode-pill { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; background: rgba(143, 95, 232, 0.15); color: var(--corona-purple); border: 1px solid rgba(143, 95, 232, 0.3); }
    .op-mode-pill .material-symbols-outlined { font-size: 14px; }
    .op-downtime-pill { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; background: rgba(0, 210, 91, 0.15); color: var(--corona-green); border: 1px solid rgba(0, 210, 91, 0.3); }
    .op-downtime-pill.downtime-warn { background: rgba(252, 66, 74, 0.15); color: var(--corona-red); border: 1px solid rgba(252, 66, 74, 0.3); }
    .op-downtime-pill.downtime-lockout { background: rgba(255, 171, 0, 0.15); color: var(--corona-orange); border: 1px solid rgba(255, 171, 0, 0.3); }
    .op-downtime-pill .material-symbols-outlined { font-size: 14px; }
    .prereq-badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; background: rgba(0, 210, 91, 0.15); color: var(--corona-green); border: 1px solid rgba(0, 210, 91, 0.3); }
    .prereq-badge .material-symbols-outlined { font-size: 14px; }

    .admin-action-panel { background: #000000; border: 1px solid var(--corona-border); border-radius: var(--radius-sm); padding: 18px; }
    .admin-action-panel h4 { display: flex; align-items: center; gap: 8px; color: #ffffff; }
    .admin-action-panel h4 .material-symbols-outlined { font-size: 20px; }

    .btn-success { background: var(--corona-green); color: #000; font-weight: 700; border: none; }
    .btn-danger { background: var(--corona-red); color: #fff; border: none; }
    .text-warning { color: var(--corona-orange); }
    .text-info { color: var(--corona-blue); }
    .text-success { color: var(--corona-green); }
    
    .badge-priority { font-size: 0.72rem; font-weight: 800; text-transform: uppercase; }
    .priority-low { color: var(--corona-green); }
    .priority-medium { color: var(--corona-orange); }
    .priority-high { color: var(--corona-red); }
    .priority-critical { color: #ff0055; text-shadow: 0 0 8px rgba(255, 0, 85, 0.4); }
    
    .form-label { display: block; font-size: 0.72rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; }
    .form-select, .form-input, .form-textarea { padding: 8px 12px; border-radius: var(--radius-sm); background: #000000; border: 1px solid var(--corona-border); color: #ffffff; font-family: inherit; font-size: 0.85rem; outline: none; }
    .btn { padding: 8px 16px; border-radius: var(--radius-sm); font-family: inherit; font-weight: 600; font-size: 0.85rem; border: 1px solid transparent; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: var(--transition); }
    .btn-primary { background: var(--corona-green); color: #000; font-weight: 700; }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-outlined { background: transparent; border-color: var(--corona-border); color: #ffffff; }
    .btn-outlined:hover { background: rgba(255, 255, 255, 0.05); border-color: var(--corona-purple); }
    .btn-danger { background: var(--corona-red); color: #fff; }
    .btn-danger:hover { background: #e6323a; }
    .btn-disabled-hint { opacity: 0.4; cursor: not-allowed; }
    .btn-sm { padding: 5px 10px; font-size: 0.75rem; }
    
    .timeline-stream { border-left: 2px solid var(--corona-border); margin-left: 12px; padding-left: 16px; display: flex; flex-direction: column; gap: 14px; }
    .timeline-node { position: relative; font-size: 0.82rem; }
    .node-marker { position: absolute; left: -21px; top: 4px; width: 8px; height: 8px; border-radius: 50%; background: var(--corona-purple); box-shadow: 0 0 6px var(--corona-purple); }
    .node-field { font-weight: 700; color: var(--text-muted); }
    .node-new { font-weight: 700; color: var(--corona-blue); }
    .node-time { font-size: 0.7rem; color: var(--text-dim); margin-top: 2px; }
    
    .comments-list { display: flex; flex-direction: column; gap: 12px; }
    .comment-bubble { background: #000000; padding: 12px 16px; border-radius: var(--radius-sm); font-size: 0.88rem; border: 1px solid var(--corona-border); color: #ffffff; }
    .comment-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
    
    .text-main { color: #ffffff; }
    .text-muted { color: var(--text-muted); }
    .text-accent { color: var(--corona-blue); }
    .text-sm { font-size: 0.8rem; }
    .text-xs { font-size: 0.7rem; }
    .text-xl { font-size: 1.2rem; }
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
    
    .animate-fade { animation: fadeIn 0.2s ease-out; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  `]
})
export class TicketDetailComponent implements OnInit {
  api = inject(ApiService);
  route = inject(ActivatedRoute);
  router = inject(Router);
  cdr = inject(ChangeDetectorRef);
  auth = inject(AuthService);
  toast = inject(ToastService);

  selectedTicket: any = null;
  targetStatus = '';
  targetAssigneeEmail = '';
  newCommentText = '';
  routeTeam = '';
  resolutionNotes = '';
  showReopenModal = false;

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
          { id: '3c8f8b88-1234-4b5b-8000-000000000002', email: 'bob@company.com', name: 'Employee Bob' },
          { id: '3c8f8b88-1234-4b5b-8000-000000000003', email: 'alice@company.com', name: 'Manager Alice' },
          { id: '3c8f8b88-1234-4b5b-8000-000000000001', email: 'admin@company.com', name: 'Admin Root' },
        ];
      }
    } catch (e) {
      this.availableAgents = [
        { id: '3c8f8b88-1234-4b5b-8000-000000000002', email: 'bob@company.com', name: 'Bob (Support Agent)' },
        { id: '3c8f8b88-1234-4b5b-8000-000000000003', email: 'alice@company.com', name: 'Alice (Support Manager)' },
        { id: '3c8f8b88-1234-4b5b-8000-000000000002', email: 'bob@company.com', name: 'Employee Bob' },
        { id: '3c8f8b88-1234-4b5b-8000-000000000003', email: 'alice@company.com', name: 'Manager Alice' },
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
      const ticketNum = this.selectedTicket.ticket_number;
      const ticketTitle = this.selectedTicket.title;
      const res = await this.api.post(`/api/tickets/${this.selectedTicket.id}/complete-work`, {
        notes: this.resolutionNotes || 'Operational maintenance executed and verified successfully.'
      });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error?.message || 'Failed to complete ticket');
        return;
      }
      this.toast.showResolved(ticketNum, ticketTitle);
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

  getReopenCount(): number {
    return this.selectedTicket?.meta_info?.reopen_count || 0;
  }

  reopenTicket() {
    if (!this.selectedTicket) return;
    const currentCount = this.getReopenCount();
    if (currentCount >= 2) {
      this.toast.show(
        'Reopen Limit Reached',
        `Ticket #${this.selectedTicket.ticket_number} has already reached the maximum limit of 2 reopens and cannot be reopened further.`,
        'error',
        this.selectedTicket.ticket_number
      );
      return;
    }
    this.showReopenModal = true;
  }

  async confirmReopen() {
    this.showReopenModal = false;
    if (!this.selectedTicket) return;
    try {
      const res = await this.api.post(`/api/tickets/${this.selectedTicket.id}/reopen`, {});
      if (!res.ok) {
        const err = await res.json();
        alert(err.error?.message || err.detail?.message || 'Failed to reopen ticket');
        return;
      }
      const newCount = this.getReopenCount() + 1;
      this.toast.show(
        'Ticket Reopened',
        `Ticket #${this.selectedTicket.ticket_number} reopened (Attempt ${newCount} of 2). Please cross-check ticket scope.`,
        'warning',
        this.selectedTicket.ticket_number
      );
      this.loadTicketDetails(this.selectedTicket.id);
    } catch (e: any) { alert(e.message); }
  }

  async renewTicket() {
    if (!this.selectedTicket) return;
    try {
      const res = await this.api.post(`/api/tickets/${this.selectedTicket.id}/renew`, {});
      if (!res.ok) {
        const err = await res.json();
        alert(err.error?.message || err.detail?.message || 'Failed to renew and reopen archived ticket');
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
