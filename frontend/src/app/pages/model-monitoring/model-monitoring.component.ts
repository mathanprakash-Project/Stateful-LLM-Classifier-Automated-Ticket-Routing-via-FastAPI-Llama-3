import { Component, OnInit, OnDestroy, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

interface InvocationLog {
  id: string;
  timestamp: string;
  node: string;
  tier: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  status: string;
}

interface TierDetail {
  name: string;
  model: string;
  calls: number;
  tokens: number;
  avg_latency_ms: number;
  cost_profile: string;
  role: string;
}

interface MetricsData {
  overview: {
    total_calls: number;
    successful_calls: number;
    failed_calls: number;
    success_rate_pct: number;
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
    average_latency_ms: number;
    monolithic_baseline_cost_usd: number;
    supporthub_tiered_cost_usd: number;
    cost_savings_usd: number;
    cost_savings_pct: number;
  };
  tiered_router: {
    micro: TierDetail;
    mid: TierDetail;
    strong: TierDetail;
  };
  rag_retrieval: {
    total_kb_documents: number;
    retrieval_queries: number;
    dense_vector_dim: string;
    hybrid_fusion_ratio: string;
    flywheel_resolutions_indexed: number;
    status: string;
  };
  rai_safety: {
    scanned_messages: number;
    pii_redactions: number;
    promise_phrases_blocked: number;
    legal_phrases_sanitized: number;
    competitor_mentions_blocked: number;
    status: string;
  };
  consensus_validation: {
    total_runs: number;
    unanimous_rate_pct: number;
    split_decisions: number;
    escalations_to_human: number;
    validator_pool_size: number;
    status: string;
  };
  model_distribution: { [model: string]: number };
  node_distribution: { [node: string]: number };
  recent_invocations: InvocationLog[];
}

@Component({
  selector: 'app-model-monitoring',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  template: `
    <div class="model-monitoring-view animate-fade">
      
      <!-- TOP BANNER -->
      <div class="corona-banner mb-6">
        <div class="banner-content">
          <div class="banner-icon-wrap icon-cyan-glow">
            <span class="material-symbols-outlined banner-icon">monitoring</span>
          </div>
          <div class="banner-text">
            <div class="flex items-center gap-2">
              <h3 class="banner-title">LLM Observability & Model Router Monitoring</h3>
              <span class="live-pulse-badge">
                <span class="pulse-dot"></span> LIVE TELEMETRY
              </span>
            </div>
            <p class="banner-desc">Real-time inspection of tiered model routing, hybrid retrieval (RAG) vector/sparse fusion, Responsible AI safety gates, and multi-agent consensus validation.</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button class="btn btn-sm btn-outlined flex items-center gap-1" (click)="loadMetrics()" [disabled]="isLoading">
            <span class="material-symbols-outlined" [class.spin-anim]="isLoading">refresh</span>
            <span>Refresh</span>
          </button>
          <label class="auto-refresh-toggle flex items-center gap-2 text-xs text-muted cursor-pointer">
            <input type="checkbox" [(ngModel)]="autoRefresh" (change)="toggleAutoRefresh()" />
            <span>Auto-Refresh (5s)</span>
          </label>
        </div>
      </div>

      <!-- KEY METRICS OVERVIEW (4 SUMMARY CARDS) -->
      <div class="grid grid-cols-4 gap-4 mb-6" *ngIf="metrics">
        <!-- 1. TOTAL INVOCATIONS -->
        <div class="kpi-card card-surface">
          <div class="kpi-header">
            <span class="kpi-title">Total AI Invocations</span>
            <div class="kpi-icon icon-purple"><span class="material-symbols-outlined">hub</span></div>
          </div>
          <div class="kpi-value">{{ metrics.overview.total_calls | number }}</div>
          <div class="kpi-footer text-success">
            <span class="material-symbols-outlined text-xs">check_circle</span>
            <span>{{ metrics.overview.success_rate_pct }}% Success Rate ({{ metrics.overview.successful_calls }} ok / {{ metrics.overview.failed_calls }} err)</span>
          </div>
        </div>

        <!-- 2. COST ROUTER SAVINGS -->
        <div class="kpi-card card-surface">
          <div class="kpi-header">
            <span class="kpi-title">Cost Router Efficiency</span>
            <div class="kpi-icon icon-green"><span class="material-symbols-outlined">savings</span></div>
          </div>
          <div class="kpi-value text-green">{{ metrics.overview.cost_savings_pct }}% <span class="text-xs text-muted font-normal">saved</span></div>
          <div class="kpi-footer text-muted">
            <span>Tiered: \${{ metrics.overview.supporthub_tiered_cost_usd | number:'1.4-4' }} vs GPT-4: \${{ metrics.overview.monolithic_baseline_cost_usd | number:'1.4-4' }}</span>
          </div>
        </div>

        <!-- 3. TOKEN CONSUMPTION -->
        <div class="kpi-card card-surface">
          <div class="kpi-header">
            <span class="kpi-title">Token Consumption</span>
            <div class="kpi-icon icon-orange"><span class="material-symbols-outlined">token</span></div>
          </div>
          <div class="kpi-value">{{ metrics.overview.total_tokens | number }}</div>
          <div class="kpi-footer text-muted">
            <span>Prompt: {{ metrics.overview.prompt_tokens | number }} • Completion: {{ metrics.overview.completion_tokens | number }}</span>
          </div>
        </div>

        <!-- 4. AVERAGE LATENCY -->
        <div class="kpi-card card-surface">
          <div class="kpi-header">
            <span class="kpi-title">Avg Pipeline Latency</span>
            <div class="kpi-icon icon-blue"><span class="material-symbols-outlined">timer</span></div>
          </div>
          <div class="kpi-value">{{ metrics.overview.average_latency_ms }} <span class="text-xs text-muted font-normal">ms</span></div>
          <div class="kpi-footer text-cyan">
            <span class="material-symbols-outlined text-xs">bolt</span>
            <span>Low-Latency Tiered Micro Routing</span>
          </div>
        </div>
      </div>

      <!-- TIERED MODEL COST ROUTER ARCHITECTURE (3-TIER BREAKDOWN) -->
      <div class="section-title-row mb-3 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-purple">alt_route</span>
          <h3 class="text-md font-bold text-white uppercase tracking-wider">Tiered Model Cost Router (Module 2)</h3>
        </div>
        <span class="badge-tag role-manager">Dynamic Routing per Pipeline Node</span>
      </div>

      <div class="grid grid-cols-3 gap-4 mb-6" *ngIf="metrics">
        <!-- MICRO TIER -->
        <div class="tier-card card-surface">
          <div class="tier-badge-pill pill-micro">
            <span class="material-symbols-outlined text-xs">bolt</span> MICRO TIER
          </div>
          <h4 class="tier-name">{{ metrics.tiered_router.micro.name }}</h4>
          <p class="tier-role">{{ metrics.tiered_router.micro.role }}</p>
          <div class="tier-meta-box">
            <div class="tier-meta-row">
              <span class="text-muted">Model Engine:</span>
              <strong class="text-main">{{ metrics.tiered_router.micro.model }}</strong>
            </div>
            <div class="tier-meta-row">
              <span class="text-muted">Total Calls:</span>
              <strong class="text-main">{{ metrics.tiered_router.micro.calls }}</strong>
            </div>
            <div class="tier-meta-row">
              <span class="text-muted">Tokens:</span>
              <strong class="text-main">{{ metrics.tiered_router.micro.tokens | number }}</strong>
            </div>
            <div class="tier-meta-row">
              <span class="text-muted">Avg Latency:</span>
              <strong class="text-cyan">{{ metrics.tiered_router.micro.avg_latency_ms }} ms</strong>
            </div>
            <div class="tier-meta-row">
              <span class="text-muted">Cost Profile:</span>
              <span class="text-green font-semibold">{{ metrics.tiered_router.micro.cost_profile }}</span>
            </div>
          </div>
        </div>

        <!-- MID TIER -->
        <div class="tier-card card-surface">
          <div class="tier-badge-pill pill-mid">
            <span class="material-symbols-outlined text-xs">psychology</span> MID TIER
          </div>
          <h4 class="tier-name">{{ metrics.tiered_router.mid.name }}</h4>
          <p class="tier-role">{{ metrics.tiered_router.mid.role }}</p>
          <div class="tier-meta-box">
            <div class="tier-meta-row">
              <span class="text-muted">Model Engine:</span>
              <strong class="text-main">{{ metrics.tiered_router.mid.model }}</strong>
            </div>
            <div class="tier-meta-row">
              <span class="text-muted">Total Calls:</span>
              <strong class="text-main">{{ metrics.tiered_router.mid.calls }}</strong>
            </div>
            <div class="tier-meta-row">
              <span class="text-muted">Tokens:</span>
              <strong class="text-main">{{ metrics.tiered_router.mid.tokens | number }}</strong>
            </div>
            <div class="tier-meta-row">
              <span class="text-muted">Avg Latency:</span>
              <strong class="text-cyan">{{ metrics.tiered_router.mid.avg_latency_ms }} ms</strong>
            </div>
            <div class="tier-meta-row">
              <span class="text-muted">Cost Profile:</span>
              <span class="text-green font-semibold">{{ metrics.tiered_router.mid.cost_profile }}</span>
            </div>
          </div>
        </div>

        <!-- STRONG TIER -->
        <div class="tier-card card-surface">
          <div class="tier-badge-pill pill-strong">
            <span class="material-symbols-outlined text-xs">smart_toy</span> STRONG TIER
          </div>
          <h4 class="tier-name">{{ metrics.tiered_router.strong.name }}</h4>
          <p class="tier-role">{{ metrics.tiered_router.strong.role }}</p>
          <div class="tier-meta-box">
            <div class="tier-meta-row">
              <span class="text-muted">Model Engine:</span>
              <strong class="text-main">{{ metrics.tiered_router.strong.model }}</strong>
            </div>
            <div class="tier-meta-row">
              <span class="text-muted">Total Calls:</span>
              <strong class="text-main">{{ metrics.tiered_router.strong.calls }}</strong>
            </div>
            <div class="tier-meta-row">
              <span class="text-muted">Tokens:</span>
              <strong class="text-main">{{ metrics.tiered_router.strong.tokens | number }}</strong>
            </div>
            <div class="tier-meta-row">
              <span class="text-muted">Avg Latency:</span>
              <strong class="text-cyan">{{ metrics.tiered_router.strong.avg_latency_ms }} ms</strong>
            </div>
            <div class="tier-meta-row">
              <span class="text-muted">Cost Profile:</span>
              <span class="text-green font-semibold">{{ metrics.tiered_router.strong.cost_profile }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- COGNIS RAG + RAI SAFETY + CONSENSUS GRID (3 COLUMNS) -->
      <div class="grid grid-cols-3 gap-4 mb-6" *ngIf="metrics">
        <!-- COGNIS RAG CARD -->
        <div class="subsystem-card card-surface">
          <div class="subsystem-header">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-purple">travel_explore</span>
              <h4 class="subsystem-title">Cognis-Style Hybrid RAG</h4>
            </div>
            <span class="status-pill-green">{{ metrics.rag_retrieval.status }}</span>
          </div>
          <p class="text-xs text-muted mb-3">70% Dense Vector (Matryoshka 768D) + 30% BM25 Keyword Search combined via Reciprocal Rank Fusion.</p>
          <div class="telemetry-stat-list">
            <div class="telemetry-stat-row">
              <span class="text-muted">Knowledge Articles in Index:</span>
              <strong class="text-white">{{ metrics.rag_retrieval.total_kb_documents }} documents</strong>
            </div>
            <div class="telemetry-stat-row">
              <span class="text-muted">Retrieval Queries Processed:</span>
              <strong class="text-white">{{ metrics.rag_retrieval.retrieval_queries }} queries</strong>
            </div>
            <div class="telemetry-stat-row">
              <span class="text-muted">Dense Embedding Dim:</span>
              <strong class="text-white">{{ metrics.rag_retrieval.dense_vector_dim }}</strong>
            </div>
            <div class="telemetry-stat-row">
              <span class="text-muted">Rank Fusion Ratio:</span>
              <span class="text-purple font-semibold">{{ metrics.rag_retrieval.hybrid_fusion_ratio }}</span>
            </div>
            <div class="telemetry-stat-row">
              <span class="text-muted">Flywheel Learned SOPs:</span>
              <span class="text-green font-semibold">+{{ metrics.rag_retrieval.flywheel_resolutions_indexed }} resolved tickets</span>
            </div>
          </div>
        </div>

        <!-- RAI GUARD CARD -->
        <div class="subsystem-card card-surface">
          <div class="subsystem-header">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-green">verified_user</span>
              <h4 class="subsystem-title">Responsible AI (RAI Guard)</h4>
            </div>
            <span class="status-pill-green">{{ metrics.rai_safety.status }}</span>
          </div>
          <p class="text-xs text-muted mb-3">Post-generation safety gate preventing unauthorized promises, legal liabilities, competitor mentions, and redacting PII.</p>
          <div class="telemetry-stat-list">
            <div class="telemetry-stat-row">
              <span class="text-muted">Scanned Agent Responses:</span>
              <strong class="text-white">{{ metrics.rai_safety.scanned_messages }}</strong>
            </div>
            <div class="telemetry-stat-row">
              <span class="text-muted">Redacted PII Entities:</span>
              <span class="text-green font-semibold">{{ metrics.rai_safety.pii_redactions }} items</span>
            </div>
            <div class="telemetry-stat-row">
              <span class="text-muted">Promise Phrases Blocked:</span>
              <span class="text-orange font-semibold">{{ metrics.rai_safety.promise_phrases_blocked }}</span>
            </div>
            <div class="telemetry-stat-row">
              <span class="text-muted">Legal Disclaimers Sanitized:</span>
              <span class="text-white">{{ metrics.rai_safety.legal_phrases_sanitized }}</span>
            </div>
            <div class="telemetry-stat-row">
              <span class="text-muted">Competitor Mentions Neutralized:</span>
              <span class="text-white">{{ metrics.rai_safety.competitor_mentions_blocked }}</span>
            </div>
          </div>
        </div>

        <!-- CONSENSUS VALIDATION CARD -->
        <div class="subsystem-card card-surface">
          <div class="subsystem-header">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-orange">groups</span>
              <h4 class="subsystem-title">3-Agent Consensus Validator</h4>
            </div>
            <span class="status-pill-green">{{ metrics.consensus_validation.status }}</span>
          </div>
          <p class="text-xs text-muted mb-3">Multi-agent majority voting verifying restricted operations (Application Version & Client Data Transfer) before admin routing.</p>
          <div class="telemetry-stat-list">
            <div class="telemetry-stat-row">
              <span class="text-muted">Validation Passes Executed:</span>
              <strong class="text-white">{{ metrics.consensus_validation.total_runs }} runs</strong>
            </div>
            <div class="telemetry-stat-row">
              <span class="text-muted">Unanimous Consensus Rate:</span>
              <span class="text-green font-semibold">{{ metrics.consensus_validation.unanimous_rate_pct }}%</span>
            </div>
            <div class="telemetry-stat-row">
              <span class="text-muted">Split Voting Decisions:</span>
              <span class="text-orange font-semibold">{{ metrics.consensus_validation.split_decisions }}</span>
            </div>
            <div class="telemetry-stat-row">
              <span class="text-muted">Escalations to Human Review:</span>
              <span class="text-white">{{ metrics.consensus_validation.escalations_to_human }}</span>
            </div>
            <div class="telemetry-stat-row">
              <span class="text-muted">Validator Pool:</span>
              <span class="text-purple font-semibold">{{ metrics.consensus_validation.validator_pool_size }} independent agents</span>
            </div>
          </div>
        </div>
      </div>

      <!-- LIVE INVOCATION TELEMETRY LOGS TABLE -->
      <div class="corona-card card-surface mb-6" *ngIf="metrics?.recent_invocations?.length">
        <div class="card-header pb-2 flex items-center justify-between" style="border-bottom: 1px solid var(--corona-border);">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-purple">receipt_long</span>
            <h3 class="card-title">Live Pipeline Invocation Stream (Last 25 Events)</h3>
          </div>
          <span class="text-xs text-muted font-mono">Stream active via centralized model tracker</span>
        </div>

        <div class="table-responsive">
          <table class="corona-table">
            <thead>
              <tr>
                <th>Time (UTC)</th>
                <th>Pipeline Node</th>
                <th>Router Tier</th>
                <th>Model</th>
                <th>Prompt Tokens</th>
                <th>Completion Tokens</th>
                <th>Total Tokens</th>
                <th>Latency</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let inv of metrics.recent_invocations" class="hover-row">
                <td class="font-mono text-xs text-muted">{{ inv.timestamp | date:'HH:mm:ss' }}</td>
                <td>
                  <span class="node-pill pill-node-{{ inv.node }}">{{ inv.node }}</span>
                </td>
                <td>
                  <span class="tier-pill-sm tier-pill-{{ inv.tier }}">{{ inv.tier | uppercase }}</span>
                </td>
                <td class="font-mono text-xs text-white">{{ inv.model }}</td>
                <td class="text-muted text-xs font-mono">{{ inv.prompt_tokens }}</td>
                <td class="text-muted text-xs font-mono">{{ inv.completion_tokens }}</td>
                <td class="text-white font-mono text-xs font-bold">{{ inv.total_tokens }}</td>
                <td class="text-cyan font-mono text-xs">{{ inv.latency_ms }} ms</td>
                <td>
                  <span class="status-badge status-{{ inv.status }}">{{ inv.status | uppercase }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  `,
  styles: [`
    .model-monitoring-view {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    /* TOP BANNER */
    .corona-banner {
      background: linear-gradient(90deg, #1f1d36 0%, #282547 50%, #171626 100%);
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 18px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .banner-content {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .banner-icon-wrap {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: rgba(0, 210, 91, 0.15);
      border: 1px solid rgba(0, 210, 91, 0.3);
      display: grid;
      place-items: center;
      color: var(--corona-green);
    }
    .banner-icon { font-size: 28px; }
    .banner-title {
      font-size: 1.15rem;
      font-weight: 800;
      color: #ffffff;
      margin: 0 0 4px 0;
    }
    .banner-desc {
      font-size: 0.8rem;
      color: var(--text-muted);
      margin: 0;
      max-width: 780px;
      line-height: 1.4;
    }
    .live-pulse-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 2px 8px;
      border-radius: 12px;
      background: rgba(0, 210, 91, 0.15);
      border: 1px solid rgba(0, 210, 91, 0.3);
      color: var(--corona-green);
      font-size: 0.7rem;
      font-weight: 800;
      letter-spacing: 0.5px;
    }
    .pulse-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--corona-green);
      box-shadow: 0 0 8px var(--corona-green);
      animation: pulseAnim 1.5s infinite;
    }
    @keyframes pulseAnim {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.85); }
    }

    /* KPI CARDS */
    .kpi-card {
      background: #000000;
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .kpi-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .kpi-title {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-muted);
      letter-spacing: 0.5px;
    }
    .kpi-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      font-size: 18px;
    }
    .kpi-value {
      font-size: 1.65rem;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.5px;
    }
    .kpi-footer {
      font-size: 0.73rem;
      display: flex;
      align-items: center;
      gap: 4px;
    }

    /* TIER CARDS */
    .tier-card {
      background: #000000;
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 16px;
      display: flex;
      flex-direction: column;
      position: relative;
    }
    .tier-badge-pill {
      align-self: flex-start;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 0.68rem;
      font-weight: 800;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
    }
    .pill-micro { background: rgba(0, 144, 231, 0.2); color: var(--corona-blue); border: 1px solid rgba(0, 144, 231, 0.4); }
    .pill-mid { background: rgba(110, 86, 207, 0.2); color: var(--corona-purple); border: 1px solid rgba(110, 86, 207, 0.4); }
    .pill-strong { background: rgba(255, 171, 0, 0.2); color: var(--corona-orange); border: 1px solid rgba(255, 171, 0, 0.4); }

    .tier-name {
      font-size: 0.95rem;
      font-weight: 700;
      color: #ffffff;
      margin: 0 0 4px 0;
    }
    .tier-role {
      font-size: 0.74rem;
      color: var(--text-muted);
      margin: 0 0 12px 0;
      line-height: 1.3;
    }
    .tier-meta-box {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 4px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      font-size: 0.78rem;
    }
    .tier-meta-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    /* SUBSYSTEM CARDS */
    .subsystem-card {
      background: #000000;
      border: 1px solid var(--corona-border);
      border-radius: var(--radius-sm);
      padding: 16px;
      display: flex;
      flex-direction: column;
    }
    .subsystem-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
    }
    .subsystem-title {
      font-size: 0.9rem;
      font-weight: 700;
      color: #ffffff;
      margin: 0;
    }
    .status-pill-green {
      padding: 2px 8px;
      border-radius: 10px;
      background: rgba(0, 210, 91, 0.15);
      border: 1px solid rgba(0, 210, 91, 0.3);
      color: var(--corona-green);
      font-size: 0.68rem;
      font-weight: 700;
    }
    .telemetry-stat-list {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 4px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      font-size: 0.78rem;
      margin-top: auto;
    }
    .telemetry-stat-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    /* TABLE */
    .corona-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.8rem;
    }
    .corona-table th {
      text-align: left;
      padding: 10px 12px;
      color: var(--text-muted);
      font-weight: 700;
      font-size: 0.72rem;
      text-transform: uppercase;
      border-bottom: 1px solid var(--corona-border);
    }
    .corona-table td {
      padding: 10px 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    .hover-row:hover {
      background: rgba(255, 255, 255, 0.02);
    }

    /* PILLS */
    .node-pill {
      display: inline-block;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.7rem;
      font-weight: 600;
      font-family: monospace;
      background: rgba(110, 86, 207, 0.15);
      color: var(--corona-purple);
      border: 1px solid rgba(110, 86, 207, 0.3);
    }
    .tier-pill-sm {
      display: inline-block;
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 0.65rem;
      font-weight: 800;
    }
    .tier-pill-micro { background: rgba(0, 144, 231, 0.2); color: var(--corona-blue); }
    .tier-pill-mid { background: rgba(110, 86, 207, 0.2); color: var(--corona-purple); }
    .tier-pill-strong { background: rgba(255, 171, 0, 0.2); color: var(--corona-orange); }

    .spin-anim {
      animation: spin 1s linear infinite;
    }
    @keyframes spin { 100% { transform: rotate(360deg); } }
  `]
})
export class ModelMonitoringComponent implements OnInit, OnDestroy {
  api = inject(ApiService);
  auth = inject(AuthService);
  cdr = inject(ChangeDetectorRef);

  metrics: MetricsData | null = null;
  isLoading = false;
  autoRefresh = true;
  private refreshTimer: any = null;

  ngOnInit() {
    this.loadMetrics();
    this.startAutoRefresh();
  }

  ngOnDestroy() {
    this.stopAutoRefresh();
  }

  async loadMetrics() {
    this.isLoading = true;
    try {
      const res = await this.api.getModelMonitoringMetrics();
      if (res.ok) {
        this.metrics = await res.json();
      }
    } catch (err) {
      console.error('Failed to load model monitoring metrics:', err);
    } finally {
      this.isLoading = false;
      this.cdr.detectChanges();
    }
  }

  startAutoRefresh() {
    this.stopAutoRefresh();
    if (this.autoRefresh) {
      this.refreshTimer = setInterval(() => {
        this.loadMetrics();
      }, 5000);
    }
  }

  stopAutoRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  toggleAutoRefresh() {
    if (this.autoRefresh) {
      this.startAutoRefresh();
    } else {
      this.stopAutoRefresh();
    }
  }
}
