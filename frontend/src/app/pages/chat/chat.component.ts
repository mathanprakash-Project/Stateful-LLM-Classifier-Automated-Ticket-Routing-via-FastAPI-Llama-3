import { Component, OnInit, inject, ChangeDetectorRef, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
  displayedContent?: string;
  isStreaming?: boolean;
  draft?: any;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="view-panel animate-fade h-full flex flex-col">
      <div class="chat-container card-surface">
        <!-- Chat Top Header -->
        <div class="chat-header">
          <div class="chat-agent-info">
            <div class="agent-avatar">
              <span class="material-symbols-outlined">psychology</span>
            </div>
            <div>
              <div class="flex items-center gap-3 flex-wrap">
                <h3 class="agent-name">IT Triage AI Agent</h3>
                <!-- Model Switcher Dropdown -->
                <div class="model-selector-pill">
                  <span class="material-symbols-outlined text-sm" [ngClass]="selectedModel === 'llama3.2:3b' ? 'text-green' : 'text-accent'">{{ selectedModel === 'llama3.2:3b' ? 'bolt' : 'cloud' }}</span>
                  <select [(ngModel)]="selectedModel" (change)="onModelChange()" class="model-dropdown-select" title="Switch Active AI Model">
                    <option value="llama3.2:3b">⚡ llama3.2:3b (Local Edge)</option>
                    <option value="gpt-oss:120b-cloud">☁️ gpt-oss:120b-cloud (Cloud Enterprise)</option>
                  </select>
                </div>
              </div>
              <span class="agent-sub">{{ auth.isUser() ? 'LangGraph Multi-Turn Diagnostic & Ticket Creation' : 'Operational & Technical Activity Advisor (Staff Mode)' }}</span>
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

              <!-- Interactive Ticket Draft Card (Editable & Validated) -->
              <div *ngIf="m.draft && !m.isStreaming" class="draft-card animate-pop">
                <div class="draft-card-header">
                  <div class="draft-card-title">
                    <span class="material-symbols-outlined text-accent">assignment</span>
                    <span>AI Ticket Draft (Editable Review)</span>
                  </div>
                  <span class="badge-status-draft">Editable Draft</span>
                </div>

                <div class="draft-grid">
                  <div class="draft-field col-span-2">
                    <label class="df-label">Title</label>
                    <input type="text" class="draft-text-field" [(ngModel)]="m.draft.draft_data.title" placeholder="Ticket title...">
                  </div>
                  <div class="draft-field">
                    <label class="df-label">Category</label>
                    <select [(ngModel)]="m.draft.draft_data.category_name" class="draft-select-field" (change)="onDraftCategoryChange(m.draft)">
                      <option value="Application UI">Application UI (Online)</option>
                      <option value="Application Version Maintenance">Application Version Maintenance (Offline)</option>
                      <option value="Client Data Transfer">Client Data Transfer (Hybrid)</option>
                      <option value="File Management">File Management (Online)</option>
                    </select>
                  </div>
                  <div class="draft-field">
                    <label class="df-label">Priority</label>
                    <select [(ngModel)]="m.draft.draft_data.priority" class="draft-select-field">
                      <option value="low">Low (Standard)</option>
                      <option value="medium">Medium (Online Default)</option>
                      <option value="high">High (Hybrid Default / Urgent)</option>
                      <option value="critical">Critical (Offline Default / Emergency)</option>
                    </select>
                  </div>
                </div>

                <div class="draft-desc-box mt-2">
                  <label class="df-label">Issue Description</label>
                  <textarea class="draft-textarea-field" rows="3" [(ngModel)]="m.draft.draft_data.description" placeholder="Describe the operational scope or error details..."></textarea>
                </div>

                <!-- Operational Maintenance Activity Details -->
                <div class="draft-op-box p-3 mb-3">
                  <div class="flex flex-wrap gap-2 mb-2">
                    <span class="op-mode-pill mode-{{ (m.draft.draft_data.execution_mode || 'Online') | lowercase }}">
                      <span class="material-symbols-outlined">bolt</span>
                      {{ m.draft.draft_data.execution_mode || 'Online' }}
                    </span>
                    <span class="op-downtime-pill" [class.downtime-warn]="m.draft.draft_data.downtime_required" [class.downtime-lockout]="m.draft.draft_data.execution_mode === 'Hybrid'">
                      <span class="material-symbols-outlined">{{ m.draft.draft_data.downtime_required ? 'power_off' : 'lock_clock' }}</span>
                      {{ m.draft.draft_data.downtime_description || (m.draft.draft_data.downtime_required ? 'Planned Downtime' : (m.draft.draft_data.execution_mode === 'Hybrid' ? 'User Lockout' : 'No Downtime')) }}
                    </span>
                    <span *ngIf="m.draft.draft_data.requires_admin_approval" class="draft-restriction-badge warn">
                      <span class="material-symbols-outlined">shield_lock</span> Admin Approval Required
                    </span>
                    <span *ngIf="m.draft.draft_data.requires_manager_review" class="draft-restriction-badge info">
                      <span class="material-symbols-outlined">alt_route</span> Manager Review Required
                    </span>
                  </div>

                  <!-- Prerequisites checklist if any -->
                  <div *ngIf="m.draft.draft_data.prerequisites?.length" class="text-xs mb-2">
                    <strong class="text-dim uppercase">Prerequisites Checklist:</strong>
                    <ul class="prereq-mini-list mt-1">
                      <li *ngFor="let p of m.draft.draft_data.prerequisites">✓ {{ p }}</li>
                    </ul>
                  </div>

                  <!-- Operational Warning -->
                  <div *ngIf="m.draft.draft_data.risk_warning" class="draft-risk-warning">
                    <span class="material-symbols-outlined text-warning">warning</span>
                    <span>{{ m.draft.draft_data.risk_warning }}</span>
                  </div>

                  <!-- Maintenance Window / Downtime Input Field -->
                  <div class="mt-2 pt-2 border-top" *ngIf="m.draft.draft_data.downtime_required || m.draft.draft_data.execution_mode === 'Hybrid'">
                    <label class="text-xs text-dim block mb-1 font-semibold">
                      <span class="material-symbols-outlined text-xs align-middle">schedule</span> Scheduled Maintenance Window / Downtime (Optional/Required):
                    </label>
                    <input type="text" class="chat-downtime-input" placeholder="e.g. Sunday 02:00 AM - 04:00 AM UTC" [(ngModel)]="m.draft.draft_data.maintenance_window">
                  </div>

                  <!-- Mandatory confirmation checkbox with visual validation error -->
                  <div class="mt-2 pt-2 border-top" [class.checkbox-error-box]="m.draft.validationError">
                    <label class="checkbox-label text-xs">
                      <input type="checkbox" [(ngModel)]="m.draft.prerequisites_confirmed" (change)="m.draft.validationError = ''">
                      <span>I verify that prerequisites, category, and downtime requirements have been reviewed.</span>
                    </label>
                    <!-- Error Banner if user didn't check checkbox -->
                    <div *ngIf="m.draft.validationError" class="draft-validation-alert animate-fade">
                      <span class="material-symbols-outlined text-xs">error</span>
                      <span>{{ m.draft.validationError }}</span>
                    </div>
                  </div>
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
              <span class="ml-2 text-sm text-muted">AI is analyzing with {{ selectedModel }}...</span>
            </div>
          </div>
        </div>

        <!-- Chat Input Bar -->
        <div class="chat-input-bar">
          <input type="text" class="chat-text-input" placeholder="Describe your technical issue or answer follow-up questions..." [(ngModel)]="currentInput" (keydown.enter)="sendMessage()" [disabled]="isThinking">
          <button class="btn btn-primary btn-send" (click)="sendMessage()" [disabled]="isThinking || !currentInput.trim()">
            <span class="material-symbols-outlined">send</span>
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .view-panel { padding: 0; max-width: 1000px; margin: 0 auto; }
    .h-full { height: 100%; }
    .flex { display: flex; }
    .flex-col { flex-direction: column; }
    
    .chat-container { display: flex; flex-direction: column; height: calc(100vh - 120px); padding: 0; overflow: hidden; background: var(--corona-surface); border: 1px solid var(--corona-border); border-radius: var(--radius-sm); box-shadow: var(--shadow-card); }
    .chat-header { padding: 16px 24px; border-bottom: 1px solid var(--corona-border); display: flex; align-items: center; justify-content: space-between; background: #000000; }
    .chat-agent-info { display: flex; align-items: center; gap: 12px; }
    .agent-avatar { width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg, var(--corona-purple), var(--corona-blue)); color: #fff; display: grid; place-items: center; }
    .agent-name { font-size: 0.95rem; font-weight: 700; color: #ffffff; }
    .model-badge { font-size: 0.65rem; background: rgba(0, 144, 231, 0.15); padding: 2px 6px; border-radius: 4px; color: var(--corona-blue); border: 1px solid rgba(0, 144, 231, 0.3); }
    .agent-sub { font-size: 0.72rem; color: var(--text-muted); }
    
    .chat-stream { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 18px; }
    .chat-row { display: flex; gap: 12px; max-width: 84%; }
    .chat-row.user { align-self: flex-end; flex-direction: row-reverse; }
    
    .chat-avatar { width: 36px; height: 36px; border-radius: 50%; display: grid; place-items: center; flex-shrink: 0; }
    .ai-av { background: linear-gradient(135deg, var(--corona-purple), var(--corona-blue)); color: #fff; }
    .user-av { background: #000000; color: var(--corona-green); border: 1px solid var(--corona-border); }
    
    .chat-bubble { padding: 14px 18px; border-radius: var(--radius-sm); font-size: 0.9rem; line-height: 1.6; }
    .ai-bubble { background: #000000; border: 1px solid var(--corona-border); border-top-left-radius: 2px; color: #ffffff; }
    .user-bubble { background: var(--corona-surface-elevated); color: #ffffff; border: 1px solid var(--corona-border); border-top-right-radius: 2px; }
    
    .draft-card { margin-top: 14px; padding: 18px; border-radius: var(--radius-sm); background: var(--corona-surface); border: 1px solid var(--corona-purple); box-shadow: var(--shadow-glow-purple); color: #ffffff; }
    .draft-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
    .draft-card-title { font-weight: 700; font-size: 0.92rem; display: flex; align-items: center; gap: 6px; color: var(--corona-purple); }
    .badge-status-draft { font-size: 0.68rem; background: rgba(143, 95, 232, 0.15); color: var(--corona-purple); border: 1px solid rgba(143, 95, 232, 0.3); padding: 2px 8px; border-radius: 4px; font-weight: 700; }
    
    .draft-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
    .col-span-2 { grid-column: span 2; }
    .df-label { display: block; font-size: 0.7rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }
    
    .draft-text-field, .draft-select-field, .draft-textarea-field {
      width: 100%;
      background: #000000;
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 6px 10px;
      font-size: 0.84rem;
      color: #ffffff;
      font-family: inherit;
      box-sizing: border-box;
      outline: none;
    }
    .draft-text-field:focus, .draft-select-field:focus, .draft-textarea-field:focus {
      border-color: var(--corona-purple);
    }
    
    .draft-desc-box { background: #000000; padding: 10px 14px; border-radius: var(--radius-sm); font-size: 0.85rem; margin-bottom: 14px; border: 1px solid var(--corona-border); }
    .draft-actions { display: flex; gap: 10px; }
    .draft-confirmed { display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 0.85rem; color: var(--corona-green); }
    .draft-rejected { display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 0.85rem; color: var(--corona-red); }
    
    .draft-badges { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }
    .draft-activity-badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 4px; background: rgba(143, 95, 232, 0.15); border: 1px solid rgba(143, 95, 232, 0.3); color: var(--corona-purple); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; }
    .draft-activity-badge .material-symbols-outlined { font-size: 14px; }
    .draft-restriction-badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; }
    .draft-restriction-badge.warn { background: rgba(255, 171, 0, 0.15); border: 1px solid rgba(255, 171, 0, 0.3); color: var(--corona-orange); }
    .draft-restriction-badge.info { background: rgba(0, 144, 231, 0.15); border: 1px solid rgba(0, 144, 231, 0.3); color: var(--corona-blue); }
    .draft-restriction-badge .material-symbols-outlined { font-size: 14px; }
    
    .chat-input-bar { padding: 16px 24px; border-top: 1px solid var(--corona-border); background: #000000; display: flex; gap: 12px; }
    .chat-text-input { flex: 1; padding: 10px 18px; border-radius: var(--radius-sm); background: var(--corona-surface); border: 1px solid var(--corona-border); color: #ffffff; font-family: inherit; font-size: 0.88rem; outline: none; }
    .chat-text-input:focus { border-color: var(--corona-purple); }
    
    .btn { padding: 8px 16px; border-radius: var(--radius-sm); font-family: inherit; font-weight: 600; font-size: 0.85rem; border: 1px solid transparent; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: var(--transition); }
    .btn-primary { background: var(--corona-green); color: #000; font-weight: 700; }
    .btn-outlined { background: transparent; border-color: var(--corona-border); color: #ffffff; }
    .btn-success { background: var(--corona-green); color: #000; font-weight: 700; }
    .btn-danger { background: var(--corona-red); color: #fff; }
    .btn-sm { padding: 5px 10px; font-size: 0.75rem; }
    .btn-send { border-radius: var(--radius-sm); padding: 8px 20px; }
    
    .badge-priority { font-size: 0.72rem; font-weight: 800; text-transform: uppercase; }
    .priority-low { color: var(--corona-green); }
    .priority-medium { color: var(--corona-orange); }
    .priority-high { color: var(--corona-red); }
    .priority-critical { color: #ff0055; text-shadow: 0 0 8px rgba(255, 0, 85, 0.4); }
    
    .text-accent { color: var(--corona-blue); }
    .text-green { color: var(--corona-green); }
    .text-danger { color: var(--corona-red); }
    .text-muted { color: var(--text-muted); }
    .text-sm { font-size: 0.8rem; }
    .ml-2 { margin-left: 8px; }
    
    .animate-fade { animation: fadeIn 0.2s ease-out; }
    .animate-pop { animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes popIn { 0% { opacity: 0; transform: scale(0.9); } 100% { opacity: 1; transform: scale(1); } }
    
    .typing-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: var(--corona-green); margin: 0 2px; animation: bounce 1.4s infinite ease-in-out both; }
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .draft-op-box { background: #000000; border: 1px solid var(--corona-border); border-radius: var(--radius-sm); font-size: 0.82rem; }
    .p-3 { padding: 12px; }
    .mb-2 { margin-bottom: 8px; }
    .mb-3 { margin-bottom: 12px; }
    .mt-1 { margin-top: 4px; }
    .mt-2 { margin-top: 8px; }
    .pt-2 { padding-top: 8px; }
    .border-top { border-top: 1px solid var(--corona-border); }
    .text-dim { color: var(--text-dim); }
    .uppercase { text-transform: uppercase; }
    .flex-wrap { flex-wrap: wrap; }

    .op-mode-pill { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; background: rgba(143, 95, 232, 0.15); color: var(--corona-purple); border: 1px solid rgba(143, 95, 232, 0.3); }
    .op-mode-pill .material-symbols-outlined { font-size: 14px; }
    .op-downtime-pill { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; background: rgba(0, 210, 91, 0.15); color: var(--corona-green); border: 1px solid rgba(0, 210, 91, 0.3); }
    .op-downtime-pill.downtime-warn { background: rgba(252, 66, 74, 0.15); color: var(--corona-red); border: 1px solid rgba(252, 66, 74, 0.3); }
    .op-downtime-pill.downtime-lockout { background: rgba(255, 171, 0, 0.15); color: var(--corona-orange); border: 1px solid rgba(255, 171, 0, 0.3); }
    .op-downtime-pill .material-symbols-outlined { font-size: 14px; }

    .prereq-mini-list { list-style: none; padding-left: 0; margin: 4px 0 0 0; display: flex; flex-direction: column; gap: 4px; color: #ffffff; }
    .draft-risk-warning { display: flex; align-items: center; gap: 6px; background: rgba(255, 171, 0, 0.08); border: 1px solid rgba(255, 171, 0, 0.3); padding: 6px 10px; border-radius: var(--radius-sm); font-size: 0.75rem; color: #ffffff; margin-top: 6px; }
    .draft-risk-warning .material-symbols-outlined { font-size: 16px; flex-shrink: 0; color: var(--corona-orange); }

    .checkbox-label { display: flex; align-items: flex-start; gap: 8px; font-size: 0.78rem; cursor: pointer; color: #ffffff; line-height: 1.3; }
    .checkbox-label input { margin-top: 2px; accent-color: var(--corona-green); }

    .checkbox-error-box { background: rgba(252, 66, 74, 0.08); border: 1px solid var(--corona-red); border-radius: 4px; padding: 8px; }
    .draft-validation-alert { display: flex; align-items: center; gap: 6px; color: var(--corona-red); font-size: 0.78rem; font-weight: 700; margin-top: 6px; }

    .chat-downtime-input { width: 100%; background: #000000; border: 1px solid var(--corona-border); border-radius: var(--radius-sm); padding: 6px 10px; font-size: 0.8rem; color: #ffffff; margin-top: 4px; box-sizing: border-box; }
    .chat-downtime-input:focus { border-color: var(--corona-purple); outline: none; }

    .model-selector-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #000000;
      border: 1px solid var(--corona-border);
      border-radius: 20px;
      padding: 3px 8px;
      transition: var(--transition);
    }
    .model-selector-pill:hover {
      border-color: var(--corona-purple);
    }
    .model-dropdown-select {
      background: transparent;
      border: none;
      color: #ffffff;
      font-size: 0.75rem;
      font-weight: 700;
      outline: none;
      cursor: pointer;
      font-family: inherit;
    }
    .model-dropdown-select option {
      background: #12151e;
      color: #ffffff;
      font-weight: 600;
    }

    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
  `]
})
export class ChatComponent implements OnInit {
  api = inject(ApiService);
  auth = inject(AuthService);
  cdr = inject(ChangeDetectorRef);

  @ViewChild('chatScrollContainer') chatScrollContainer!: ElementRef;

  chatSessionId: string | null = null;
  chatMessages: ChatMessage[] = [];
  currentInput = '';
  isThinking = false;
  selectedModel: string = 'llama3.2:3b';

  ngOnInit() {
    const saved = localStorage.getItem('preferred_ai_model');
    if (saved) this.selectedModel = saved;
    this.startNewChatSession();
  }

  onModelChange() {
    localStorage.setItem('preferred_ai_model', this.selectedModel);
    this.cdr.detectChanges();
  }

  async startNewChatSession() {
    try {
      const res = await this.api.post('/api/chat/sessions', {});
      if (res.ok) {
        const session = await res.json();
        this.chatSessionId = session.id;

        const isUser = this.auth.isUser();
        const greetingContent = isUser
          ? "👋 **Hello! I'm your Enterprise Application Support AI Specialist.**\n\nTell me about any issue, error, or operational maintenance request you need, and I will guide you through prerequisites, downtime verification, and prepare a ticket for you."
          : "👋 **Hello! I'm your Operational & Technical Activity Advisor.**\n\nAsk me any technical questions or doubts about performing operational activities (e.g. Application Versioning, Client Data Transfer, File Management, UI adaptations, database locks, rollback procedures, prerequisites, checklist checks, etc.).";

        this.chatMessages = [{
          role: 'ai',
          content: greetingContent
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
    this.scrollToBottom();

    try {
      const res = await this.api.post(`/api/chat/sessions/${this.chatSessionId}/messages`, {
        content: text,
        preferred_model: this.selectedModel,
      });
      if (!res.ok) throw new Error('Chat API error');
      const data = await res.json();

      if (data.draft && data.draft.draft_data) {
        const cat = data.draft.draft_data.category_name;
        const mode = data.draft.draft_data.execution_mode;
        let defaultPrio = 'medium';
        if (cat === 'Application Version Maintenance' || mode === 'Offline') {
          defaultPrio = 'critical';
        } else if (cat === 'Client Data Transfer' || mode === 'Hybrid') {
          defaultPrio = 'high';
        } else {
          defaultPrio = 'medium';
        }

        let prio = (data.draft.draft_data.priority || defaultPrio).toString().toLowerCase();
        if (!['low', 'medium', 'high', 'critical'].includes(prio)) {
          prio = defaultPrio;
        }
        data.draft.draft_data.priority = prio;
      }

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
      this.scrollToBottom();

      this.runTypewriterEffect(newMsg);
    } catch (e: any) {
      this.isThinking = false;
      this.chatMessages.push({ role: 'ai', content: "⚠️ I encountered an error communicating with the agent: " + e.message });
      this.cdr.detectChanges();
      this.scrollToBottom();
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
      this.scrollToBottom();
    }, 18);
  }

  onDraftCategoryChange(draft: any) {
    if (!draft || !draft.draft_data) return;
    const cat = draft.draft_data.category_name;

    switch (cat) {
      case 'Application UI':
        draft.draft_data.title = 'Application UI Maintenance';
        draft.draft_data.activity_code = 'APPLICATION_UI';
        draft.draft_data.execution_mode = 'Online';
        draft.draft_data.downtime_required = false;
        draft.draft_data.downtime_description = 'No Downtime';
        draft.draft_data.priority = 'medium'; // Online mode default: medium
        draft.draft_data.requires_admin_approval = false;
        draft.draft_data.risk_warning = '';
        break;

      case 'Application Version Maintenance':
        draft.draft_data.title = 'Application Version Maintenance';
        draft.draft_data.activity_code = 'APPLICATION_VERSION';
        draft.draft_data.execution_mode = 'Offline';
        draft.draft_data.downtime_required = true;
        draft.draft_data.downtime_description = 'Yes (Planned Downtime)';
        draft.draft_data.priority = 'critical'; // Offline mode default: critical
        draft.draft_data.requires_admin_approval = true;
        draft.draft_data.risk_warning = 'Requires offline maintenance window and Administrator authorization.';
        break;

      case 'Client Data Transfer':
        draft.draft_data.title = 'Client Data Transfer';
        draft.draft_data.activity_code = 'CLIENT_DATA_TRANSFER';
        draft.draft_data.execution_mode = 'Hybrid';
        draft.draft_data.downtime_required = false;
        draft.draft_data.downtime_description = 'No Full Downtime (User Lockout Required)';
        draft.draft_data.priority = 'high'; // Hybrid mode default: high
        draft.draft_data.requires_admin_approval = true;
        draft.draft_data.risk_warning = 'Active users must be locked out during data synchronization.';
        break;

      case 'File Management':
        draft.draft_data.title = 'File Management Operations';
        draft.draft_data.activity_code = 'FILE_MANAGEMENT';
        draft.draft_data.execution_mode = 'Online';
        draft.draft_data.downtime_required = false;
        draft.draft_data.downtime_description = 'No Downtime';
        draft.draft_data.priority = 'medium'; // Online mode default: medium
        draft.draft_data.requires_admin_approval = false;
        draft.draft_data.risk_warning = '';
        break;
    }
    this.cdr.detectChanges();
  }

  async approveDraft(draft: any) {
    if (!draft || !draft.draft_data) return;

    const title = (draft.draft_data.title || '').trim();
    const category = (draft.draft_data.category_name || '').trim();
    const priority = (draft.draft_data.priority || '').trim();
    const description = (draft.draft_data.description || '').trim();

    // Mandatory Field Validations
    if (!title) {
      draft.validationError = 'Ticket Title is mandatory. Please provide an activity title.';
      alert('⚠️ Ticket Title is mandatory. Please provide an activity title.');
      this.cdr.detectChanges();
      return;
    }

    if (!category) {
      draft.validationError = 'Category is mandatory. Please select an application category.';
      alert('⚠️ Category is mandatory. Please select an application category.');
      this.cdr.detectChanges();
      return;
    }

    if (!priority) {
      draft.validationError = 'Priority is mandatory. Please select a priority level.';
      alert('⚠️ Priority is mandatory. Please select a priority level.');
      this.cdr.detectChanges();
      return;
    }

    if (!description) {
      draft.validationError = 'Issue Description is mandatory. Please provide a description of the issue.';
      alert('⚠️ Issue Description is mandatory. Please provide a description of the issue.');
      this.cdr.detectChanges();
      return;
    }

    // Checkbox Validation
    if (!draft.prerequisites_confirmed) {
      draft.validationError = 'Please check and click the confirmation checkbox before creating the ticket.';
      alert('⚠️ Please check and click the confirmation checkbox before creating the ticket.');
      this.cdr.detectChanges();
      return;
    }

    draft.validationError = '';
    try {
      const res = await this.api.post(`/api/chat/sessions/${this.chatSessionId}/drafts/${draft.id}/approve`, {
        custom_data: draft.draft_data
      });
      if (res.ok) {
        draft.approved = true;
        this.cdr.detectChanges();
      } else {
        const err = await res.json();
        alert(err.error?.message || 'Failed to approve draft');
      }
    } catch (e: any) {
      alert(e.message || 'Failed to approve draft');
    }
  }

  async rejectDraft(draft: any) {
    try {
      await this.api.post(`/api/chat/sessions/${this.chatSessionId}/drafts/${draft.id}/reject`, {});
      draft.rejected = true;
      this.cdr.detectChanges();
    } catch (e) { console.error(e); }
  }

  scrollToBottom() {
    setTimeout(() => {
      if (this.chatScrollContainer) {
        this.chatScrollContainer.nativeElement.scrollTop = this.chatScrollContainer.nativeElement.scrollHeight;
      }
    }, 50);
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
