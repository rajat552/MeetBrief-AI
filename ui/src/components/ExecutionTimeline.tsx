import React from 'react';
import {
  CheckCircle2,
  Clock,
  Globe,
  ShieldCheck,
  FileText,
  ChevronRight,
  AlertTriangle,
  ExternalLink
} from 'lucide-react';
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
    <div className="tavily-card p-4 sm:p-6 mb-6 no-print">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3.5 sm:mb-4 pb-3 border-b border-[#EAE4D8]">
        <div className="flex items-center space-x-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-[#2E5A44] bg-[#EAF2EC] px-2 py-0.5 rounded-md">
            Pipeline
          </span>
          <h3 className="text-sm font-bold text-[#18181B] tracking-tight">
            Execution Progress &amp; Safe Streaming Pipeline
          </h3>
        </div>

        {claimsStats && (
          <span className="text-xs font-semibold px-2.5 sm:px-3 py-1 rounded-full bg-[#EAF2EC] text-[#2E5A44] border border-[#D5E5DA] shadow-2xs self-start sm:self-auto">
            {claimsStats.verified_count} Primary / {claimsStats.reported_count} Secondary Grounded
          </span>
        )}
      </div>

      {/* Progress Steps Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-2.5 mb-3.5 sm:mb-4">
        {stages.map((st) => {
          const status = getStageStatus(st.id);
          const Icon = st.icon;

          return (
            <div
              key={st.id}
              className={`p-2.5 sm:p-3 rounded-xl border flex items-center space-x-2 sm:space-x-2.5 transition-all ${
                status === 'done'
                  ? 'bg-[#EAF2EC]/60 border-[#D5E5DA] text-[#2E5A44]'
                  : status === 'active'
                  ? 'bg-white border-[#2E5A44] text-[#18181B] shadow-sm ring-1 ring-[#2E5A44]/30 animate-gentle-pulse'
                  : status === 'failed'
                  ? 'bg-[#FEF2F2] border-[#FCA5A5] text-[#DC2626]'
                  : 'bg-[#FAF8F5] border-[#EAE4D8] text-[#8C8C94]'
              }`}
            >
              {status === 'done' ? (
                <CheckCircle2 className="h-4 w-4 text-[#16A34A] shrink-0" />
              ) : status === 'active' ? (
                <div className="h-4 w-4 rounded-full border-2 border-[#2E5A44] border-t-transparent animate-spin shrink-0" />
              ) : status === 'failed' ? (
                <AlertTriangle className="h-4 w-4 text-[#DC2626] shrink-0" />
              ) : (
                <Icon className="h-4 w-4 text-[#A1A1AA] shrink-0" />
              )}
              <span className="text-[11px] sm:text-xs font-semibold truncate">{st.label}</span>
            </div>
          );
        })}
      </div>

      {/* Stage Description Bar */}
      {stageDescription && (
        <div className="p-2.5 sm:p-3 rounded-xl bg-[#FAF8F5] border border-[#EAE4D8] text-xs text-[#18181B] flex items-center space-x-2">
          <ChevronRight className="h-3.5 w-3.5 text-[#2E5A44] shrink-0" />
          <span className="truncate font-medium">{stageDescription}</span>
        </div>
      )}

      {/* Discovered Sources Live Feed */}
      {sources.length > 0 && (
        <div className="mt-3.5 sm:mt-4 pt-3 border-t border-[#EAE4D8]">
          <div className="flex flex-wrap items-center justify-between text-xs text-[#71717A] mb-2 font-medium gap-1">
            <span>Discovered Evidence Sources ({sources.length}):</span>
            <span className="text-[11px] text-[#A1A1AA]">Bounded to 30 days</span>
          </div>
          <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto pr-1">
            {sources.map((s, idx) => (
              <a
                key={idx}
                href={s.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-white hover:bg-[#FAF8F5] border border-[#EAE4D8] text-[11px] text-[#52525B] hover:text-[#18181B] transition-colors shadow-2xs group max-w-[130px] xs:max-w-[170px] sm:max-w-[220px]"
                title={`${s.title} (${s.published_date || 'Within window'})`}
              >
                <Globe className="h-3 w-3 text-[#2E5A44] shrink-0" />
                <span className="truncate">{s.title}</span>
                <ExternalLink className="h-2.5 w-2.5 text-[#A1A1AA] group-hover:text-[#2E5A44] transition-colors shrink-0 ml-0.5" />
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
