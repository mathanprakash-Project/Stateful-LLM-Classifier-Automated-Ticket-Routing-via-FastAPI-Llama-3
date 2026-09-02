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
    <div class="corona-dashboard animate-fade">
      
      <!-- TOP REFRESHING LOOK GRADIENT BANNER -->
      <div class="corona-banner">
        <div class="banner-content">
          <div class="banner-icon-wrap">
            <span class="material-symbols-outlined banner-icon">auto_awesome</span>
          </div>
          <div class="banner-text">
            <h3 class="banner-title">Autonomous SupportHub AI Operations</h3>
            <p class="banner-desc">SupportHub autonomous operations with multi-turn diagnostic triage, prerequisites governance, and real-time SLA metrics!</p>
          </div>
        </div>
        <button class="btn-banner" routerLink="/assistant">
          <span>AI Assistant</span>
          <span class="material-symbols-outlined">arrow_forward</span>
        </button>
      </div>

      <!-- CUSTOMER PROCESS & RESOLUTION TRACKER OVERVIEW (Clean, Un-congested with link to Ticket Status) -->
      <div *ngIf="auth.isUser() && dashboardStats?.recent_tickets?.length" class="corona-card mb-6 animate-fade" style="border: 1px solid var(--corona-border); margin-top: 24px;">
        <div class="card-header pb-2" style="border-bottom: 1px solid var(--corona-border);">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined" style="font-size: 24px; color: var(--corona-purple);">track_changes</span>
            <div>
              <h3 class="card-title" style="margin: 0;">Recent Request Status Overview</h3>
              <span class="card-subtitle">Active request progress tracker • Full workflow available in <strong>Ticket Status</strong></span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button class="btn btn-sm btn-outlined" routerLink="/ticket-status">
              <span class="material-symbols-outlined text-sm">track_changes</span>
              <span>All Status ({{ dashboardStats?.total_tickets || dashboardStats?.recent_tickets?.length }})</span>
            </button>
            <button class="btn-refresh-mini" (click)="loadDashboard()" title="Refresh Status">
              <span class="material-symbols-outlined">refresh</span>
            </button>
          </div>
        </div>

        <div style="padding: 16px 0;" class="flex flex-col gap-3">
          <div *ngFor="let t of (dashboardStats?.recent_tickets || []).slice(0, 2)" class="p-3 rounded flex flex-col md:flex-row justify-between items-start md:items-center gap-3"
               style="background: #000000; border: 1px solid var(--corona-border); border-left: 4px solid;"
               [style.border-left-color]="t.status === 'resolved' ? 'var(--corona-green)' : (t.status === 'in_progress' ? 'var(--corona-blue)' : (t.status === 'reopened' ? 'var(--corona-red)' : 'var(--corona-orange)'))">
            
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1 flex-wrap">
                <span style="font-weight: 800; font-size: 0.85rem; color: var(--corona-purple);">{{ t.ticket_number }}</span>
                <span class="font-bold text-white text-sm">{{ t.title }}</span>
                <span class="category-tag">{{ t.category_name || 'Application Support' }}</span>
              </div>

              <!-- Process Stage Banner -->
              <div class="flex items-center gap-2 mt-2">
                <div class="flex items-center gap-1 px-2 py-1 rounded text-xs font-bold"
                     [style.background]="t.status === 'resolved' ? 'rgba(0, 210, 91, 0.15)' : (t.status === 'in_progress' ? 'rgba(0, 144, 231, 0.15)' : (t.status === 'reopened' ? 'rgba(255, 61, 0, 0.15)' : 'rgba(255, 171, 0, 0.15)'))"
                     [style.color]="t.status === 'resolved' ? 'var(--corona-green)' : (t.status === 'in_progress' ? 'var(--corona-blue)' : (t.status === 'reopened' ? 'var(--corona-red)' : 'var(--corona-orange)'))">
                  <span class="material-symbols-outlined" style="font-size: 16px;">{{ getProcessStageInfo(t.status).icon }}</span>
                  {{ getProcessStageInfo(t.status).label }}
                </div>
                <span class="text-xs text-muted">{{ getProcessStageInfo(t.status).desc }}</span>
              </div>
            </div>

            <div class="flex items-center gap-2">
              <button class="btn btn-sm btn-primary" (click)="viewTicketDetails(t.id)">
                <span class="material-symbols-outlined text-sm">visibility</span>
                <span>{{ t.status === 'resolved' ? 'Inspect Resolution' : 'View Workflow' }}</span>
              </button>
            </div>
          </div>

          <div *ngIf="(dashboardStats?.recent_tickets?.length || 0) > 2" class="text-center pt-2">
            <a routerLink="/ticket-status" class="text-xs text-purple font-bold hover:underline flex items-center justify-center gap-1">
              <span>View all {{ dashboardStats?.recent_tickets?.length }} requests with step-by-step stage tracker</span>
              <span class="material-symbols-outlined text-xs">arrow_forward</span>
            </a>
          </div>
        </div>
      </div>

      <!-- 4-METRIC TOP CARDS GRID -->
      <div class="corona-metrics-grid">
        <!-- Metric 1: Total Tickets -->
        <div class="corona-metric-card">
          <div class="metric-body">
            <div class="metric-main">
              <span class="metric-value">{{ dashboardStats?.total_tickets || 0 }}</span>
            </div>
            <span class="metric-subtitle">Total Service Tickets</span>
          </div>
          <div class="metric-arrow-box arrow-purple">
            <span class="material-symbols-outlined">confirmation_number</span>
          </div>
        </div>

        <!-- Metric 2: Open Workload -->
        <div class="corona-metric-card">
          <div class="metric-body">
            <div class="metric-main">
              <span class="metric-value">{{ dashboardStats?.open_tickets || 0 }}</span>
            </div>
            <span class="metric-subtitle">Active Open Queue</span>
          </div>
          <div class="metric-arrow-box arrow-orange">
            <span class="material-symbols-outlined">pending_actions</span>
          </div>
        </div>

        <!-- Metric 3: In Progress -->
        <div class="corona-metric-card">
          <div class="metric-body">
            <div class="metric-main">
              <span class="metric-value">{{ dashboardStats?.in_progress_tickets || 0 }}</span>
            </div>
            <span class="metric-subtitle">In Progress Execution</span>
          </div>
          <div class="metric-arrow-box arrow-blue">
            <span class="material-symbols-outlined">engineering</span>
          </div>
        </div>

        <!-- Metric 4: Resolved / Closed -->
        <div class="corona-metric-card">
          <div class="metric-body">
            <div class="metric-main">
              <span class="metric-value">{{ (dashboardStats?.resolved_tickets || 0) + (dashboardStats?.closed_tickets || 0) }}</span>
            </div>
            <span class="metric-subtitle">Resolved & Completed</span>
          </div>
          <div class="metric-arrow-box arrow-green">
            <span class="material-symbols-outlined">task_alt</span>
          </div>
        </div>
      </div>

      <!-- MIDDLE DUAL-COLUMN SECTION -->
      <div class="corona-mid-grid">
        
        <!-- COLUMN 1: Operational Activity Breakdown -->
        <div class="corona-card card-distribution">
          <div class="card-header">
            <h3 class="card-title">Activity Breakdown</h3>
            <span class="card-header-badge">Live Operations</span>
          </div>

          <div class="distribution-chart-wrap">
            <div class="donut-chart-container">
              <svg viewBox="0 0 36 36" class="circular-chart">
                <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                <path class="circle-seg seg-orange" stroke-dasharray="35, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                <path class="circle-seg seg-green" stroke-dasharray="30, 100" stroke-dashoffset="-35" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                <path class="circle-seg seg-blue" stroke-dasharray="20, 100" stroke-dashoffset="-65" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                <path class="circle-seg seg-purple" stroke-dasharray="15, 100" stroke-dashoffset="-85" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              </svg>
              <div class="donut-center-text">
                <span class="donut-count">{{ dashboardStats?.total_tickets || 0 }}</span>
                <span class="donut-label">Tickets</span>
              </div>
            </div>
          </div>

          <!-- Activity Legend List -->
          <div class="activity-items-list">
            <div class="activity-row">
              <div class="activity-meta">
                <span class="activity-dot dot-orange"></span>
                <div>
                  <span class="activity-name">Application UI</span>
                  <span class="activity-desc">Screen changes & bugs</span>
                </div>
              </div>
              <span class="activity-tag">Online</span>
            </div>

            <div class="activity-row">
              <div class="activity-meta">
                <span class="activity-dot dot-green"></span>
                <div>
                  <span class="activity-name">Application Versioning</span>
                  <span class="activity-desc">Engine binary upgrades</span>
                </div>
              </div>
              <span class="activity-tag">Offline</span>
            </div>

            <div class="activity-row">
              <div class="activity-meta">
                <span class="activity-dot dot-blue"></span>
                <div>
                  <span class="activity-name">Client Data Transfer</span>
                  <span class="activity-desc">Tenant data migrations</span>
                </div>
              </div>
              <span class="activity-tag">Hybrid</span>
            </div>

            <div class="activity-row">
              <div class="activity-meta">
                <span class="activity-dot dot-purple"></span>
                <div>
                  <span class="activity-name">File Management</span>
                  <span class="activity-desc">Archiving & cleanup</span>
                </div>
              </div>
              <span class="activity-tag">Online</span>
            </div>
          </div>
        </div>

        <!-- COLUMN 2: Open Projects / Recent Tickets List -->
        <div class="corona-card card-recent-requests">
          <div class="card-header">
            <div>
              <h3 class="card-title">Open Service Requests</h3>
              <span class="card-subtitle">Active requests awaiting completion</span>
            </div>
            <button class="btn-refresh-mini" (click)="loadDashboard()" title="Refresh">
              <span class="material-symbols-outlined">refresh</span>
            </button>
          </div>

          <div class="requests-list">
            <div *ngFor="let t of dashboardStats?.recent_tickets?.slice(0, 5); let i = index" class="request-item" (click)="viewTicketDetails(t.id)">
              <div class="req-icon-box" [ngClass]="getAvatarColorClass(i)">
                <span class="material-symbols-outlined">{{ getCategoryIcon(t.category_name) }}</span>
              </div>
              <div class="req-details">
                <span class="req-title">{{ t.title }}</span>
                <span class="req-desc">{{ t.ticket_number }} • {{ t.category_name || 'General Support' }}</span>
              </div>
              <div class="req-status-col">
                <span class="status-pill status-{{ t.status }}">{{ formatStatus(t.status) }}</span>
                <span class="req-priority priority-{{ t.priority }}">{{ t.priority }}</span>
              </div>
            </div>

            <div *ngIf="!dashboardStats?.recent_tickets?.length" class="empty-state">
              <span class="material-symbols-outlined">task</span>
              <p>No active service requests right now.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- BOTTOM COMPREHENSIVE TICKET REGISTRY TABLE -->
      <div class="corona-card mt-6">
        <div class="card-header">
          <div>
            <h3 class="card-title">Ticket Activity Registry</h3>
            <span class="card-subtitle">Real-time log of customer requests, approvals, and resolutions</span>
          </div>
          <a routerLink="/tickets" class="view-all-link">View All Tickets →</a>
        </div>

        <div class="corona-table-wrap">
          <table class="corona-table">
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
                <td class="col-num">{{ t.ticket_number }}</td>
                <td class="col-title font-semibold">{{ t.title }}</td>
                <td><span class="category-tag">{{ t.category_name || 'Application Support' }}</span></td>
                <td>
                  <span class="priority-badge priority-{{ t.priority }}">{{ t.priority }}</span>
                </td>
                <td>
                  <span class="status-badge status-{{ t.status }}">{{ formatStatus(t.status) }}</span>
                </td>
                <td class="text-muted">{{ t.creator_name || 'System' }}</td>
                <td>
                  <div class="table-actions">
                    <button class="btn-table-inspect" (click)="viewTicketDetails(t.id)">Inspect</button>
                    <button *ngIf="isManager() && (t.status === 'resolved' || t.status === 'closed')"
                            class="btn-table-delete" (click)="deleteResolvedTicket(t, $event)" title="Delete Resolved Ticket">
                      <span class="material-symbols-outlined">delete</span>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  `,
  styles: [`
    .corona-dashboard {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    /* TOP GRADIENT BANNER */
    .corona-banner {
      background: linear-gradient(90deg, #ff4081 0%, #e040fb 50%, #7c4dff 100%);
      border-radius: var(--radius-sm);
      padding: 20px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 4px 20px rgba(224, 64, 251, 0.25);
    }

    .banner-content {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .banner-icon-wrap {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.2);
      display: grid;
      place-items: center;
      color: #ffffff;
    }
    .banner-icon { font-size: 26px; }

    .banner-text {
      display: flex;
      flex-direction: column;
    }

    .banner-title {
      font-size: 1.15rem;
      font-weight: 800;
      color: #ffffff;
      margin-bottom: 2px;
    }

    .banner-desc {
      font-size: 0.82rem;
      color: rgba(255, 255, 255, 0.9);
      max-width: 600px;
    }

    .btn-banner {
      background-color: rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.4);
      color: #ffffff;
      font-weight: 700;
      font-size: 0.82rem;
      padding: 8px 18px;
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: var(--transition);
      white-space: nowrap;
    }
    .btn-banner:hover {
      background-color: #ffffff;
      color: #000000;
    }

    /* 4-METRIC TOP CARDS GRID */
    .corona-metrics-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }

    .corona-metric-card {
      background-color: var(--corona-surface);
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 18px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      transition: var(--transition);
    }
    .corona-metric-card:hover {
      border-color: var(--corona-purple);
      transform: translateY(-2px);
    }

    .metric-body {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .metric-main {
      display: flex;
      align-items: baseline;
      gap: 8px;
    }

    .metric-value {
      font-size: 1.65rem;
      font-weight: 800;
      color: #ffffff;
      font-family: var(--font-heading);
    }

    .metric-trend {
      font-size: 0.75rem;
      font-weight: 700;
    }
    .trend-up { color: var(--corona-green); }
    .trend-down { color: var(--corona-red); }

    .metric-subtitle {
      font-size: 0.78rem;
      color: var(--text-muted);
      font-weight: 500;
    }

    .metric-arrow-box {
      width: 36px;
      height: 36px;
      border-radius: var(--radius-sm);
      display: grid;
      place-items: center;
      font-size: 18px;
    }
    .arrow-green {
      background-color: var(--corona-green-bg);
      color: var(--corona-green);
    }
    .arrow-red {
      background-color: var(--corona-red-bg);
      color: var(--corona-red);
    }
    .arrow-purple {
      background-color: var(--corona-purple-bg);
      color: var(--corona-purple);
    }
    .arrow-orange {
      background-color: var(--corona-orange-bg);
      color: var(--corona-orange);
    }
    .arrow-blue {
      background-color: var(--corona-blue-bg);
      color: var(--corona-blue);
    }

    /* MIDDLE DUAL-COLUMN */
    .corona-mid-grid {
      display: grid;
      grid-template-columns: 1fr 1.6fr;
      gap: 20px;
    }

    .corona-card {
      background-color: var(--corona-surface);
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 22px;
    }

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 18px;
    }

    .card-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: #ffffff;
    }

    .card-subtitle {
      display: block;
      font-size: 0.78rem;
      color: var(--text-muted);
    }

    .card-header-badge {
      font-size: 0.7rem;
      font-weight: 700;
      background: rgba(0, 210, 91, 0.15);
      color: var(--corona-green);
      padding: 3px 8px;
      border-radius: 4px;
    }

    /* CIRCULAR DONUT CHART */
    .distribution-chart-wrap {
      display: flex;
      justify-content: center;
      margin: 10px 0 20px 0;
    }

    .donut-chart-container {
      position: relative;
      width: 140px;
      height: 140px;
    }

    .circular-chart {
      display: block;
      width: 100%;
      height: 100%;
    }

    .circle-bg {
      fill: none;
      stroke: #12151e;
      stroke-width: 3.8;
    }

    .circle-seg {
      fill: none;
      stroke-width: 3.8;
      stroke-linecap: round;
      transition: stroke-dasharray 0.3s ease;
    }
    .seg-orange { stroke: var(--corona-orange); }
    .seg-green { stroke: var(--corona-green); }
    .seg-blue { stroke: var(--corona-blue); }
    .seg-purple { stroke: var(--corona-purple); }

    .donut-center-text {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
      display: flex;
      flex-direction: column;
    }

    .donut-count {
      font-size: 1.4rem;
      font-weight: 800;
      color: #ffffff;
      line-height: 1;
    }

    .donut-label {
      font-size: 0.65rem;
      text-transform: uppercase;
      color: var(--text-muted);
      font-weight: 700;
    }

    /* ACTIVITY LEGEND LIST */
    .activity-items-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
      border-top: 1px solid var(--corona-border);
      padding-top: 16px;
    }

    .activity-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .activity-meta {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .activity-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
    .dot-orange { background-color: var(--corona-orange); }
    .dot-green { background-color: var(--corona-green); }
    .dot-blue { background-color: var(--corona-blue); }
    .dot-purple { background-color: var(--corona-purple); }

    .activity-name {
      display: block;
      font-size: 0.82rem;
      font-weight: 700;
      color: #ffffff;
    }

    .activity-desc {
      display: block;
      font-size: 0.72rem;
      color: var(--text-muted);
    }

    .activity-tag {
      font-size: 0.7rem;
      font-weight: 700;
      color: var(--text-muted);
      background: #000000;
      border: 1px solid var(--corona-border);
      padding: 2px 8px;
      border-radius: 4px;
    }

    /* RECENT REQUESTS LIST */
    .requests-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .request-item {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 10px 12px;
      border-radius: var(--radius-sm);
      background-color: #000000;
      border: 1px solid var(--corona-border);
      cursor: pointer;
      transition: var(--transition);
    }
    .request-item:hover {
      border-color: var(--corona-purple);
      background-color: #0d0f15;
    }

    .req-icon-box {
      width: 38px;
      height: 38px;
      border-radius: var(--radius-sm);
      display: grid;
      place-items: center;
      font-size: 20px;
      flex-shrink: 0;
    }
    .bg-avatar-0 { background: rgba(0, 144, 231, 0.2); color: var(--corona-blue); }
    .bg-avatar-1 { background: rgba(0, 210, 91, 0.2); color: var(--corona-green); }
    .bg-avatar-2 { background: rgba(143, 95, 232, 0.2); color: var(--corona-purple); }
    .bg-avatar-3 { background: rgba(252, 66, 74, 0.2); color: var(--corona-red); }
    .bg-avatar-4 { background: rgba(255, 171, 0, 0.2); color: var(--corona-orange); }

    .req-details {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 2px;
      overflow: hidden;
    }

    .req-title {
      font-size: 0.85rem;
      font-weight: 700;
      color: #ffffff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .req-desc {
      font-size: 0.72rem;
      color: var(--text-muted);
    }

    .req-status-col {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 2px;
    }

    .status-pill {
      font-size: 0.65rem;
      font-weight: 800;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
    }
    .status-open { background: rgba(255, 171, 0, 0.2); color: var(--corona-orange); }
    .status-in_progress { background: rgba(0, 144, 231, 0.2); color: var(--corona-blue); }
    .status-resolved { background: rgba(0, 210, 91, 0.2); color: var(--corona-green); }
    .status-closed { background: rgba(108, 114, 147, 0.2); color: var(--text-muted); }
    .status-routed { background: rgba(143, 95, 232, 0.2); color: var(--corona-purple); }
    .status-pending_manager_routing { background: rgba(255, 171, 0, 0.2); color: var(--corona-orange); }
    .status-pending_admin_approval { background: rgba(252, 66, 74, 0.2); color: var(--corona-red); }
    .status-approved { background: rgba(0, 210, 91, 0.2); color: var(--corona-green); }

    .req-priority {
      font-size: 0.65rem;
      font-weight: 800;
      text-transform: uppercase;
    }
    .priority-low { color: var(--corona-green); }
    .priority-medium { color: var(--corona-orange); }
    .priority-high { color: var(--corona-red); }
    .priority-critical { color: #ff0055; text-shadow: 0 0 6px rgba(255, 0, 85, 0.4); }

    .btn-refresh-mini {
      background: transparent;
      border: 1px solid var(--corona-border);
      color: var(--text-muted);
      cursor: pointer;
      border-radius: 4px;
      padding: 4px;
      display: grid;
      place-items: center;
    }
    .btn-refresh-mini:hover { color: #ffffff; border-color: var(--corona-purple); }

    /* TABLE SECTION */
    .view-all-link {
      color: var(--corona-green);
      font-size: 0.8rem;
      font-weight: 700;
      text-decoration: none;
    }
    .view-all-link:hover { text-decoration: underline; }

    .corona-table-wrap {
      overflow-x: auto;
      margin-top: 10px;
    }

    .corona-table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }

    .corona-table th {
      padding: 12px 14px;
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      border-bottom: 1px solid var(--corona-border);
      font-weight: 700;
    }

    .corona-table td {
      padding: 14px;
      font-size: 0.85rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.03);
      vertical-align: middle;
    }

    .corona-table tr:hover td {
      background-color: rgba(255, 255, 255, 0.02);
    }

    .col-num {
      color: var(--corona-purple);
      font-weight: 700;
    }

    .category-tag {
      background: #000000;
      border: 1px solid var(--corona-border);
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      color: var(--text-light);
    }

    .status-badge {
      font-size: 0.68rem;
      font-weight: 800;
      text-transform: uppercase;
      padding: 4px 8px;
      border-radius: 4px;
    }

    .priority-badge {
      font-size: 0.72rem;
      font-weight: 800;
      text-transform: uppercase;
    }

    .table-actions {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .btn-table-inspect {
      background: transparent;
      border: 1px solid var(--corona-border);
      color: #ffffff;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 4px;
      cursor: pointer;
      transition: var(--transition);
    }
    .btn-table-inspect:hover {
      background: var(--corona-purple);
      border-color: var(--corona-purple);
    }

    .btn-table-delete {
      background: rgba(252, 66, 74, 0.15);
      border: 1px solid rgba(252, 66, 74, 0.3);
      color: var(--corona-red);
      border-radius: 4px;
      padding: 3px;
      cursor: pointer;
      display: grid;
      place-items: center;
    }
    .btn-table-delete:hover {
      background: var(--corona-red);
      color: #fff;
    }

    .empty-state {
      text-align: center;
      padding: 24px;
      color: var(--text-muted);
    }

    .animate-fade {
      animation: fadeIn 0.2s ease-out;
    }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .mt-6 { margin-top: 24px; }
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

  getProcessStageInfo(status: string): { label: string; desc: string; step: number; icon: string } {
    switch (status) {
      case 'resolved':
        return {
          label: 'Stage 4: Activity Resolved & Verified',
          desc: 'Support team has completed maintenance and verified operational state. Ready for your review.',
          step: 4,
          icon: 'task_alt'
        };
      case 'in_progress':
        return {
          label: 'Stage 3: Active Maintenance in Progress',
          desc: 'Assigned Support Employee is actively performing operational steps.',
          step: 3,
          icon: 'engineering'
        };
      case 'assigned':
        return {
          label: 'Stage 2: Assigned to Support Employee',
          desc: 'Ticket assigned to support personnel and queued for execution.',
          step: 2,
          icon: 'assignment_ind'
        };
      case 'pending_admin_approval':
        return {
          label: 'Stage 1: Pending Admin Governance Approval',
          desc: 'High-impact operation awaiting Administrator authorization.',
          step: 1,
          icon: 'shield_lock'
        };
      case 'approved':
        return {
          label: 'Stage 2: Approved — Ready for Assignment',
          desc: 'Admin has signed off. The ticket is ready to be assigned to a support employee.',
          step: 2,
          icon: 'verified'
        };
      case 'reopened':
        return {
          label: 'Stage 3: Reopened — Urgent Priority Follow-Up',
          desc: 'Customer requested re-verification. Reopened with elevated HIGH priority.',
          step: 3,
          icon: 'priority_high'
        };
      case 'closed':
        return {
          label: 'Stage 5: Activity Closed & Archived',
          desc: 'Maintenance completed and closed.',
          step: 5,
          icon: 'check_circle'
        };
      default:
        return {
          label: 'Stage 1: Request Created & Queued',
          desc: 'Submitted and queued for initial review and routing.',
          step: 1,
          icon: 'pending'
        };
    }
  }

  getAvatarColorClass(index: number): string {
    return `bg-avatar-${index % 5}`;
  }

  getCategoryIcon(category?: string): string {
    if (!category) return 'description';
    const c = category.toLowerCase();
    if (c.includes('ui')) return 'palette';
    if (c.includes('version')) return 'cloud_sync';
    if (c.includes('data')) return 'swap_horiz';
    if (c.includes('file')) return 'folder';
    if (c.includes('database')) return 'database';
    return 'description';
  }
}
