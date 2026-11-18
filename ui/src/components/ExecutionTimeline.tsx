import React from 'react';
import { CheckCircle2, Clock, Globe, ShieldCheck, FileText, ChevronRight } from 'lucide-react';
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

  const getStageStatus = (stageId: string) => {
    if (isComplete) return 'done';
    const stageOrder = ['query_planning', 'parallel_research', 'evidence_verification', 'dossier_synthesis'];
    const currentIdx = stageOrder.indexOf(currentStage);
    const thisIdx = stageOrder.indexOf(stageId);

    if (thisIdx < currentIdx) return 'done';
    if (thisIdx === currentIdx) return 'active';
    return 'pending';
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6 no-print">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <span>Execution Progress & Safe Streaming Pipeline</span>
        </h3>
        {claimsStats && (
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            {claimsStats.verified_count} Primary / {claimsStats.reported_count} Secondary Grounded
          </span>
        )}
      </div>

      {/* Progress Steps */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
        {stages.map((st) => {
          const status = getStageStatus(st.id);
          const Icon = st.icon;

          return (
            <div
              key={st.id}
              className={`p-3 rounded-xl border flex items-center space-x-2.5 transition-all ${
                status === 'done'
                  ? 'bg-emerald-50/50 border-emerald-200 text-emerald-900'
                  : status === 'active'
                  ? 'bg-indigo-50/70 border-indigo-300 text-indigo-900 ring-1 ring-indigo-200'
                  : 'bg-slate-50 border-slate-200 text-slate-400'
              }`}
            >
              {status === 'done' ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
              ) : status === 'active' ? (
                <div className="h-4 w-4 rounded-full border-2 border-indigo-600 border-t-transparent animate-spin shrink-0" />
              ) : (
                <Icon className="h-4 w-4 text-slate-400 shrink-0" />
              )}
              <span className="text-xs font-semibold truncate">{st.label}</span>
            </div>
          );
        })}
      </div>

      {/* Status Description Bar */}
      {stageDescription && (
        <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-center space-x-2">
          <ChevronRight className="h-3.5 w-3.5 text-indigo-500 shrink-0" />
          <span className="truncate">{stageDescription}</span>
        </div>
      )}

      {/* Discovered Sources Live Feed */}
      {sources.length > 0 && (
        <div className="mt-4 pt-3 border-t border-slate-100">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span>Discovered Evidence Sources ({sources.length}):</span>
          </div>
          <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
            {sources.map((s, idx) => (
              <a
                key={idx}
                href={s.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium border border-slate-200 transition-colors truncate max-w-xs"
              >
                <span className={`h-1.5 w-1.5 rounded-full ${s.tier === 1 ? 'bg-indigo-500' : 'bg-emerald-500'}`} />
                <span className="truncate">{s.title || s.url}</span>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
