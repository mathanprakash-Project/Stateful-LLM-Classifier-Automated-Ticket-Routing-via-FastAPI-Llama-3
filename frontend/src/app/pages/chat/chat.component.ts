import { Component, OnInit, inject, ChangeDetectorRef, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

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

                <!-- Operational Maintenance Activity Details -->
                <div class="draft-op-box p-3 mb-3" *ngIf="m.draft.draft_data?.activity_code">
                  <div class="flex flex-wrap gap-2 mb-2">
                    <span class="op-mode-pill mode-{{ (m.draft.draft_data.execution_mode || 'Online') | lowercase }}">
                      <span class="material-symbols-outlined">bolt</span>
                      {{ m.draft.draft_data.execution_mode || 'Online' }}
                    </span>
                    <span class="op-downtime-pill" [class.downtime-warn]="m.draft.draft_data.downtime_required" [class.downtime-lockout]="m.draft.draft_data.execution_mode === 'Hybrid'">
                      <span class="material-symbols-outlined">{{ m.draft.draft_data.downtime_required ? 'power_off' : 'lock_clock' }}</span>
                      {{ m.draft.draft_data.downtime_description || (m.draft.draft_data.downtime_required ? 'Planned Downtime' : 'No Downtime') }}
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
                      <span class="material-symbols-outlined text-xs align-middle">schedule</span> Approved Maintenance Window / Downtime Schedule:
                    </label>
                    <input type="text" class="chat-downtime-input" placeholder="e.g. Sunday 02:00 AM - 04:00 AM UTC" [(ngModel)]="m.draft.draft_data.maintenance_window">
                  </div>

                  <!-- Mandatory confirmation checkbox -->
                  <div class="mt-2 pt-2 border-top">
                    <label class="checkbox-label text-xs">
                      <input type="checkbox" [(ngModel)]="m.draft.prerequisites_confirmed">
                      <span>I verify that prerequisites and downtime requirements have been reviewed and accepted.</span>
                    </label>
                  </div>
                </div>

                <div class="draft-actions" *ngIf="!m.draft.approved && !m.draft.rejected">
                  <button class="btn btn-success" (click)="approveDraft(m.draft)" [disabled]="(m.draft.draft_data?.prerequisites?.length && !m.draft.prerequisites_confirmed) || (m.draft.draft_data?.downtime_required && !m.draft.draft_data?.maintenance_window)">
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
    .view-panel { padding: 28px 36px; max-width: 1200px; margin: 0 auto; }
    .h-full { height: 100%; }
    .flex { display: flex; }
    .flex-col { flex-direction: column; }
    
    .chat-container { display: flex; flex-direction: column; height: calc(100vh - 120px); padding: 0; overflow: hidden; background: var(--bg-surface); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); }
    .chat-header { padding: 16px 24px; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; background: var(--bg-subtle); }
    .chat-agent-info { display: flex; align-items: center; gap: 12px; }
    .agent-avatar { width: 42px; height: 42px; border-radius: var(--radius-md); background: linear-gradient(135deg, var(--primary), var(--accent)); color: #fff; display: grid; place-items: center; }
    .agent-name { font-size: 1rem; font-weight: 700; }
    .model-badge { font-size: 0.65rem; background: var(--bg-surface-elevated); padding: 2px 6px; border-radius: var(--radius-full); color: var(--accent); border: 1px solid var(--border); }
    .agent-sub { font-size: 0.72rem; color: var(--text-dim); }
    
    .chat-stream { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 18px; }
    .chat-row { display: flex; gap: 12px; max-width: 82%; }
    .chat-row.user { align-self: flex-end; flex-direction: row-reverse; }
    
    .chat-avatar { width: 36px; height: 36px; border-radius: var(--radius-md); display: grid; place-items: center; flex-shrink: 0; }
    .ai-av { background: linear-gradient(135deg, var(--primary), var(--accent)); color: #fff; }
    .user-av { background: var(--bg-surface-elevated); color: var(--text-main); border: 1px solid var(--border); }
    
    .chat-bubble { padding: 14px 18px; border-radius: var(--radius-lg); font-size: 0.92rem; line-height: 1.6; }
    .ai-bubble { background: var(--chat-ai-bubble, var(--bg-subtle)); border: 1px solid var(--border); border-top-left-radius: 4px; }
    .user-bubble { background: var(--chat-user-bubble, var(--primary)); color: #fff; border-top-right-radius: 4px; }
    
    .draft-card { margin-top: 14px; padding: 18px; border-radius: var(--radius-md); background: var(--bg-surface); border: 1px solid rgba(var(--primary-rgb), 0.4); box-shadow: var(--shadow-md); color: var(--text-main); }
    .draft-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
    .draft-card-title { font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px; }
    .badge-status-draft { font-size: 0.68rem; background: rgba(var(--primary-rgb), 0.12); color: var(--primary); border: 1px solid rgba(var(--primary-rgb), 0.3); padding: 2px 8px; border-radius: var(--radius-full); font-weight: 700; }
    .draft-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
    .df-label { display: block; font-size: 0.7rem; color: var(--text-dim); font-weight: 700; text-transform: uppercase; }
    .df-val { font-size: 0.85rem; font-weight: 600; }
    .draft-desc-box { background: var(--bg-subtle); padding: 10px 14px; border-radius: var(--radius-sm); font-size: 0.85rem; margin-bottom: 14px; }
    .draft-actions { display: flex; gap: 10px; }
    .draft-confirmed { display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 0.85rem; }
    .draft-rejected { display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 0.85rem; }
    
    .draft-badges { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }
    .draft-activity-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: var(--radius-full); background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); color: var(--primary); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; }
    .draft-activity-badge .material-symbols-outlined { font-size: 14px; }
    .draft-restriction-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: var(--radius-full); font-size: 0.72rem; font-weight: 700; }
    .draft-restriction-badge.warn { background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.3); color: #fbbf24; }
    .draft-restriction-badge.info { background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.3); color: #60a5fa; }
    .draft-restriction-badge .material-symbols-outlined { font-size: 14px; }
    
    .chat-input-bar { padding: 16px 24px; border-top: 1px solid var(--border); background: var(--bg-subtle); display: flex; gap: 12px; }
    .chat-text-input { flex: 1; padding: 12px 18px; border-radius: var(--radius-full); background: var(--bg-surface); border: 1px solid var(--border); color: var(--text-main); font-family: inherit; font-size: 0.9rem; outline: none; }
    
    .btn { padding: 9px 16px; border-radius: var(--radius-md); font-family: inherit; font-weight: 600; font-size: 0.85rem; border: 1px solid transparent; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; transition: var(--transition); }
    .btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-hover)); color: #fff; }
    .btn-outlined { background: transparent; border-color: var(--border); color: var(--text-main); }
    .btn-success { background: var(--success); color: #fff; }
    .btn-danger { background: var(--danger); color: #fff; }
    .btn-sm { padding: 7px 12px; font-size: 0.78rem; }
    .btn-send { border-radius: var(--radius-full); padding: 10px 22px; }
    
    .badge-priority { font-size: 0.75rem; font-weight: 800; text-transform: uppercase; }
    .priority-low { color: #34d399; }
    .priority-medium { color: #fbbf24; }
    .priority-high { color: #f87171; }
    .priority-critical { color: #ff0055; text-shadow: 0 0 10px rgba(255, 0, 85, 0.4); }
    
    .text-accent { color: var(--accent); }
    .text-green { color: var(--success); }
    .text-danger { color: var(--danger); }
    .text-muted { color: var(--text-muted); }
    .text-sm { font-size: 0.8rem; }
    .ml-2 { margin-left: 8px; }
    
    .animate-fade { animation: fadeIn 0.25s ease-out; }
    .animate-pop { animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes popIn { 0% { opacity: 0; transform: scale(0.9); } 100% { opacity: 1; transform: scale(1); } }
    
    .typing-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: var(--text-muted); margin: 0 2px; animation: bounce 1.4s infinite ease-in-out both; }
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .draft-op-box { background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.82rem; }
    .p-3 { padding: 12px; }
    .mb-2 { margin-bottom: 8px; }
    .mb-3 { margin-bottom: 12px; }
    .mt-1 { margin-top: 4px; }
    .mt-2 { margin-top: 8px; }
    .pt-2 { padding-top: 8px; }
    .border-top { border-top: 1px solid var(--border); }
    .text-dim { color: var(--text-dim); }
    .uppercase { text-transform: uppercase; }
    .flex-wrap { flex-wrap: wrap; }

    .op-mode-pill { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: var(--radius-full); font-size: 0.7rem; font-weight: 700; text-transform: uppercase; background: rgba(99, 102, 241, 0.12); color: var(--primary); border: 1px solid rgba(99, 102, 241, 0.3); }
    .op-mode-pill .material-symbols-outlined { font-size: 14px; }
    .op-downtime-pill { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: var(--radius-full); font-size: 0.7rem; font-weight: 700; background: rgba(16, 185, 129, 0.12); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .op-downtime-pill.downtime-warn { background: rgba(239, 68, 68, 0.12); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .op-downtime-pill.downtime-lockout { background: rgba(245, 158, 11, 0.12); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .op-downtime-pill .material-symbols-outlined { font-size: 14px; }

    .prereq-mini-list { list-style: none; padding-left: 0; margin: 4px 0 0 0; display: flex; flex-direction: column; gap: 4px; color: var(--text-main); }
    .draft-risk-warning { display: flex; align-items: center; gap: 6px; background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); padding: 6px 10px; border-radius: var(--radius-sm); font-size: 0.75rem; color: var(--text-main); margin-top: 6px; }
    .draft-risk-warning .material-symbols-outlined { font-size: 16px; flex-shrink: 0; }

    .checkbox-label { display: flex; align-items: flex-start; gap: 8px; font-size: 0.78rem; cursor: pointer; color: var(--text-main); line-height: 1.3; }
    .checkbox-label input { margin-top: 2px; accent-color: var(--primary); }

    .chat-downtime-input { width: 100%; background: var(--bg-surface); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 6px 10px; font-size: 0.8rem; color: var(--text-main); margin-top: 4px; box-sizing: border-box; }
    .chat-downtime-input:focus { border-color: var(--primary); outline: none; }

    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
  `]
})
export class ChatComponent implements OnInit {
  api = inject(ApiService);
  cdr = inject(ChangeDetectorRef);

  @ViewChild('chatScrollContainer') chatScrollContainer!: ElementRef;

  chatSessionId: string | null = null;
  chatMessages: ChatMessage[] = [];
  currentInput = '';
  isThinking = false;

  ngOnInit() {
    this.startNewChatSession();
  }

  async startNewChatSession() {
    try {
      const res = await this.api.post('/api/chat/sessions', {});
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
    this.scrollToBottom();

    try {
      const res = await this.api.post(`/api/chat/sessions/${this.chatSessionId}/messages`, { content: text });
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

  async approveDraft(draft: any) {
    try {
      const res = await this.api.post(`/api/chat/sessions/${this.chatSessionId}/drafts/${draft.id}/approve`, {});
      if (res.ok) {
        draft.approved = true;
        this.cdr.detectChanges();
      }
    } catch (e) { console.error(e); }
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
