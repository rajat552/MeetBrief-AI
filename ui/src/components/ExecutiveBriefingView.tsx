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
  ChevronUp,
  TrendingUp,
  Sparkles,
  Zap,
  Cpu
} from 'lucide-react';
import { OnePageBriefing, ResearchFinding } from '../types/briefing';
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
      <div className="tavily-card p-6 sm:p-8 mt-6 print-page">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-[#EAE4D8]">
          <div className="flex items-center space-x-2 text-[#2E5A44] font-semibold text-sm">
            <div className="h-2 w-2 rounded-full bg-[#16A34A] animate-ping" />
            <span>Streaming Executive Dossier...</span>
          </div>
          <ExportToolbar markdownContent={streamingMarkdown} />
        </div>
        <div className="prose prose-stone max-w-none text-[#18181B] text-sm leading-relaxed">
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
- Target Market: ${briefing.card2_company_profile.target_market}
- Competitive Moat: ${briefing.card2_company_profile.competitive_moat}
- Key Competitors: ${briefing.card2_company_profile.key_competitors.join(', ')}

## 3. Attendee Dossier: ${briefing.card3_attendee_dossier.name}
- Verified Title: ${briefing.card3_attendee_dossier.verified_title || 'N/A'}
- Career History: ${briefing.card3_attendee_dossier.career_history.join('; ')}
- Public Stances: ${briefing.card3_attendee_dossier.public_stances_and_quotes.join('; ')}
- Likely Agenda: ${briefing.card3_attendee_dossier.likely_agenda || 'Strategic discussion'}
- Communication Hook: ${briefing.card3_attendee_dossier.communication_hook || 'Direct collaboration'}

## 4. Preceding 30-Day Signals
${briefing.card4_recent_30d_signals.map(s => `### [${s.category.toUpperCase()}] ${s.title} (${s.published_date || 'Within window'})\n${s.summary}\nSource: ${s.source_url}`).join('\n\n')}

## 5. Strategic Discussion Hooks
${briefing.card5_discussion_hooks.map((hook, i) => `${i + 1}. ${hook}`).join('\n')}

## 6. Risk Blindspots & Open Questions
${briefing.card6_risk_blindspots.map(q => `- ${q}`).join('\n')}
  `.trim();

  return (
    <div className="tavily-card p-6 sm:p-8 mt-6 space-y-6 print-page">
      {/* Dossier Header Banner */}
      <div className="border-b border-[#EAE4D8] pb-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-[11px] font-bold uppercase tracking-wider text-[#2E5A44] mb-1">
              <span>Executive Intelligence Dossier</span>
              <span>•</span>
              <span>Preceding 30 Days</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#18181B] tracking-tight flex items-center gap-2">
              <span>{briefing.target_company}</span>
              <span className="text-[#A1A1AA] font-light">—</span>
              <span className="text-[#3F3F46] font-semibold">{briefing.target_attendee}</span>
            </h1>
            <p className="text-xs text-[#71717A] mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="flex items-center gap-1 font-medium">
                <Calendar className="h-3.5 w-3.5 text-[#2E5A44]" />
                {briefing.meeting_datetime}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Target className="h-3.5 w-3.5 text-[#8C8C94]" />
                {briefing.meeting_goal || 'Strategic Discussion'}
              </span>
            </p>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            {/* Confidence & Route Badges */}
            <div className="flex items-center gap-2">
              <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#EAF2EC] text-[#2E5A44] border border-[#D5E5DA] text-xs font-semibold shadow-2xs">
                <ShieldCheck className="h-3.5 w-3.5 text-[#16A34A]" />
                <span>{Math.round(briefing.aggregate_confidence * 100)}% Fact Grounded</span>
              </div>

              {briefing.inference_route && (
                <div
                  className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full border text-[11px] font-semibold shadow-2xs ${
                    briefing.inference_route === 'bifrost_gateway'
                      ? 'bg-[#EAF2EC] text-[#2E5A44] border-[#D5E5DA]'
                      : briefing.inference_route === 'direct_provider_fallback'
                      ? 'bg-[#EFF6FF] text-[#1D4ED8] border-[#DBEAFE]'
                      : 'bg-[#F4F0E8] text-[#71717A] border-[#EAE4D8]'
                  }`}
                  title={`Inference route: ${briefing.inference_route}`}
                >
                  {briefing.inference_route === 'bifrost_gateway' ? (
                    <ShieldCheck className="h-3 w-3 text-[#16A34A]" />
                  ) : briefing.inference_route === 'direct_provider_fallback' ? (
                    <Zap className="h-3 w-3 text-[#2563EB]" />
                  ) : (
                    <Cpu className="h-3 w-3 text-[#71717A]" />
                  )}
                  <span>
                    {briefing.inference_route === 'bifrost_gateway'
                      ? 'Bifrost'
                      : briefing.inference_route === 'direct_provider_fallback'
                      ? 'Direct LLM'
                      : 'Rules'}
                  </span>
                </div>
              )}
            </div>

            <ExportToolbar markdownContent={rawMarkdown} />
          </div>
        </div>
      </div>

      {/* Grid of Cards: 6-Card Executive Structure */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Card 1: Executive Snapshot */}
        <div className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#EAE4D8] space-y-2">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-[#18181B]">
            <Sparkles className="h-4 w-4 text-[#2E5A44]" />
            <span>1. Executive Snapshot</span>
          </div>
          <p className="text-xs text-[#27272A] leading-relaxed">
            {briefing.card1_executive_snapshot}
          </p>
        </div>

        {/* Card 2: Company Profile */}
        <div className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#EAE4D8] space-y-2.5 text-xs">
          <div className="flex items-center space-x-2 font-bold uppercase tracking-wider text-[#18181B]">
            <Building2 className="h-4 w-4 text-[#2E5A44]" />
            <span>2. Strategic Target Profile</span>
          </div>
          <div className="space-y-1.5 text-[#3F3F46]">
            <div>
              <strong className="text-[#18181B]">Business Model:</strong> {briefing.card2_company_profile.business_model}
            </div>
            <div>
              <strong className="text-[#18181B]">Core Products:</strong> {briefing.card2_company_profile.core_products.join(', ')}
            </div>
            <div>
              <strong className="text-[#18181B]">Target Market:</strong> {briefing.card2_company_profile.target_market}
            </div>
            <div>
              <strong className="text-[#18181B]">Competitive Moat:</strong> {briefing.card2_company_profile.competitive_moat}
            </div>
            <div>
              <strong className="text-[#18181B]">Key Competitors:</strong> {briefing.card2_company_profile.key_competitors.join(', ')}
            </div>
          </div>
        </div>

        {/* Card 3: Attendee Dossier */}
        <div className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#EAE4D8] space-y-2.5 text-xs">
          <div className="flex items-center space-x-2 font-bold uppercase tracking-wider text-[#18181B]">
            <User className="h-4 w-4 text-[#2E5A44]" />
            <span>3. Attendee Dossier</span>
          </div>
          <div className="space-y-2 text-[#3F3F46]">
            <div>
              <strong className="text-[#18181B]">Name &amp; Role:</strong> {briefing.card3_attendee_dossier.name} ({briefing.card3_attendee_dossier.verified_title || 'Attendee'})
            </div>
            {briefing.card3_attendee_dossier.career_history.length > 0 && (
              <div>
                <strong className="text-[#18181B]">Career Trajectory:</strong>
                <ul className="list-disc list-inside mt-0.5 space-y-0.5 text-[11px]">
                  {briefing.card3_attendee_dossier.career_history.map((hist, i) => (
                    <li key={i}>{hist}</li>
                  ))}
                </ul>
              </div>
            )}
            {briefing.card3_attendee_dossier.communication_hook && (
              <div>
                <strong className="text-[#18181B]">Communication Hook:</strong>{' '}
                <span className="text-[#2E5A44] font-medium italic">
                  {briefing.card3_attendee_dossier.communication_hook}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Card 4: Recent Signals (Preceding 30 Days) */}
        <div className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#EAE4D8] space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-[#18181B]">
              <TrendingUp className="h-4 w-4 text-[#2E5A44]" />
              <span>4. Verified 30-Day Signals ({briefing.card4_recent_30d_signals.length})</span>
            </div>
            <span className="text-[11px] font-semibold text-[#2E5A44] bg-[#EAF2EC] px-2 py-0.5 rounded-md">
              Strictly Bounded
            </span>
          </div>

          <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
            {briefing.card4_recent_30d_signals.map((sig: ResearchFinding, idx: number) => (
              <div key={idx} className="p-3 rounded-xl bg-white border border-[#EAE4D8] space-y-1 shadow-2xs">
                <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-[#71717A]">
                  <span className="px-1.5 py-0.5 rounded bg-[#FAF8F5] border border-[#EAE4D8] text-[#2E5A44]">
                    {sig.category}
                  </span>
                  {sig.published_date && <span>{sig.published_date.substring(0, 10)}</span>}
                </div>
                <h4 className="font-semibold text-xs text-[#18181B] line-clamp-2">
                  {sig.title}
                </h4>
                <p className="text-[11px] text-[#52525B] line-clamp-2">
                  {sig.summary}
                </p>
                {sig.source_url && (
                  <a
                    href={sig.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[10px] text-[#2E5A44] hover:underline flex items-center space-x-1 pt-0.5 font-medium"
                  >
                    <span className="truncate">Source Citation</span>
                    <ExternalLink className="h-2.5 w-2.5 shrink-0" />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Card 5: Strategic Discussion Hooks */}
        <div className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#EAE4D8] space-y-2.5 text-xs">
          <div className="flex items-center space-x-2 font-bold uppercase tracking-wider text-[#18181B]">
            <MessageSquare className="h-4 w-4 text-[#2E5A44]" />
            <span>5. High-Impact Discussion Hooks</span>
          </div>
          <div className="space-y-2">
            {briefing.card5_discussion_hooks.map((hook: string, idx: number) => (
              <div key={idx} className="p-2.5 rounded-xl bg-white border border-[#EAE4D8] flex items-start space-x-2">
                <span className="h-4 w-4 rounded-full bg-[#EAF2EC] text-[#2E5A44] flex items-center justify-center text-[10px] shrink-0 font-bold mt-0.5">
                  {idx + 1}
                </span>
                <span className="text-[11px] text-[#27272A] leading-snug font-medium">{hook}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Card 6: Risk Blindspots & Open Questions */}
        <div className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#EAE4D8] space-y-2 text-xs">
          <div className="flex items-center space-x-2 font-bold uppercase tracking-wider text-[#DC2626]">
            <HelpCircle className="h-4 w-4 text-[#DC2626]" />
            <span>6. Risk Blindspots &amp; Open Questions</span>
          </div>
          <div className="space-y-2 pt-0.5">
            {briefing.card6_risk_blindspots.map((risk: string, idx: number) => (
              <div key={idx} className="p-2.5 rounded-xl bg-white border border-[#EAE4D8] flex items-start space-x-2">
                <span className="h-4 w-4 rounded-full bg-[#FEF2F2] text-[#DC2626] flex items-center justify-center text-[10px] shrink-0 font-bold mt-0.5">
                  ?
                </span>
                <span className="text-[11px] text-[#3F3F46] leading-snug">{risk}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Undated Quarantine Notice */}
      {briefing.undated_signals.length > 0 && (
        <div className="p-4 rounded-2xl bg-[#FFFBEB] border border-[#FDE68A] text-xs text-[#92400E] space-y-1.5">
          <div className="flex items-center space-x-2 font-bold text-[#B45309]">
            <AlertTriangle className="h-4 w-4 text-[#D97706]" />
            <span>Undated Public Findings (Excluded from 30-Day Window)</span>
          </div>
          <p className="text-[11px]">
            These documents lacked verifiable timestamp metadata and were strictly quarantined from the 30-day signals:
          </p>
          <ul className="list-disc list-inside space-y-0.5 text-[11px]">
            {briefing.undated_signals.map((u, i) => (
              <li key={i}>
                <a href={u.source_url} target="_blank" rel="noreferrer" className="underline hover:text-[#78350F]">
                  {u.title}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Traceable Evidence Grounding Drawer */}
      {briefing.verified_claims.length > 0 && (
        <div className="tavily-card overflow-hidden no-print">
          <button
            type="button"
            onClick={() => setShowClaimsDrawer(!showClaimsDrawer)}
            className="w-full px-5 py-3.5 bg-[#FAF8F5] hover:bg-[#F4F0E8] flex items-center justify-between text-xs font-bold text-[#18181B] transition-colors"
          >
            <div className="flex items-center space-x-2">
              <FileCheck2 className="h-4 w-4 text-[#2E5A44]" />
              <span>Traceable Source Passages &amp; Claim Verification ({briefing.verified_claims.length})</span>
            </div>
            {showClaimsDrawer ? <ChevronUp className="h-4 w-4 text-[#71717A]" /> : <ChevronDown className="h-4 w-4 text-[#71717A]" />}
          </button>

          {showClaimsDrawer && (
            <div className="p-5 space-y-3 bg-white divide-y divide-[#EAE4D8]">
              {briefing.verified_claims.map((claim, idx) => (
                <div key={idx} className="pt-3 first:pt-0 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-[#18181B]">{claim.claim}</span>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase shrink-0 border ${
                      claim.verification_status === 'VERIFIED_PRIMARY'
                        ? 'bg-[#EAF2EC] text-[#2E5A44] border-[#D5E5DA]'
                        : claim.verification_status === 'REPORTED_SECONDARY'
                        ? 'bg-[#EFF6FF] text-[#1D4ED8] border-[#DBEAFE]'
                        : claim.verification_status === 'CONFLICTED'
                        ? 'bg-[#FEF2F2] text-[#DC2626] border-[#FCA5A5]'
                        : 'bg-[#F4F0E8] text-[#71717A] border-[#EAE4D8]'
                    }`}>
                      {claim.verification_status} ({Math.round(claim.confidence_score * 100)}%)
                    </span>
                  </div>
                  {claim.source_passage && (
                    <blockquote className="pl-3 border-l-2 border-[#2E5A44] text-[#52525B] italic text-[11px] bg-[#FAF8F5] py-1 rounded-r">
                      "{claim.source_passage}"
                    </blockquote>
                  )}
                  <div className="flex items-center space-x-2 text-[11px] text-[#71717A]">
                    <span>Source:</span>
                    <a href={claim.source_url} target="_blank" rel="noreferrer" className="text-[#2E5A44] hover:underline flex items-center gap-1 font-medium">
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
