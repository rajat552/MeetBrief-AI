import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Building2,
  User,
  Calendar,
  Target,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  MessageSquare,
  HelpCircle,
  FileCheck2,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { OnePageBriefing } from '../types/briefing';
import { ExportToolbar } from './ExportToolbar';

interface ExecutiveBriefingViewProps {
  briefing: OnePageBriefing | null;
  streamingMarkdown: string;
}

export const ExecutiveBriefingView: React.FC<ExecutiveBriefingViewProps> = ({
  briefing,
  streamingMarkdown,
}) => {
  const [showClaimsDrawer, setShowClaimsDrawer] = useState(false);

  // If streaming but structured object not ready, display clean streaming Markdown
  if (!briefing) {
    if (!streamingMarkdown) return null;

    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 mt-6 print-page">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
          <div className="flex items-center space-x-2 text-indigo-600 font-semibold text-sm">
            <div className="h-2 w-2 rounded-full bg-indigo-600 animate-ping" />
            <span>Streaming Executive Dossier...</span>
          </div>
          <ExportToolbar markdownContent={streamingMarkdown} />
        </div>
        <div className="prose prose-slate max-w-none text-slate-800 text-sm">
          <ReactMarkdown>{streamingMarkdown}</ReactMarkdown>
        </div>
      </div>
    );
  }

  const rawMarkdown = `
# Executive Dossier: ${briefing.target_company} — ${briefing.target_attendee}
**Meeting:** ${briefing.meeting_datetime} | **Objective:** ${briefing.meeting_goal || 'Strategic Alignment'}

## 1. Executive Snapshot
${briefing.card1_executive_snapshot}

## 2. Strategic Target Profile
- Business Model: ${briefing.card2_company_profile.business_model}
- Core Products: ${briefing.card2_company_profile.core_products.join(', ')}
- Competitive Moat: ${briefing.card2_company_profile.competitive_moat}

## 3. Key Attendee Dossier
- Role: ${briefing.card3_attendee_dossier.verified_title}
- Agenda: ${briefing.card3_attendee_dossier.likely_agenda}
- Hook: ${briefing.card3_attendee_dossier.communication_hook}

## 4. Preceding 30-Day Signals
${briefing.card4_recent_30d_signals.map(s => `- [${s.category.toUpperCase()}] ${s.title}: ${s.summary}`).join('\n')}

## 5. Strategic Discussion Points
${briefing.card5_discussion_hooks.map((h, i) => `${i + 1}. ${h}`).join('\n')}

## 6. Risk Blindspots & Open Questions
${briefing.card6_risk_blindspots.map(q => `- ${q}`).join('\n')}
  `.trim();

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 mt-6 space-y-6 print-page">
      {/* Dossier Header Banner */}
      <div className="border-b border-slate-200 pb-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-indigo-600 mb-1">
              <span>Executive Intelligence Dossier</span>
              <span>•</span>
              <span>Preceding 30 Days</span>
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <span>{briefing.target_company}</span>
              <span className="text-slate-400 font-light">—</span>
              <span className="text-slate-700 font-semibold">{briefing.target_attendee}</span>
            </h1>
            <p className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5 text-slate-400" />
                {briefing.meeting_datetime}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Target className="h-3.5 w-3.5 text-slate-400" />
                {briefing.meeting_goal || 'Strategic Discussion'}
              </span>
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {/* Confidence Badge */}
            <div className="text-right">
              <div className="inline-flex items-center space-x-1 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                <span>{Math.round(briefing.aggregate_confidence * 100)}% Fact Grounded</span>
              </div>
              <p className="text-[10px] text-slate-400 mt-0.5">
                Route: {briefing.inference_route === 'bifrost_gateway' ? 'Bifrost AI Gateway' : 'Direct Fallback'}
              </p>
            </div>

            <ExportToolbar markdownContent={rawMarkdown} />
          </div>
        </div>
      </div>

      {/* 6-Card Executive Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Card 1: Executive Snapshot */}
        <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 md:col-span-2">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-indigo-600" />
            <span>1. Executive Snapshot & Strategic Context</span>
          </h2>
          <p className="text-sm text-slate-700 leading-relaxed font-normal">
            {briefing.card1_executive_snapshot}
          </p>
        </div>

        {/* Card 2: Strategic Target Profile */}
        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm space-y-3">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-2">
            <Building2 className="h-4 w-4 text-indigo-600" />
            <span>2. Strategic Company Profile</span>
          </h2>
          <div className="text-xs space-y-2 text-slate-600">
            <p>
              <span className="font-semibold text-slate-800">Business Model:</span>{' '}
              {briefing.card2_company_profile.business_model}
            </p>
            <p>
              <span className="font-semibold text-slate-800">Core Products:</span>{' '}
              {briefing.card2_company_profile.core_products.join(', ')}
            </p>
            <p>
              <span className="font-semibold text-slate-800">Competitive Moat:</span>{' '}
              {briefing.card2_company_profile.competitive_moat}
            </p>
            <p>
              <span className="font-semibold text-slate-800">Key Competitors:</span>{' '}
              {briefing.card2_company_profile.key_competitors.join(', ')}
            </p>
          </div>
        </div>

        {/* Card 3: Key Attendee Dossier */}
        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm space-y-3">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-2">
            <User className="h-4 w-4 text-indigo-600" />
            <span>3. Key Attendee Dossier</span>
          </h2>
          <div className="text-xs space-y-2 text-slate-600">
            <p>
              <span className="font-semibold text-slate-800">Role & Title:</span>{' '}
              {briefing.card3_attendee_dossier.verified_title}
            </p>
            <p>
              <span className="font-semibold text-slate-800">Likely Agenda:</span>{' '}
              {briefing.card3_attendee_dossier.likely_agenda}
            </p>
            <p>
              <span className="font-semibold text-slate-800">Conversation Hook:</span>{' '}
              {briefing.card3_attendee_dossier.communication_hook}
            </p>
            {briefing.card3_attendee_dossier.public_stances_and_quotes.length > 0 && (
              <p>
                <span className="font-semibold text-slate-800">Stated Focus:</span>{' '}
                {briefing.card3_attendee_dossier.public_stances_and_quotes[0]}
              </p>
            )}
          </div>
        </div>

        {/* Card 4: Preceding 30-Day Signals */}
        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm md:col-span-2 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Calendar className="h-4 w-4 text-indigo-600" />
              <span>4. Preceding 30-Day Signals (News, Launches & Hiring)</span>
            </h2>
            <span className="text-[11px] text-slate-400 font-medium">Strict Rolling Window</span>
          </div>

          {briefing.card4_recent_30d_signals.length > 0 ? (
            <div className="space-y-2.5">
              {briefing.card4_recent_30d_signals.map((sig, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex flex-col sm:flex-row sm:items-start justify-between gap-2 text-xs">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-indigo-100 text-indigo-800">
                        {sig.category}
                      </span>
                      <a
                        href={sig.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-semibold text-slate-900 hover:text-indigo-600 hover:underline flex items-center gap-1"
                      >
                        <span>{sig.title}</span>
                        <ExternalLink className="h-3 w-3 shrink-0" />
                      </a>
                    </div>
                    <p className="text-slate-600 leading-relaxed">{sig.summary}</p>
                  </div>
                  {sig.published_date && (
                    <span className="text-slate-400 whitespace-nowrap text-[11px] shrink-0 font-medium">
                      {sig.published_date}
                    </span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic p-3">
              No verified public press releases or product drops recorded in the preceding 30 days.
            </p>
          )}
        </div>

        {/* Card 5: High-Impact Discussion Hooks */}
        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm space-y-3">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-2">
            <MessageSquare className="h-4 w-4 text-emerald-600" />
            <span>5. Strategic Discussion Points</span>
          </h2>
          <div className="space-y-2.5">
            {briefing.card5_discussion_hooks.map((hook, i) => (
              <div key={i} className="flex items-start space-x-2.5 text-xs text-slate-700">
                <span className="h-4 w-4 rounded-full bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center shrink-0 mt-0.5 text-[10px]">
                  {i + 1}
                </span>
                <p className="leading-relaxed">{hook}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Card 6: Risk Blindspots & Open Questions */}
        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm space-y-3">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-2">
            <HelpCircle className="h-4 w-4 text-amber-600" />
            <span>6. Risk Blindspots & Open Questions</span>
          </h2>
          <div className="space-y-2.5">
            {briefing.card6_risk_blindspots.map((risk, i) => (
              <div key={i} className="flex items-start space-x-2.5 text-xs text-slate-700">
                <span className="h-4 w-4 rounded-full bg-amber-100 text-amber-800 font-bold flex items-center justify-center shrink-0 mt-0.5 text-[10px]">
                  ?
                </span>
                <p className="leading-relaxed">{risk}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Undated Signals Notice (if any) */}
      {briefing.undated_signals.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 text-xs text-amber-900 space-y-1.5">
          <div className="flex items-center space-x-2 font-bold text-amber-800">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <span>Undated Public Findings (Excluded from 30-Day Window)</span>
          </div>
          <p className="text-[11px] text-amber-700">
            These documents lacked verifiable timestamp metadata and were strictly quarantined from the 30-day signals:
          </p>
          <ul className="list-disc list-inside space-y-0.5 text-[11px]">
            {briefing.undated_signals.map((u, i) => (
              <li key={i}>
                <a href={u.source_url} target="_blank" rel="noreferrer" className="underline hover:text-amber-900">
                  {u.title}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Traceable Evidence Grounding Drawer */}
      {briefing.verified_claims.length > 0 && (
        <div className="border border-slate-200 rounded-xl overflow-hidden no-print">
          <button
            type="button"
            onClick={() => setShowClaimsDrawer(!showClaimsDrawer)}
            className="w-full px-5 py-3.5 bg-slate-50 hover:bg-slate-100 flex items-center justify-between text-xs font-bold text-slate-700 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <FileCheck2 className="h-4 w-4 text-indigo-600" />
              <span>Traceable Source Passages & Claim Verification ({briefing.verified_claims.length})</span>
            </div>
            {showClaimsDrawer ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>

          {showClaimsDrawer && (
            <div className="p-5 space-y-3 bg-white divide-y divide-slate-100">
              {briefing.verified_claims.map((claim, idx) => (
                <div key={idx} className="pt-3 first:pt-0 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-slate-800">{claim.claim}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase shrink-0 ${
                      claim.verification_status === 'VERIFIED_PRIMARY'
                        ? 'bg-emerald-100 text-emerald-800'
                        : claim.verification_status === 'REPORTED_SECONDARY'
                        ? 'bg-blue-100 text-blue-800'
                        : claim.verification_status === 'CONFLICTED'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-slate-100 text-slate-600'
                    }`}>
                      {claim.verification_status} ({Math.round(claim.confidence_score * 100)}%)
                    </span>
                  </div>
                  {claim.source_passage && (
                    <blockquote className="pl-3 border-l-2 border-slate-300 text-slate-500 italic text-[11px]">
                      "{claim.source_passage}"
                    </blockquote>
                  )}
                  <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                    <span>Source:</span>
                    <a href={claim.source_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline flex items-center gap-1">
                      <span>{claim.source_title || claim.source_url}</span>
                      <ExternalLink className="h-2.5 w-2.5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
