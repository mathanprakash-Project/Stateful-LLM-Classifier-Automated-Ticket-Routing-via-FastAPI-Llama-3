import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';

interface ProcessStage {
  stageNumber: number;
  label: string;
  icon: string;
  desc: string;
  badgeClass: string;
}

@Component({
  selector: 'app-ticket-status',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="ticket-status-page animate-fade">
      
      <!-- PAGE HEADER -->
      <div class="view-header">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="material-symbols-outlined text-purple" style="font-size: 28px;">track_changes</span>
            <h1 class="view-title">Ticket Status & Real-Time Process Tracker</h1>
          </div>
          <p class="view-desc">Live step-by-step workflow lifecycle and operational stages for all your submitted service requests</p>
        </div>
        <div class="flex gap-2">
          <button class="btn btn-outlined" (click)="loadTickets()" title="Refresh Status">
            <span class="material-symbols-outlined">refresh</span>
            <span>Refresh</span>
          </button>
          <button class="btn btn-primary" *ngIf="auth.isUser()" (click)="openCreateTicket()">
            <span class="material-symbols-outlined">add</span>
            <span>New Request</span>
          </button>
        </div>
      </div>

      <!-- METRIC COUNTER CARDS -->
      <div class="status-metrics-grid mb-6">
        <div class="metric-card" [class.active-metric]="selectedStageFilter === 'all'" (click)="setStageFilter('all')">
          <div class="metric-icon-wrap icon-purple">
            <span class="material-symbols-outlined">receipt_long</span>
          </div>
          <div class="metric-info">
            <span class="metric-val">{{ tickets.length }}</span>
            <span class="metric-lbl">Total Requests</span>
          </div>
        </div>

        <div class="metric-card" [class.active-metric]="selectedStageFilter === 'in_progress'" (click)="setStageFilter('in_progress')">
          <div class="metric-icon-wrap icon-blue">
            <span class="material-symbols-outlined">engineering</span>
          </div>
          <div class="metric-info">
            <span class="metric-val">{{ countByStatus(['in_progress', 'assigned', 'approved']) }}</span>
            <span class="metric-lbl">Stage 3: In Progress</span>
          </div>
        </div>

        <div class="metric-card" [class.active-metric]="selectedStageFilter === 'resolved'" (click)="setStageFilter('resolved')">
          <div class="metric-icon-wrap icon-green">
            <span class="material-symbols-outlined">task_alt</span>
          </div>
          <div class="metric-info">
            <span class="metric-val">{{ countByStatus(['resolved']) }}</span>
            <span class="metric-lbl">Stage 4: Resolved & Ready</span>
          </div>
        </div>

        <div class="metric-card" [class.active-metric]="selectedStageFilter === 'closed'" (click)="setStageFilter('closed')">
          <div class="metric-icon-wrap icon-orange">
            <span class="material-symbols-outlined">lock</span>
          </div>
          <div class="metric-info">
            <span class="metric-val">{{ countByStatus(['closed', 'archived']) }}</span>
            <span class="metric-lbl">Stage 5: Closed & Reopenable</span>
          </div>
        </div>
      </div>

      <!-- FILTER & SEARCH BAR -->
      <div class="filters-panel mb-6">
        <div class="search-input-wrap">
          <span class="material-symbols-outlined search-icon">search</span>
          <input 
            type="text" 
            class="search-input" 
            placeholder="Search tickets by number, title, category, or notes..." 
            [(ngModel)]="searchQuery" 
            (input)="applyFilters()"
          >
        </div>

        <div class="filter-controls">
          <select class="form-input filter-select" [(ngModel)]="selectedCategoryFilter" (change)="applyFilters()" title="Filter by Category">
            <option value="">All Application Activities</option>
            <option value="Application UI">Application UI (Online)</option>
            <option value="File Management">File Management (Online)</option>
            <option value="Client Data Transfer">Client Data Transfer (Hybrid)</option>
            <option value="Application Version Maintenance">Application Version Maintenance (Offline)</option>
          </select>

          <select class="form-input filter-select" [(ngModel)]="selectedModeFilter" (change)="applyFilters()" title="Filter by Execution Mode">
            <option value="">All Execution Modes</option>
            <option value="Online">Online (No Downtime)</option>
            <option value="Hybrid">Hybrid (User Lockout)</option>
            <option value="Offline">Offline (Planned Downtime)</option>
          </select>
        </div>
      </div>

      <!-- STAGE TABS -->
      <div class="stage-tabs-row mb-6">
        <button class="stage-tab-btn" [class.active]="selectedStageFilter === 'all'" (click)="setStageFilter('all')">
          All Requests ({{ tickets.length }})
        </button>
        <button class="stage-tab-btn" [class.active]="selectedStageFilter === 'new'" (click)="setStageFilter('new')">
          Stage 1 & 2: Governance / New ({{ countByStatus(['open', 'pending_manager_routing', 'pending_admin_approval']) }})
        </button>
        <button class="stage-tab-btn" [class.active]="selectedStageFilter === 'in_progress'" (click)="setStageFilter('in_progress')">
          Stage 3: Engineering Work ({{ countByStatus(['in_progress', 'assigned', 'approved']) }})
        </button>
        <button class="stage-tab-btn" [class.active]="selectedStageFilter === 'resolved'" (click)="setStageFilter('resolved')">
          Stage 4: Resolved & Verified ({{ countByStatus(['resolved']) }})
        </button>
        <button class="stage-tab-btn" [class.active]="selectedStageFilter === 'reopened'" (click)="setStageFilter('reopened')">
          Reopened ({{ countByStatus(['reopened']) }})
        </button>
        <button class="stage-tab-btn" [class.active]="selectedStageFilter === 'closed'" (click)="setStageFilter('closed')">
          Stage 5: Closed / Archived ({{ countByStatus(['closed', 'archived']) }})
        </button>
      </div>

      <!-- TICKETS LIST OF DETAILED PROCESS CARDS -->
      <div class="tickets-process-list flex flex-col gap-4">
        
        <!-- EMPTY STATE -->
        <div *ngIf="filteredTickets.length === 0" class="empty-state-card">
          <span class="material-symbols-outlined empty-icon">inbox</span>
          <h3 class="empty-title">No service requests found</h3>
          <p class="empty-desc">No tickets match the selected filter criteria or search query.</p>
          <button class="btn btn-outlined mt-3" (click)="resetFilters()">Reset Filters</button>
        </div>

        <!-- TICKET TRACKER CARD -->
        <div *ngFor="let t of filteredTickets" class="process-tracker-card animate-fade" [ngClass]="'border-status-' + t.status">
          
          <!-- CARD HEADER -->
          <div class="ptc-header">
            <div class="ptc-title-group">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="ticket-badge-num">{{ t.ticket_number }}</span>
                <span class="category-chip">{{ t.category_name || t.category?.name || 'Application Support' }}</span>
                <span class="badge-priority" [ngClass]="'priority-' + t.priority">{{ t.priority }}</span>
                <span class="mode-tag" [ngClass]="'mode-' + getExecutionMode(t)">
                  <span class="material-symbols-outlined text-xs">bolt</span>
                  {{ getExecutionMode(t) }}
                </span>
                <span *ngIf="getReopenCount(t) > 0" class="reopen-badge">
                  <span class="material-symbols-outlined text-xs">replay</span>
                  Reopened {{ getReopenCount(t) }}/3
                </span>
              </div>
              <h3 class="ptc-title">{{ t.title }}</h3>
            </div>

            <div class="ptc-actions">
              <button class="btn btn-sm btn-primary" (click)="viewTicket(t.id)">
                <span class="material-symbols-outlined">visibility</span>
                <span>{{ t.status === 'resolved' ? 'Inspect Resolution' : 'View Workflow' }}</span>
              </button>
            </div>
          </div>

          <!-- 5-STEP INTERACTIVE PROGRESS STEPPER -->
          <div class="stepper-wrap">
            <div class="stepper-track">
              
              <!-- STEP 1: AI Triage -->
              <div class="step-item" [ngClass]="getStepClass(t, 1)">
                <div class="step-circle">
                  <span class="material-symbols-outlined">{{ getStepClass(t, 1) === 'completed' ? 'check' : 'smart_toy' }}</span>
                </div>
                <div class="step-meta">
                  <span class="step-name">1. AI Triage</span>
                  <span class="step-sub">Prerequisites Verified</span>
                </div>
              </div>

              <div class="step-line" [class.active-line]="getStepNumber(t.status) >= 2"></div>

              <!-- STEP 2: Governance / Assignment -->
              <div class="step-item" [ngClass]="getStepClass(t, 2)">
                <div class="step-circle">
                  <span class="material-symbols-outlined">{{ getStepClass(t, 2) === 'completed' ? 'check' : 'assignment_ind' }}</span>
                </div>
                <div class="step-meta">
                  <span class="step-name">2. Assignment</span>
                  <span class="step-sub">{{ t.assignee_name ? t.assignee_name : 'Routing & Assignment' }}</span>
                </div>
              </div>

              <div class="step-line" [class.active-line]="getStepNumber(t.status) >= 3"></div>

              <!-- STEP 3: Engineering Work -->
              <div class="step-item" [ngClass]="getStepClass(t, 3)">
                <div class="step-circle">
                  <span class="material-symbols-outlined">{{ getStepClass(t, 3) === 'completed' ? 'check' : 'engineering' }}</span>
                </div>
                <div class="step-meta">
                  <span class="step-name">3. In Progress</span>
                  <span class="step-sub">Active Maintenance</span>
                </div>
              </div>

              <div class="step-line" [class.active-line]="getStepNumber(t.status) >= 4"></div>

              <!-- STEP 4: Verification & Resolution -->
              <div class="step-item" [ngClass]="getStepClass(t, 4)">
                <div class="step-circle">
                  <span class="material-symbols-outlined">{{ getStepClass(t, 4) === 'completed' ? 'check' : 'task_alt' }}</span>
                </div>
                <div class="step-meta">
                  <span class="step-name">4. Resolved</span>
                  <span class="step-sub">Tested & Verified</span>
                </div>
              </div>

              <div class="step-line" [class.active-line]="getStepNumber(t.status) >= 5"></div>

              <!-- STEP 5: Closed & Archived -->
              <div class="step-item" [ngClass]="getStepClass(t, 5)">
                <div class="step-circle">
                  <span class="material-symbols-outlined">{{ t.status === 'closed' || t.status === 'archived' ? 'lock' : 'inventory_2' }}</span>
                </div>
                <div class="step-meta">
                  <span class="step-name">5. Closed</span>
                  <span class="step-sub">2-Mo Retention</span>
                </div>
              </div>

            </div>
          </div>

          <!-- STAGE CALLOUT & ACTION STATUS BANNER -->
          <div class="stage-callout-banner" [ngClass]="'callout-' + t.status">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined callout-icon">{{ getProcessStageInfo(t.status).icon }}</span>
              <div>
                <strong class="callout-title">{{ getProcessStageInfo(t.status).label }}</strong>
                <p class="callout-desc">{{ getProcessStageInfo(t.status).desc }}</p>
              </div>
            </div>

            <!-- Contextual Quick Action Buttons for User -->
            <div class="flex items-center gap-2 flex-wrap" *ngIf="auth.isUser()">
              <button *ngIf="t.status === 'resolved'" class="btn-action-pill btn-action-close" (click)="closeTicket(t)">
                <span class="material-symbols-outlined text-sm">lock</span>
                <span>Confirm & Close</span>
              </button>
              <button *ngIf="(t.status === 'resolved' || t.status === 'closed') && getReopenCount(t) < 3" class="btn-action-pill btn-action-reopen" (click)="openReopenModal(t)">
                <span class="material-symbols-outlined text-sm">replay</span>
                <span>Reopen ({{ getReopenCount(t) }}/3)</span>
              </button>
            </div>
          </div>

          <!-- FOOTER DETAILS -->
          <div class="ptc-footer">
            <div class="footer-item">
              <span class="text-muted">Created:</span>
              <strong class="text-white">{{ formatDate(t.created_at) }}</strong>
            </div>
            <div class="footer-item" *ngIf="t.assignee_name">
              <span class="text-muted">Assigned Engineer:</span>
              <strong class="text-white">{{ t.assignee_name }}</strong>
            </div>
            <div class="footer-item" *ngIf="t.status === 'resolved'">
              <span class="text-muted">Status:</span>
              <span class="text-success font-bold flex items-center gap-1">
                <span class="material-symbols-outlined text-xs">verified</span> Ready for Requester Review
              </span>
            </div>
          </div>

        </div>
      </div>

      <!-- REOPEN WARNING & CONFIRMATION MODAL -->
      <div class="role-modal-backdrop" *ngIf="showReopenDialog" (click)="showReopenDialog = false">
        <div class="role-modal-card animate-pop" (click)="$event.stopPropagation()" style="max-width: 520px;">
          <div class="role-modal-header" style="border-bottom: 1px solid rgba(255, 61, 0, 0.3);">
            <div class="role-modal-title flex items-center gap-2">
              <span class="material-symbols-outlined text-red" style="font-size: 24px;">warning</span>
              <span style="color: var(--corona-red);">Reopen Ticket Confirmation</span>
            </div>
            <button class="icon-close-btn" (click)="showReopenDialog = false">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <div style="padding: 16px 0;">
            <div class="reopen-warning-box mb-3">
              <span class="material-symbols-outlined text-red" style="font-size: 20px;">info</span>
              <div>
                <strong>Reopen Policy Warning (Attempt {{ targetReopenTicket ? getReopenCount(targetReopenTicket) + 1 : 1 }} of 3):</strong>
                <p style="margin: 4px 0 0 0; font-size: 0.82rem; line-height: 1.4;">
                  Please cross-check everything carefully before reopening. You can reopen a ticket a maximum of <strong>3 times</strong>.
                  Reopened tickets follow the standard assignment process with elevated priority attention.
                </p>
              </div>
            </div>

            <label class="form-label mb-1" style="display: block; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted);">
              Detailed Reason for Reopening (Required)
            </label>
            <textarea 
              class="form-textarea" 
              rows="3" 
              placeholder="Provide specific details on why the resolution was incomplete or what issue persists..." 
              [(ngModel)]="reopenReason"
            ></textarea>
            <p *ngIf="reopenError" class="text-danger text-xs mt-1">{{ reopenError }}</p>
          </div>

          <div class="flex justify-end gap-2 pt-3 border-t" style="border-color: var(--corona-border);">
            <button class="btn btn-outlined" (click)="showReopenDialog = false">Cancel</button>
            <button class="btn btn-danger" (click)="executeReopen()" [disabled]="isSubmittingReopen">
              <span class="material-symbols-outlined">replay</span>
              <span>{{ isSubmittingReopen ? 'Reopening...' : 'Confirm & Reopen Ticket' }}</span>
            </button>
          </div>
        </div>
      </div>

    </div>
  `,
  styles: [`
    .ticket-status-page {
      padding: 0 4px;
      color: #ffffff;
    }

    .view-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }
    .view-title {
      font-size: 1.5rem;
      font-weight: 800;
      color: #ffffff;
      margin: 0;
    }
    .view-desc {
      font-size: 0.88rem;
      color: var(--text-muted);
      margin: 4px 0 0 0;
    }

    /* METRICS GRID */
    .status-metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
    }
    .metric-card {
      background: var(--corona-surface);
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 16px;
      display: flex;
      align-items: center;
      gap: 14px;
      cursor: pointer;
      transition: var(--transition);
    }
    .metric-card:hover {
      border-color: var(--corona-purple);
      transform: translateY(-2px);
    }
    .metric-card.active-metric {
      border-color: var(--corona-purple);
      background: rgba(143, 95, 232, 0.08);
      box-shadow: 0 0 12px rgba(143, 95, 232, 0.2);
    }
    .metric-icon-wrap {
      width: 44px;
      height: 44px;
      border-radius: var(--radius-sm);
      display: grid;
      place-items: center;
      font-size: 22px;
    }
    .icon-purple { background: var(--corona-purple-bg); color: var(--corona-purple); }
    .icon-blue { background: var(--corona-blue-bg); color: var(--corona-blue); }
    .icon-green { background: var(--corona-green-bg); color: var(--corona-green); }
    .icon-orange { background: var(--corona-orange-bg); color: var(--corona-orange); }

    .metric-info { display: flex; flex-direction: column; }
    .metric-val { font-size: 1.5rem; font-weight: 800; color: #ffffff; line-height: 1.1; }
    .metric-lbl { font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-top: 2px; }

    /* FILTERS PANEL */
    .filters-panel {
      display: flex;
      align-items: center;
      gap: 14px;
      flex-wrap: wrap;
    }
    .search-input-wrap {
      flex: 1;
      min-width: 280px;
      position: relative;
    }
    .search-icon {
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      font-size: 18px;
    }
    .search-input {
      width: 100%;
      background: #000000;
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 10px 14px 10px 38px;
      color: #ffffff;
      font-size: 0.85rem;
      outline: none;
      transition: var(--transition);
    }
    .search-input:focus { border-color: var(--corona-purple); }
    .filter-controls { display: flex; gap: 10px; flex-wrap: wrap; }
    .filter-select {
      background: #000000;
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 8px 12px;
      color: #ffffff;
      font-size: 0.82rem;
      outline: none;
      cursor: pointer;
    }

    /* STAGE TABS */
    .stage-tabs-row {
      display: flex;
      align-items: center;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 4px;
    }
    .stage-tab-btn {
      background: #000000;
      border: 1px solid var(--corona-border);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: var(--radius-sm);
      font-size: 0.78rem;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      transition: var(--transition);
    }
    .stage-tab-btn:hover { color: #ffffff; border-color: rgba(255, 255, 255, 0.2); }
    .stage-tab-btn.active {
      background: var(--corona-purple-bg);
      border-color: var(--corona-purple);
      color: var(--corona-purple);
    }

    /* PROCESS TRACKER CARD */
    .process-tracker-card {
      background: var(--corona-surface);
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      border-left: 5px solid var(--corona-purple);
      transition: var(--transition);
    }
    .process-tracker-card:hover { border-color: rgba(143, 95, 232, 0.5); }
    .border-status-resolved { border-left-color: var(--corona-green) !important; }
    .border-status-in_progress, .border-status-assigned, .border-status-approved { border-left-color: var(--corona-blue) !important; }
    .border-status-reopened { border-left-color: var(--corona-red) !important; }
    .border-status-closed, .border-status-archived { border-left-color: var(--corona-orange) !important; }

    .ptc-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    .ptc-title-group { flex: 1; min-width: 280px; }
    .ticket-badge-num {
      font-size: 0.85rem;
      font-weight: 800;
      color: var(--corona-purple);
    }
    .category-chip {
      background: #000000;
      border: 1px solid var(--corona-border);
      font-size: 0.72rem;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 4px;
      color: var(--text-muted);
    }
    .badge-priority {
      font-size: 0.7rem;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 4px;
      text-transform: uppercase;
    }
    .priority-low { background: rgba(0, 210, 91, 0.15); color: var(--corona-green); }
    .priority-medium { background: rgba(0, 144, 231, 0.15); color: var(--corona-blue); }
    .priority-high { background: rgba(255, 171, 0, 0.15); color: var(--corona-orange); }
    .priority-critical { background: rgba(252, 66, 74, 0.15); color: var(--corona-red); }

    .mode-tag {
      font-size: 0.68rem;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 4px;
      display: inline-flex;
      align-items: center;
      gap: 3px;
      text-transform: uppercase;
    }
    .mode-Online { background: rgba(0, 210, 91, 0.15); color: var(--corona-green); border: 1px solid rgba(0, 210, 91, 0.3); }
    .mode-Hybrid { background: rgba(143, 95, 232, 0.15); color: var(--corona-purple); border: 1px solid rgba(143, 95, 232, 0.3); }
    .mode-Offline { background: rgba(252, 66, 74, 0.15); color: var(--corona-red); border: 1px solid rgba(252, 66, 74, 0.3); }

    .reopen-badge {
      background: rgba(252, 66, 74, 0.2);
      color: var(--corona-red);
      border: 1px solid var(--corona-red);
      font-size: 0.68rem;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 4px;
      display: inline-flex;
      align-items: center;
      gap: 3px;
    }

    .ptc-title {
      font-size: 1.1rem;
      font-weight: 700;
      color: #ffffff;
      margin: 6px 0 0 0;
    }

    /* STEPPER */
    .stepper-wrap {
      background: #000000;
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 16px;
    }
    .stepper-track {
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: relative;
    }
    .step-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 6px;
      z-index: 2;
      min-width: 90px;
    }
    .step-circle {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #111111;
      border: 2px solid var(--corona-border);
      color: var(--text-muted);
      display: grid;
      place-items: center;
      font-size: 16px;
      transition: var(--transition);
    }
    .step-name { font-size: 0.75rem; font-weight: 700; color: #ffffff; }
    .step-sub { font-size: 0.68rem; color: var(--text-muted); }

    .step-item.completed .step-circle {
      background: var(--corona-green);
      border-color: var(--corona-green);
      color: #000000;
      font-weight: 800;
    }
    .step-item.active .step-circle {
      background: var(--corona-purple);
      border-color: var(--corona-purple);
      color: #ffffff;
      box-shadow: 0 0 10px var(--corona-purple);
      animation: pulseActive 2s infinite;
    }
    .step-item.pending .step-circle {
      background: #090909;
      border-color: var(--corona-border);
      color: var(--text-muted);
    }

    .step-line {
      flex: 1;
      height: 2px;
      background: var(--corona-border);
      margin: 0 8px -18px 8px;
      z-index: 1;
    }
    .step-line.active-line {
      background: var(--corona-green);
      box-shadow: 0 0 6px var(--corona-green);
    }

    /* STAGE CALLOUT */
    .stage-callout-banner {
      background: #000000;
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 12px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .callout-icon { font-size: 22px; }
    .callout-title { font-size: 0.85rem; display: block; }
    .callout-desc { font-size: 0.78rem; color: var(--text-muted); margin: 2px 0 0 0; }

    .callout-resolved {
      border-color: rgba(0, 210, 91, 0.4);
      background: rgba(0, 210, 91, 0.05);
    }
    .callout-resolved .callout-icon, .callout-resolved .callout-title { color: var(--corona-green); }

    .callout-in_progress, .callout-assigned, .callout-approved {
      border-color: rgba(0, 144, 231, 0.4);
      background: rgba(0, 144, 231, 0.05);
    }
    .callout-in_progress .callout-icon, .callout-in_progress .callout-title { color: var(--corona-blue); }

    .callout-reopened {
      border-color: rgba(252, 66, 74, 0.4);
      background: rgba(252, 66, 74, 0.05);
    }
    .callout-reopened .callout-icon, .callout-reopened .callout-title { color: var(--corona-red); }

    .btn-action-pill {
      border-radius: 4px;
      padding: 5px 12px;
      font-size: 0.75rem;
      font-weight: 700;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      cursor: pointer;
      border: none;
      transition: var(--transition);
    }
    .btn-action-close {
      background: var(--corona-green);
      color: #000000;
    }
    .btn-action-close:hover { background: #00bf52; box-shadow: var(--shadow-glow-green); }
    .btn-action-reopen {
      background: rgba(252, 66, 74, 0.15);
      color: var(--corona-red);
      border: 1px solid var(--corona-red);
    }
    .btn-action-reopen:hover { background: var(--corona-red); color: #ffffff; }

    /* FOOTER */
    .ptc-footer {
      display: flex;
      align-items: center;
      gap: 20px;
      font-size: 0.78rem;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      padding-top: 10px;
      flex-wrap: wrap;
    }
    .footer-item { display: flex; align-items: center; gap: 6px; }

    /* REOPEN MODAL */
    .reopen-warning-box {
      background: rgba(252, 66, 74, 0.1);
      border: 1px solid var(--corona-red);
      border-radius: var(--radius-sm);
      padding: 12px;
      display: flex;
      align-items: flex-start;
      gap: 10px;
      color: #ffffff;
    }

    .empty-state-card {
      background: var(--corona-surface);
      border: 1px dashed var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 48px 24px;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .empty-icon { font-size: 48px; color: var(--text-muted); margin-bottom: 12px; }
    .empty-title { font-size: 1.1rem; font-weight: 700; color: #ffffff; margin: 0; }
    .empty-desc { font-size: 0.82rem; color: var(--text-muted); margin: 6px 0 0 0; }

    @keyframes pulseActive {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.08); }
    }
  `]
})
export class TicketStatusComponent implements OnInit {
  api = inject(ApiService);
  auth = inject(AuthService);
  router = inject(Router);
  cdr = inject(ChangeDetectorRef);
  toastService = inject(ToastService);

  tickets: any[] = [];
  filteredTickets: any[] = [];

  searchQuery = '';
  selectedCategoryFilter = '';
  selectedModeFilter = '';
  selectedStageFilter = 'all';

  showReopenDialog = false;
  targetReopenTicket: any = null;
  reopenReason = '';
  reopenError = '';
  isSubmittingReopen = false;

  ngOnInit() {
    this.loadTickets();
  }

  async loadTickets() {
    try {
      const res = await this.api.get('/api/tickets');
      if (res.ok) {
        const data = await res.json();
        this.tickets = Array.isArray(data) ? data : (data.items || []);
        this.applyFilters();
        this.cdr.detectChanges();
      }
    } catch (e) {
      console.error('Failed to load tickets', e);
    }
  }

  applyFilters() {
    let list = [...this.tickets];

    // Search filter
    if (this.searchQuery.trim()) {
      const q = this.searchQuery.toLowerCase();
      list = list.filter(t => 
        (t.ticket_number && t.ticket_number.toLowerCase().includes(q)) ||
        (t.title && t.title.toLowerCase().includes(q)) ||
        (t.description && t.description.toLowerCase().includes(q)) ||
        (t.category_name && t.category_name.toLowerCase().includes(q))
      );
    }

    // Category filter
    if (this.selectedCategoryFilter) {
      list = list.filter(t => {
        const cat = t.category_name || (t.category && t.category.name) || '';
        return cat.toLowerCase().includes(this.selectedCategoryFilter.toLowerCase());
      });
    }

    // Mode filter
    if (this.selectedModeFilter) {
      list = list.filter(t => this.getExecutionMode(t) === this.selectedModeFilter);
    }

    // Stage filter
    if (this.selectedStageFilter === 'new') {
      list = list.filter(t => ['open', 'pending_manager_routing', 'pending_admin_approval'].includes(t.status));
    } else if (this.selectedStageFilter === 'in_progress') {
      list = list.filter(t => ['in_progress', 'assigned', 'approved'].includes(t.status));
    } else if (this.selectedStageFilter === 'resolved') {
      list = list.filter(t => t.status === 'resolved');
    } else if (this.selectedStageFilter === 'reopened') {
      list = list.filter(t => t.status === 'reopened');
    } else if (this.selectedStageFilter === 'closed') {
      list = list.filter(t => ['closed', 'archived'].includes(t.status));
    }

    this.filteredTickets = list;
    this.cdr.detectChanges();
  }

  setStageFilter(stage: string) {
    this.selectedStageFilter = stage;
    this.applyFilters();
  }

  resetFilters() {
    this.searchQuery = '';
    this.selectedCategoryFilter = '';
    this.selectedModeFilter = '';
    this.selectedStageFilter = 'all';
    this.applyFilters();
  }

  countByStatus(statuses: string[]): number {
    return this.tickets.filter(t => statuses.includes(t.status)).length;
  }

  getExecutionMode(ticket: any): string {
    const cat = (ticket.category_name || (ticket.category && ticket.category.name) || '').toLowerCase();
    if (cat.includes('version')) return 'Offline';
    if (cat.includes('transfer') || cat.includes('client')) return 'Hybrid';
    return 'Online';
  }

  getReopenCount(ticket: any): number {
    let count = 0;
    if (ticket.reopened_count !== undefined) return Number(ticket.reopened_count);
    if (ticket.audit_history && Array.isArray(ticket.audit_history)) {
      count = ticket.audit_history.filter((a: any) => a.action === 'reopen_ticket' || (a.details && a.details.includes('reopen'))).length;
    }
    return count;
  }

  getStepNumber(status: string): number {
    switch (status) {
      case 'open':
      case 'pending_manager_routing':
      case 'pending_admin_approval':
        return 2;
      case 'approved':
      case 'assigned':
      case 'in_progress':
      case 'reopened':
        return 3;
      case 'resolved':
        return 4;
      case 'closed':
      case 'archived':
        return 5;
      default:
        return 1;
    }
  }

  getStepClass(ticket: any, stepNum: number): string {
    const currentStep = this.getStepNumber(ticket.status);
    if (currentStep > stepNum) return 'completed';
    if (currentStep === stepNum) return 'active';
    return 'pending';
  }

  getProcessStageInfo(status: string): ProcessStage {
    switch (status) {
      case 'open':
      case 'pending_manager_routing':
      case 'pending_admin_approval':
        return {
          stageNumber: 2,
          label: 'Stage 2: Governance & Assignment in Progress',
          icon: 'shield_person',
          desc: 'Request is undergoing automated governance verification and specialist assignment.',
          badgeClass: 'badge-role-tag role-manager'
        };
      case 'approved':
      case 'assigned':
      case 'in_progress':
        return {
          stageNumber: 3,
          label: 'Stage 3: Engineering Work In Progress',
          icon: 'engineering',
          desc: 'An assigned support engineer has commenced active maintenance on your request.',
          badgeClass: 'badge-role-tag role-employee'
        };
      case 'reopened':
        return {
          stageNumber: 3,
          label: 'Stage 3: Reopened (Elevated Priority Queue)',
          icon: 'replay',
          desc: 'Ticket has been reopened with high priority attention for re-investigation.',
          badgeClass: 'badge-role-tag role-manager'
        };
      case 'resolved':
        return {
          stageNumber: 4,
          label: 'Stage 4: Activity Resolved & Verified',
          icon: 'task_alt',
          desc: 'Support team has completed maintenance and verified operational state. Ready for your review.',
          badgeClass: 'badge-role-tag role-user'
        };
      case 'closed':
        return {
          stageNumber: 5,
          label: 'Stage 5: Activity Closed & Finalized',
          icon: 'lock',
          desc: 'Maintenance request is closed. Reopenable up to 3 times if needed.',
          badgeClass: 'badge-role-tag'
        };
      case 'archived':
        return {
          stageNumber: 5,
          label: 'Stage 5: Activity Archived (2-Month Retention)',
          icon: 'inventory_2',
          desc: 'Ticket archived after 2-month retention period. Ready for instant renewal.',
          badgeClass: 'badge-role-tag'
        };
      default:
        return {
          stageNumber: 1,
          label: 'Stage 1: AI Diagnostic & Prerequisites',
          icon: 'smart_toy',
          desc: 'Request created and verified through conversational triage.',
          badgeClass: 'badge-role-tag'
        };
    }
  }

  formatDate(isoStr: string): string {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoStr;
    }
  }

  viewTicket(id: string) {
    this.router.navigate([`/tickets/${id}`]);
  }

  openCreateTicket() {
    this.router.navigate(['/tickets'], { queryParams: { create: true } });
  }

  async closeTicket(ticket: any) {
    try {
      const res = await this.api.post(`/api/tickets/${ticket.id}/close`, {});
      if (res.ok) {
        this.toastService.show('Ticket Closed', `Ticket #${ticket.ticket_number} marked as closed.`, 'info');
        this.loadTickets();
      }
    } catch (e) {
      console.error('Failed to close ticket', e);
    }
  }

  openReopenModal(ticket: any) {
    this.targetReopenTicket = ticket;
    this.reopenReason = '';
    this.reopenError = '';
    this.showReopenDialog = true;
  }

  async executeReopen() {
    if (!this.targetReopenTicket) return;
    if (!this.reopenReason.trim()) {
      this.reopenError = 'Please provide a detailed reason for reopening.';
      return;
    }

    this.isSubmittingReopen = true;
    this.reopenError = '';

    try {
      const res = await this.api.post(`/api/tickets/${this.targetReopenTicket.id}/reopen`, {
        reason: this.reopenReason.trim()
      });

      this.isSubmittingReopen = false;

      if (res.ok) {
        this.showReopenDialog = false;
        this.toastService.show(
          'Ticket Reopened (Elevated Priority)',
          `Ticket #${this.targetReopenTicket.ticket_number} has been reopened and queued for prompt follow-up.`,
          'warning'
        );
        this.loadTickets();
      } else {
        const err = await res.json();
        this.reopenError = err.detail || 'Failed to reopen ticket.';
      }
    } catch (e: any) {
      this.isSubmittingReopen = false;
      this.reopenError = e.message || 'An error occurred while reopening.';
    }
  }
}

