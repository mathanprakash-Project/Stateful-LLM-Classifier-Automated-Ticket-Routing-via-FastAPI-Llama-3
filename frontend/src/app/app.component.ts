import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface User {
  email: string;
  name: string;
  role: string;
}

interface Category {
  id: string;
  name: string;
  description?: string;
  subcategories: { id: string; name: string }[];
}

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
  recent_tickets: TicketSummary[];
}

interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
  displayedContent?: string;
  isStreaming?: boolean;
  draft?: any;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="app-shell" [class.dark]="isDarkTheme" [class.light]="!isDarkTheme">
      
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
          <button class="icon-btn theme-toggle" (click)="toggleTheme()" [title]="isDarkTheme ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
            <span class="material-symbols-outlined">{{ isDarkTheme ? 'light_mode' : 'dark_mode' }}</span>
          </button>

          <!-- User Role Switcher -->
          <div class="user-selector-wrapper">
            <span class="material-symbols-outlined user-icon">account_circle</span>
            <select class="user-dropdown" [ngModel]="currentUser.email" (ngModelChange)="switchUser($event)">
              <option *ngFor="let u of availableUsers" [value]="u.email">
                {{ u.name }} ({{ u.role | uppercase }})
              </option>
            </select>
          </div>
        </div>
      </header>

      <!-- BODY CONTAINER -->
      <div class="app-body">
        
        <!-- SIDEBAR -->
        <aside class="app-sidebar">
          <nav class="sidebar-nav">
            <button class="nav-item" [class.active]="activeTab === 'dashboard'" (click)="setTab('dashboard')">
              <span class="material-symbols-outlined">dashboard</span>
              <span>Dashboard</span>
            </button>
            <button class="nav-item" [class.active]="activeTab === 'tickets'" (click)="setTab('tickets')">
              <span class="material-symbols-outlined">confirmation_number</span>
              <span>All Tickets</span>
              <span class="nav-count" *ngIf="dashboardStats?.total_tickets">{{ dashboardStats?.total_tickets }}</span>
            </button>
            <button class="nav-item" [class.active]="activeTab === 'chat'" (click)="setTab('chat')">
              <span class="material-symbols-outlined">smart_toy</span>
              <span>AI Assistant</span>
              <span class="nav-badge-ai">GPT 120B</span>
            </button>
          </nav>

          <div class="sidebar-action">
            <button class="btn-create-ticket" (click)="openCreateModal()">
              <span class="material-symbols-outlined">add_circle</span>
              <span>New Ticket</span>
            </button>
          </div>

          <div class="sidebar-footer">
            <div class="current-user-card">
              <div class="avatar">{{ currentUser.name.charAt(0) }}</div>
              <div class="user-meta">
                <span class="user-name">{{ currentUser.name }}</span>
                <span class="user-role-badge badge-{{ currentUser.role }}">{{ currentUser.role }}</span>
              </div>
            </div>
          </div>
        </aside>

        <!-- MAIN VIEW AREA -->
        <main class="app-content">

          <!-- ================= DASHBOARD VIEW ================= -->
          <section *ngIf="activeTab === 'dashboard'" class="view-panel animate-fade">
            <div class="view-header">
              <div>
                <h1 class="view-title">System Overview & Analytics</h1>
                <p class="view-desc">Live status of support operations, SLA metrics, and incoming workload</p>
              </div>
              <button class="btn btn-outlined" (click)="loadDashboard()">
                <span class="material-symbols-outlined">refresh</span>
                <span>Refresh</span>
              </button>
            </div>

            <!-- KPI Metric Cards -->
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
            </div>

            <!-- Recent Activity Table -->
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
                        <button class="btn btn-sm btn-outlined" (click)="viewTicketDetails(t.id)">Inspect</button>
                      </td>
                    </tr>
                    <tr *ngIf="!dashboardStats?.recent_tickets?.length">
                      <td colspan="7" class="empty-state">No recent activity found.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <!-- ================= ALL TICKETS REGISTRY VIEW ================= -->
          <section *ngIf="activeTab === 'tickets'" class="view-panel animate-fade">
            <div class="view-header">
              <div>
                <h1 class="view-title">Ticket Registry</h1>
                <p class="view-desc">Filter, inspect, and manage service tickets across departments</p>
              </div>
              <button class="btn btn-primary" (click)="openCreateModal()">
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
                <select class="mat-select" [(ngModel)]="statusFilter" (change)="loadTickets()">
                  <option value="">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="assigned">Assigned</option>
                  <option value="in_progress">In Progress</option>
                  <option value="escalated">Escalated</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
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
                      <td><span class="status-badge status-{{ t.status }}">{{ formatStatus(t.status) }}</span></td>
                      <td>{{ t.assignee_name || 'Unassigned' }}</td>
                      <td class="text-muted text-sm">{{ t.created_at | date:'shortDate' }}</td>
                      <td>
                        <button class="btn btn-sm btn-outlined" (click)="viewTicketDetails(t.id)">Inspect</button>
                      </td>
                    </tr>
                    <tr *ngIf="!ticketsList.length">
                      <td colspan="8" class="empty-state">No tickets matched the active filters.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <!-- ================= AI ASSISTANT CHAT VIEW ================= -->
          <section *ngIf="activeTab === 'chat'" class="view-panel animate-fade h-full flex flex-col">
            <div class="chat-container card-surface">
              <!-- Chat Top Header -->
              <div class="chat-header">
                <div class="chat-agent-info">
                  <div class="agent-avatar">
                    <span class="material-symbols-outlined">psychology</span>
                  </div>
                  <div>
                    <h3 class="agent-name">IT Triage AI Agent <span class="model-badge">gpt-oss:120b-cloud</span></h3>
                    <span class="agent-sub">LangGraph Multi-Turn Diagnostic Workflow</span>
                  </div>
                </div>
                <button class="btn btn-sm btn-outlined" (click)="startNewChatSession()">
                  <span class="material-symbols-outlined">restart_alt</span>
                  <span>New Session</span>
                </button>
              </div>

              <!-- Messages Stream -->
              <div class="chat-stream" #chatScrollContainer>
                <div *ngFor="let m of chatMessages" class="chat-row" [class.user]="m.role === 'user'" [class.ai]="m.role === 'ai'">
                  <div class="chat-avatar" [class.user-av]="m.role === 'user'" [class.ai-av]="m.role === 'ai'">
                    <span class="material-symbols-outlined">{{ m.role === 'user' ? 'person' : 'smart_toy' }}</span>
                  </div>

                  <div class="chat-bubble" [class.user-bubble]="m.role === 'user'" [class.ai-bubble]="m.role === 'ai'">
                    <div class="markdown-body" [innerHTML]="renderMarkdown(m.displayedContent || m.content)"></div>
                    <span *ngIf="m.isStreaming" class="typewriter-cursor"></span>

                    <!-- Interactive Ticket Draft Card -->
                    <div *ngIf="m.draft && !m.isStreaming" class="draft-card animate-pop">
                      <div class="draft-card-header">
                        <div class="draft-card-title">
                          <span class="material-symbols-outlined text-accent">assignment</span>
                          <span>AI Ticket Draft Generated</span>
                        </div>
                        <span class="badge-status-draft">Pending Confirmation</span>
                      </div>

                      <div class="draft-grid">
                        <div class="draft-field">
                          <span class="df-label">Title</span>
                          <span class="df-val">{{ m.draft.draft_data.title }}</span>
                        </div>
                        <div class="draft-field">
                          <span class="df-label">Category</span>
                          <span class="df-val">{{ m.draft.draft_data.category_name || 'General' }}</span>
                        </div>
                        <div class="draft-field">
                          <span class="df-label">Priority</span>
                          <span class="badge-priority priority-{{ m.draft.draft_data.priority }}">{{ m.draft.draft_data.priority }}</span>
                        </div>
                        <div class="draft-field">
                          <span class="df-label">Affected System</span>
                          <span class="df-val">{{ m.draft.draft_data.meta_info?.affected_system || 'General Device' }}</span>
                        </div>
                      </div>

                      <div class="draft-desc-box">
                        <span class="df-label">Issue Description</span>
                        <p>{{ m.draft.draft_data.description }}</p>
                      </div>

                      <div class="draft-actions" *ngIf="!m.draft.approved && !m.draft.rejected">
                        <button class="btn btn-success" (click)="approveDraft(m.draft)">
                          <span class="material-symbols-outlined">check</span>
                          <span>Approve & Create Ticket</span>
                        </button>
                        <button class="btn btn-danger" (click)="rejectDraft(m.draft)">
                          <span class="material-symbols-outlined">close</span>
                          <span>Reject</span>
                        </button>
                      </div>

                      <div *ngIf="m.draft.approved" class="draft-confirmed text-green">
                        <span class="material-symbols-outlined">verified</span>
                        <span>Ticket created successfully! Tracked in dashboard.</span>
                      </div>

                      <div *ngIf="m.draft.rejected" class="draft-rejected text-danger">
                        <span class="material-symbols-outlined">cancel</span>
                        <span>Draft rejected. Tell me what needs adjustments.</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div *ngIf="isThinking" class="chat-row ai">
                  <div class="chat-avatar ai-av">
                    <span class="material-symbols-outlined">smart_toy</span>
                  </div>
                  <div class="chat-bubble ai-bubble thinking-bubble">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="ml-2 text-sm text-muted">AI is analyzing with gpt-oss:120b...</span>
                  </div>
                </div>
              </div>

              <!-- Chat Input Bar -->
              <div class="chat-input-bar">
                <input type="text" class="chat-text-input" placeholder="Describe your issue or answer follow-up questions..." [(ngModel)]="currentInput" (keydown.enter)="sendMessage()" [disabled]="isThinking">
                <button class="btn btn-primary btn-send" (click)="sendMessage()" [disabled]="isThinking || !currentInput.trim()">
                  <span class="material-symbols-outlined">send</span>
                  <span>Send</span>
                </button>
              </div>
            </div>
          </section>

        </main>
      </div>

      <!-- ================= CREATE TICKET MODAL ================= -->
      <div *ngIf="showCreateModal" class="modal-backdrop animate-fade">
        <div class="modal-dialog card-surface animate-scale">
          <div class="modal-header">
            <h3 class="modal-title">Create Support Ticket</h3>
            <button class="icon-btn" (click)="closeCreateModal()">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <form (ngSubmit)="submitManualTicket()" class="modal-body">
            <div class="form-group">
              <label class="form-label">Title</label>
              <input type="text" class="form-input" placeholder="Brief summary of the issue" [(ngModel)]="newTicket.title" name="title" required>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Category</label>
                <select class="form-select" [(ngModel)]="newTicket.category_id" name="category" (change)="onCategoryChange()" required>
                  <option value="">Select Category</option>
                  <option *ngFor="let c of categories" [value]="c.id">{{ c.name }}</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label">Subcategory</label>
                <select class="form-select" [(ngModel)]="newTicket.subcategory_id" name="subcategory">
                  <option value="">Select Subcategory</option>
                  <option *ngFor="let s of subcategoriesForSelected" [value]="s.id">{{ s.name }}</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Priority</label>
              <select class="form-select" [(ngModel)]="newTicket.priority" name="priority">
                <option value="low">Low (Standard request)</option>
                <option value="medium">Medium (Normal priority)</option>
                <option value="high">High (Affects critical daily work)</option>
                <option value="critical">Critical (Company-wide / Blocker)</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Description</label>
              <textarea class="form-textarea" rows="4" placeholder="Detailed explanation and error messages..." [(ngModel)]="newTicket.description" name="description" required></textarea>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn btn-outlined" (click)="closeCreateModal()">Cancel</button>
              <button type="submit" class="btn btn-primary" [disabled]="!newTicket.title || !newTicket.category_id || !newTicket.description">
                Submit Ticket
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- ================= TICKET DETAIL INSPECTOR MODAL ================= -->
      <div *ngIf="showDetailModal && selectedTicket" class="modal-backdrop animate-fade">
        <div class="modal-dialog modal-lg card-surface animate-scale">
          <div class="modal-header">
            <div class="ticket-header-meta">
              <span class="ticket-lg-num">{{ selectedTicket.ticket_number }}</span>
              <span class="status-badge status-{{ selectedTicket.status }}">{{ formatStatus(selectedTicket.status) }}</span>
              <span class="badge-priority priority-{{ selectedTicket.priority }}">{{ selectedTicket.priority }}</span>
            </div>
            <button class="icon-btn" (click)="closeDetailModal()">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <div class="modal-body modal-scrollable">
            <h2 class="text-xl font-bold mb-2">{{ selectedTicket.title }}</h2>
            <div class="text-muted text-sm mb-4">
              Category: <strong class="text-main">{{ selectedTicket.category?.name || 'General' }}</strong> • 
              Created by: <strong class="text-main">{{ selectedTicket.creator?.full_name || 'User' }}</strong> • 
              Assignee: <strong class="text-main">{{ selectedTicket.assignee?.full_name || 'Unassigned' }}</strong>
            </div>

            <div class="card-subtle p-4 mb-6">
              <h4 class="text-xs uppercase font-bold text-muted mb-2">Description</h4>
              <p class="whitespace-pre-wrap leading-relaxed">{{ selectedTicket.description }}</p>
            </div>

            <!-- Role-guarded lifecycle transitions -->
            <div class="transition-box mb-6">
              <h4 class="text-xs uppercase font-bold text-accent mb-2">Workflow State Transition</h4>
              <div class="flex gap-3 items-center">
                <select class="form-select flex-1" [(ngModel)]="targetStatus">
                  <option value="in_progress">In Progress</option>
                  <option value="assigned">Assigned</option>
                  <option value="escalated">Escalated</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="reopened">Reopened</option>
                </select>
                <button class="btn btn-primary" (click)="applyStatusTransition()">Update Status</button>
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

    /* HEADER */
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

    /* Status Pill */
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

    .user-selector-wrapper {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      background: var(--bg-subtle);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
    }
    .user-dropdown {
      background: transparent;
      border: none;
      color: var(--text-main);
      font-family: inherit;
      font-size: 0.82rem;
      font-weight: 600;
      outline: none;
      cursor: pointer;
    }

    /* APP BODY */
    .app-body {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    /* SIDEBAR */
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
      width: 100%;
      text-align: left;
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
    .nav-count {
      margin-left: auto;
      background: var(--bg-subtle);
      border: 1px solid var(--border);
      padding: 2px 8px;
      border-radius: var(--radius-full);
      font-size: 0.72rem;
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
    .user-name {
      font-size: 0.8rem;
      font-weight: 700;
    }
    .user-role-badge {
      font-size: 0.65rem;
      text-transform: uppercase;
      font-weight: 700;
      color: var(--text-dim);
    }

    /* MAIN CONTENT */
    .app-content {
      flex: 1;
      overflow-y: auto;
      padding: 28px 36px;
    }
    .view-panel {
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

    /* KPI GRID */
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
    .kpi-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-md);
    }
    .kpi-icon-wrap {
      width: 48px;
      height: 48px;
      border-radius: var(--radius-md);
      display: grid;
      place-items: center;
    }
    .icon-total { background: rgba(99, 102, 241, 0.12); color: var(--primary); }
    .icon-open { background: rgba(245, 158, 11, 0.12); color: var(--warning); }
    .icon-progress { background: rgba(6, 182, 212, 0.12); color: var(--accent); }
    .icon-resolved { background: rgba(16, 185, 129, 0.12); color: var(--success); }
    .icon-closed { background: rgba(100, 116, 139, 0.12); color: var(--text-dim); }
    .kpi-info { display: flex; flex-direction: column; }
    .kpi-label { font-size: 0.75rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; }
    .kpi-value { font-family: var(--font-heading); font-size: 1.8rem; font-weight: 800; }

    /* CARD SURFACE & TABLES */
    .card-surface {
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 24px;
      box-shadow: var(--shadow-sm);
    }
    .card-surface-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }
    .card-title {
      font-family: var(--font-heading);
      font-size: 1.1rem;
      font-weight: 700;
    }
    .table-container {
      overflow-x: auto;
    }
    .mat-table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }
    .mat-table th {
      padding: 12px 16px;
      font-size: 0.75rem;
      text-transform: uppercase;
      color: var(--text-dim);
      font-weight: 700;
      border-bottom: 1px solid var(--border);
    }
    .mat-table td {
      padding: 14px 16px;
      font-size: 0.88rem;
      border-bottom: 1px solid var(--border-subtle);
      vertical-align: middle;
    }
    .mat-table tr:hover td {
      background: var(--bg-subtle);
    }
    .ticket-num {
      font-weight: 700;
      color: var(--primary);
      font-family: var(--font-heading);
    }
    .category-chip {
      padding: 4px 10px;
      border-radius: var(--radius-full);
      background: var(--bg-subtle);
      border: 1px solid var(--border);
      font-size: 0.75rem;
      font-weight: 600;
    }

    /* BADGES */
    .status-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: var(--radius-full);
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .status-open { background: rgba(245, 158, 11, 0.12); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .status-assigned { background: rgba(168, 85, 247, 0.12); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
    .status-in_progress { background: rgba(6, 182, 212, 0.12); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.3); }
    .status-escalated { background: rgba(239, 68, 68, 0.12); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .status-resolved { background: rgba(16, 185, 129, 0.12); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .status-closed { background: rgba(100, 116, 139, 0.12); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.3); }

    .badge-priority {
      font-size: 0.75rem;
      font-weight: 800;
      text-transform: uppercase;
    }
    .priority-low { color: #34d399; }
    .priority-medium { color: #fbbf24; }
    .priority-high { color: #f87171; }
    .priority-critical { color: #ff0055; text-shadow: 0 0 10px rgba(255, 0, 85, 0.4); }

    /* BUTTONS */
    .btn {
      padding: 9px 16px;
      border-radius: var(--radius-md);
      font-family: inherit;
      font-weight: 600;
      font-size: 0.85rem;
      border: 1px solid transparent;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: var(--transition);
    }
    .btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-hover)); color: #fff; }
    .btn-outlined { background: transparent; border-color: var(--border); color: var(--text-main); }
    .btn-outlined:hover { background: var(--bg-subtle); }
    .btn-success { background: var(--success); color: #fff; }
    .btn-danger { background: var(--danger); color: #fff; }
    .btn-sm { padding: 5px 10px; font-size: 0.75rem; }
    .icon-btn { background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 6px; border-radius: var(--radius-full); display: grid; place-items: center; }
    .icon-btn:hover { background: var(--bg-subtle); color: var(--text-main); }

    /* FILTERS BAR */
    .filters-bar {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
    }
    .search-input-wrap {
      flex: 1;
      position: relative;
      display: flex;
      align-items: center;
    }
    .search-icon {
      position: absolute;
      left: 14px;
      color: var(--text-dim);
    }
    .search-input {
      width: 100%;
      padding: 12px 16px 12px 42px;
      border-radius: var(--radius-md);
      background: var(--bg-surface);
      border: 1px solid var(--border);
      color: var(--text-main);
      font-family: inherit;
      font-size: 0.88rem;
      outline: none;
    }

    /* CHAT ASSISTANT */
    .chat-container {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 120px);
      padding: 0;
      overflow: hidden;
    }
    .chat-header {
      padding: 16px 24px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: var(--bg-subtle);
    }
    .chat-agent-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .agent-avatar {
      width: 42px;
      height: 42px;
      border-radius: var(--radius-md);
      background: linear-gradient(135deg, var(--primary), var(--accent));
      color: #fff;
      display: grid;
      place-items: center;
    }
    .agent-name {
      font-size: 1rem;
      font-weight: 700;
    }
    .model-badge {
      font-size: 0.65rem;
      background: var(--bg-surface-elevated);
      padding: 2px 6px;
      border-radius: var(--radius-full);
      color: var(--accent);
      border: 1px solid var(--border);
    }
    .agent-sub {
      font-size: 0.72rem;
      color: var(--text-dim);
    }
    .chat-stream {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .chat-row {
      display: flex;
      gap: 12px;
      max-width: 82%;
    }
    .chat-row.user {
      align-self: flex-end;
      flex-direction: row-reverse;
    }
    .chat-avatar {
      width: 36px;
      height: 36px;
      border-radius: var(--radius-md);
      display: grid;
      place-items: center;
      flex-shrink: 0;
    }
    .ai-av { background: linear-gradient(135deg, var(--primary), var(--accent)); color: #fff; }
    .user-av { background: var(--bg-surface-elevated); color: var(--text-main); border: 1px solid var(--border); }
    .chat-bubble {
      padding: 14px 18px;
      border-radius: var(--radius-lg);
      font-size: 0.92rem;
      line-height: 1.6;
    }
    .ai-bubble {
      background: var(--chat-ai-bubble);
      border: 1px solid var(--border);
      border-top-left-radius: 4px;
    }
    .user-bubble {
      background: var(--chat-user-bubble);
      color: #fff;
      border-top-right-radius: 4px;
    }

    /* DRAFT CARD */
    .draft-card {
      margin-top: 14px;
      padding: 18px;
      border-radius: var(--radius-md);
      background: var(--bg-surface);
      border: 1px solid rgba(var(--primary-rgb), 0.4);
      box-shadow: var(--shadow-md);
    }
    .draft-card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }
    .draft-card-title {
      font-weight: 700;
      font-size: 0.95rem;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .badge-status-draft {
      font-size: 0.68rem;
      background: rgba(var(--primary-rgb), 0.12);
      color: var(--primary);
      border: 1px solid rgba(var(--primary-rgb), 0.3);
      padding: 2px 8px;
      border-radius: var(--radius-full);
      font-weight: 700;
    }
    .draft-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 12px;
    }
    .df-label {
      display: block;
      font-size: 0.7rem;
      color: var(--text-dim);
      font-weight: 700;
      text-transform: uppercase;
    }
    .df-val {
      font-size: 0.85rem;
      font-weight: 600;
    }
    .draft-desc-box {
      background: var(--bg-subtle);
      padding: 10px 14px;
      border-radius: var(--radius-sm);
      font-size: 0.85rem;
      margin-bottom: 14px;
    }
    .draft-actions {
      display: flex;
      gap: 10px;
    }

    .chat-input-bar {
      padding: 16px 24px;
      border-top: 1px solid var(--border);
      background: var(--bg-subtle);
      display: flex;
      gap: 12px;
    }
    .chat-text-input {
      flex: 1;
      padding: 12px 18px;
      border-radius: var(--radius-full);
      background: var(--bg-surface);
      border: 1px solid var(--border);
      color: var(--text-main);
      font-family: inherit;
      font-size: 0.9rem;
      outline: none;
    }
    .btn-send {
      border-radius: var(--radius-full);
      padding: 10px 22px;
    }

    /* MODAL */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(8px);
      z-index: 100;
      display: grid;
      place-items: center;
      padding: 20px;
    }
    .modal-dialog {
      width: min(650px, 100%);
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      padding: 24px;
    }
    .modal-lg {
      width: min(850px, 100%);
    }
    .modal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 18px;
    }
    .modal-title {
      font-family: var(--font-heading);
      font-size: 1.25rem;
      font-weight: 700;
    }
    .form-group {
      margin-bottom: 14px;
    }
    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .form-label {
      display: block;
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-dim);
      text-transform: uppercase;
      margin-bottom: 6px;
    }
    .form-input, .form-select, .form-textarea {
      width: 100%;
      padding: 10px 14px;
      border-radius: var(--radius-md);
      background: var(--bg-subtle);
      border: 1px solid var(--border);
      color: var(--text-main);
      font-family: inherit;
      font-size: 0.88rem;
      outline: none;
    }
    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 18px;
    }

    /* TIMELINE */
    .timeline-stream {
      border-left: 2px solid var(--border);
      margin-left: 12px;
      padding-left: 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .timeline-node {
      position: relative;
      font-size: 0.82rem;
    }
    .node-marker {
      position: absolute;
      left: -21px;
      top: 4px;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--primary);
    }
    .node-field { font-weight: 700; color: var(--text-dim); }
    .node-new { font-weight: 700; color: var(--accent); }
    .node-time { font-size: 0.7rem; color: var(--text-dim); margin-top: 2px; }

    /* UTILS & ANIMATIONS */
    .text-amber { color: var(--warning); }
    .text-accent { color: var(--accent); }
    .text-green { color: var(--success); }
    .text-danger { color: var(--danger); }
    .text-muted { color: var(--text-muted); }
    .text-sm { font-size: 0.8rem; }
    .font-semibold { font-weight: 600; }
    .mt-6 { margin-top: 24px; }
    .mb-2 { margin-bottom: 8px; }
    .mb-3 { margin-bottom: 12px; }
    .mb-4 { margin-bottom: 16px; }
    .mb-6 { margin-bottom: 24px; }
    .empty-state { text-align: center; color: var(--text-dim); padding: 24px; }

    .animate-fade { animation: fadeIn 0.25s ease-out; }
    .animate-scale { animation: scaleIn 0.25s ease-out; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes scaleIn { from { opacity: 0; transform: scale(0.96); } to { opacity: 1; transform: scale(1); } }
  `]
})
export class AppComponent implements OnInit, OnDestroy {
  isDarkTheme = true;
  activeTab: 'dashboard' | 'tickets' | 'chat' = 'dashboard';
  sseConnected = false;

  availableUsers: User[] = [
    { email: 'john@company.com', name: 'John Doe', role: 'user' },
    { email: 'jane@company.com', name: 'Jane Smith', role: 'user' },
    { email: 'bob@company.com', name: 'Agent Bob', role: 'agent' },
    { email: 'alice@company.com', name: 'Manager Alice', role: 'manager' },
    { email: 'admin@company.com', name: 'Admin Root', role: 'admin' }
  ];
  currentUser: User = this.availableUsers[0];
  token: string | null = null;

  categories: Category[] = [];
  subcategoriesForSelected: { id: string; name: string }[] = [];

  dashboardStats: DashboardStats | null = null;
  ticketsList: TicketSummary[] = [];
  searchQuery = '';
  statusFilter = '';

  // AI Chat
  chatSessionId: string | null = null;
  chatMessages: ChatMessage[] = [];
  currentInput = '';
  isThinking = false;

  // Modals
  showCreateModal = false;
  newTicket = { title: '', category_id: '', subcategory_id: '', priority: 'medium', description: '' };

  showDetailModal = false;
  selectedTicket: any = null;
  targetStatus = 'in_progress';
  newCommentText = '';

  private eventSource: EventSource | null = null;

  constructor(private cdr: ChangeDetectorRef) {}

  async ngOnInit() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      this.isDarkTheme = savedTheme === 'dark';
    }
    this.applyThemeClass();

    await this.switchUser(this.currentUser.email);
    await this.loadCategories();
    this.initSSE();
  }

  ngOnDestroy() {
    if (this.eventSource) this.eventSource.close();
  }

  toggleTheme() {
    this.isDarkTheme = !this.isDarkTheme;
    localStorage.setItem('theme', this.isDarkTheme ? 'dark' : 'light');
    this.applyThemeClass();
  }

  private applyThemeClass() {
    if (typeof document !== 'undefined') {
      document.body.className = this.isDarkTheme ? 'theme-dark' : 'theme-light';
    }
  }

  setTab(tab: 'dashboard' | 'tickets' | 'chat') {
    this.activeTab = tab;
    if (tab === 'dashboard') this.loadDashboard();
    if (tab === 'tickets') this.loadTickets();
    if (tab === 'chat' && !this.chatSessionId) this.startNewChatSession();
  }

  async switchUser(email: string) {
    const found = this.availableUsers.find(u => u.email === email);
    if (found) this.currentUser = found;

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, password: 'password123' })
      });
      if (!res.ok) throw new Error('Login failed');
      const data = await res.json();
      this.token = data.access_token;
      this.loadDashboard();
      this.loadTickets();
    } catch (e) {
      console.error(e);
    }
  }

  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.token}`
    };
  }

  async loadCategories() {
    try {
      const res = await fetch('/api/categories');
      if (res.ok) this.categories = await res.json();
    } catch (e) { console.error(e); }
  }

  onCategoryChange() {
    const cat = this.categories.find(c => c.id === this.newTicket.category_id);
    this.subcategoriesForSelected = cat ? cat.subcategories : [];
    this.newTicket.subcategory_id = '';
  }

  async loadDashboard() {
    try {
      const res = await fetch('/api/dashboard/stats', { headers: this.getHeaders() });
      if (res.ok) {
        this.dashboardStats = await res.json();
        this.cdr.detectChanges();
      }
    } catch (e) { console.error(e); }
  }

  async loadTickets() {
    try {
      let url = '/api/tickets?page=1&per_page=50';
      if (this.searchQuery) url += `&search=${encodeURIComponent(this.searchQuery)}`;
      if (this.statusFilter) url += `&status=${encodeURIComponent(this.statusFilter)}`;
      const res = await fetch(url, { headers: this.getHeaders() });
      if (res.ok) {
        const data = await res.json();
        this.ticketsList = data.items || [];
        this.cdr.detectChanges();
      }
    } catch (e) { console.error(e); }
  }

  // ================= AI CHAT & TYPEWRITER =================
  async startNewChatSession() {
    try {
      const res = await fetch('/api/chat/sessions', {
        method: 'POST',
        headers: this.getHeaders()
      });
      if (res.ok) {
        const session = await res.json();
        this.chatSessionId = session.id;
        this.chatMessages = [{
          role: 'ai',
          content: "👋 **Hello! I'm your AI Support Assistant powered by gpt-oss:120b.**\n\nTell me about any hardware issue, VPN problem, software bug, or account access trouble you are facing, and I will help triage and prepare a ticket for you."
        }];
        this.cdr.detectChanges();
      }
    } catch (e) { console.error(e); }
  }

  async sendMessage() {
    const text = this.currentInput.trim();
    if (!text || !this.chatSessionId || this.isThinking) return;

    this.currentInput = '';
    this.chatMessages.push({ role: 'user', content: text });
    this.isThinking = true;
    this.cdr.detectChanges();

    try {
      const res = await fetch(`/api/chat/sessions/${this.chatSessionId}/messages`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ content: text })
      });
      if (!res.ok) throw new Error('Chat API error');
      const data = await res.json();

      const newMsg: ChatMessage = {
        role: 'ai',
        content: data.response,
        displayedContent: '',
        isStreaming: true,
        draft: data.draft || null
      };
      this.chatMessages.push(newMsg);
      this.isThinking = false;
      this.cdr.detectChanges();

      // Run streaming typewriter effect
      this.runTypewriterEffect(newMsg);
    } catch (e: any) {
      this.isThinking = false;
      this.chatMessages.push({
        role: 'ai',
        content: "⚠️ I encountered an error communicating with the agent: " + e.message
      });
      this.cdr.detectChanges();
    }
  }

  private runTypewriterEffect(msg: ChatMessage) {
    const fullText = msg.content;
    let index = 0;
    const interval = setInterval(() => {
      index += 3;
      if (index >= fullText.length) {
        msg.displayedContent = fullText;
        msg.isStreaming = false;
        clearInterval(interval);
      } else {
        msg.displayedContent = fullText.slice(0, index);
      }
      this.cdr.detectChanges();
    }, 18);
  }

  async approveDraft(draft: any) {
    try {
      const res = await fetch(`/api/chat/sessions/${this.chatSessionId}/drafts/${draft.id}/approve`, {
        method: 'POST',
        headers: this.getHeaders()
      });
      if (res.ok) {
        draft.approved = true;
        this.loadDashboard();
        this.loadTickets();
        this.cdr.detectChanges();
      }
    } catch (e) { console.error(e); }
  }

  async rejectDraft(draft: any) {
    try {
      await fetch(`/api/chat/sessions/${this.chatSessionId}/drafts/${draft.id}/reject`, {
        method: 'POST',
        headers: this.getHeaders()
      });
      draft.rejected = true;
      this.cdr.detectChanges();
    } catch (e) { console.error(e); }
  }

  // ================= MODALS & DETAILS =================
  openCreateModal() {
    this.showCreateModal = true;
  }
  closeCreateModal() {
    this.showCreateModal = false;
    this.newTicket = { title: '', category_id: '', subcategory_id: '', priority: 'medium', description: '' };
  }

  async submitManualTicket() {
    try {
      const res = await fetch('/api/tickets', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(this.newTicket)
      });
      if (!res.ok) {
        const err = await res.json();
        alert('Error creating ticket: ' + (err.error?.message || 'Failed'));
        return;
      }
      this.closeCreateModal();
      this.loadDashboard();
      this.loadTickets();
    } catch (e: any) { alert(e.message); }
  }

  async viewTicketDetails(id: string) {
    try {
      const res = await fetch(`/api/tickets/${id}`, { headers: this.getHeaders() });
      if (res.ok) {
        this.selectedTicket = await res.json();
        this.targetStatus = this.selectedTicket.status;
        this.showDetailModal = true;
        this.cdr.detectChanges();
      }
    } catch (e) { console.error(e); }
  }
  closeDetailModal() {
    this.showDetailModal = false;
    this.selectedTicket = null;
  }

  async applyStatusTransition() {
    if (!this.selectedTicket) return;
    try {
      const res = await fetch(`/api/tickets/${this.selectedTicket.id}`, {
        method: 'PATCH',
        headers: this.getHeaders(),
        body: JSON.stringify({ status: this.targetStatus, comment: `Transitioned status to ${this.targetStatus}` })
      });
      if (!res.ok) {
        const err = await res.json();
        alert(err.error?.message || 'Invalid state transition for your role.');
        return;
      }
      this.viewTicketDetails(this.selectedTicket.id);
      this.loadDashboard();
      this.loadTickets();
    } catch (e: any) { alert(e.message); }
  }

  async addComment() {
    if (!this.selectedTicket || !this.newCommentText.trim()) return;
    try {
      const res = await fetch(`/api/tickets/${this.selectedTicket.id}/comments`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ content: this.newCommentText.trim() })
      });
      if (res.ok) {
        this.newCommentText = '';
        this.viewTicketDetails(this.selectedTicket.id);
      }
    } catch (e) { console.error(e); }
  }

  // ================= SSE STREAM =================
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
        this.loadDashboard();
        this.loadTickets();
      });
      this.eventSource.addEventListener('ticket_updated', () => {
        this.loadDashboard();
        this.loadTickets();
        if (this.showDetailModal && this.selectedTicket) {
          this.viewTicketDetails(this.selectedTicket.id);
        }
      });
    } catch (e) { console.error(e); }
  }

  formatStatus(status: string): string {
    return status ? status.replace('_', ' ') : '';
  }

  renderMarkdown(text: string): string {
    if (!text) return '';
    let html = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>');
    return html;
  }
}

