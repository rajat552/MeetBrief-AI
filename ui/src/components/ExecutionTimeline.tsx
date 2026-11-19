import React from 'react';
import { CheckCircle2, Clock, Globe, ShieldCheck, FileText, ChevronRight, AlertTriangle } from 'lucide-react';
import { SourceDiscoveredEvent, ClaimsVerifiedEvent } from '../types/briefing';

interface ExecutionTimelineProps {
  currentStage: string;
  stageDescription: string;
  sources: SourceDiscoveredEvent[];
  claimsStats: ClaimsVerifiedEvent | null;
  isComplete: boolean;
}

export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({
  currentStage,
  stageDescription,
  sources,
  claimsStats,
  isComplete,
}) => {
  const stages = [
    { id: 'query_planning', label: '1. Temporal Planning', icon: Clock },
    { id: 'parallel_research', label: '2. 5-Branch Research', icon: Globe },
    { id: 'evidence_verification', label: '3. Evidence Grounding', icon: ShieldCheck },
    { id: 'dossier_synthesis', label: '4. Executive Briefing', icon: FileText },
  ];

  const getStageStatus = (stageId: string): 'done' | 'active' | 'pending' | 'failed' => {
    if (isComplete) return 'done';
    const stageOrder = ['query_planning', 'parallel_research', 'evidence_verification', 'dossier_synthesis'];
    const currentIdx = stageOrder.indexOf(currentStage);
    const thisIdx = stageOrder.indexOf(stageId);

    if (thisIdx < currentIdx) return 'done';
    if (thisIdx === currentIdx) return 'active';
    return 'pending';
  };

  return (
    <div className="glass-card p-6 mb-6 no-print">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs font-bold text-theme-primary uppercase tracking-wider flex items-center gap-1.5">
          <span>Execution Progress & Safe Streaming Pipeline</span>
        </h3>
        {claimsStats && (
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-theme-glass text-theme-success border border-theme-glass-border">
            {claimsStats.verified_count} Primary / {claimsStats.reported_count} Secondary Grounded
          </span>
        )}
      </div>

      {/* Progress Steps */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 mb-4">
        {stages.map((st) => {
          const status = getStageStatus(st.id);
          const Icon = st.icon;

          return (
            <div
              key={st.id}
              className={`p-3 rounded-xl border flex items-center space-x-2.5 transition-all ${
                status === 'done'
                  ? 'bg-theme-glass border-theme-success/40 text-theme-success'
                  : status === 'active'
                  ? 'bg-theme-glass border-theme-accent text-theme-accent ring-1 ring-theme-accent/40 animate-gentle-pulse'
                  : status === 'failed'
                  ? 'bg-theme-glass border-theme-danger/40 text-theme-danger'
                  : 'bg-theme-glass/30 border-theme-glass-border text-theme-muted'
              }`}
            >
              {status === 'done' ? (
                <CheckCircle2 className="h-4 w-4 text-theme-success shrink-0" />
              ) : status === 'active' ? (
                <div className="h-4 w-4 rounded-full border-2 border-theme-accent border-t-transparent animate-spin shrink-0" />
              ) : status === 'failed' ? (
                <AlertTriangle className="h-4 w-4 text-theme-danger shrink-0" />
              ) : (
                <Icon className="h-4 w-4 text-theme-muted shrink-0" />
              )}
              <span className="text-xs font-semibold truncate">{st.label}</span>
            </div>
          );
        })}
      </div>

      {/* Status Description Bar */}
      {stageDescription && (
        <div className="p-2.5 rounded-xl bg-theme-glass/60 border border-theme-glass-border text-xs text-theme-text flex items-center space-x-2 backdrop-blur-sm">
          <ChevronRight className="h-3.5 w-3.5 text-theme-accent shrink-0" />
          <span className="truncate">{stageDescription}</span>
        </div>
      )}

      {/* Discovered Sources Live Feed */}
      {sources.length > 0 && (
        <div className="mt-4 pt-3 border-t border-theme-glass-border">
          <div className="flex items-center justify-between text-xs text-theme-muted mb-2">
            <span>Discovered Evidence Sources ({sources.length}):</span>
          </div>
          <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
            {sources.map((s, idx) => (
              <a
                key={idx}
                href={s.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-theme-glass hover:bg-[rgba(255,240,225,0.1)] text-theme-text text-xs font-medium border border-theme-glass-border transition-colors truncate max-w-xs backdrop-blur-sm"
              >
                <span className={`h-1.5 w-1.5 rounded-full ${s.tier === 1 ? 'bg-theme-accent' : 'bg-theme-success'}`} />
                <span className="truncate">{s.title || s.url}</span>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
