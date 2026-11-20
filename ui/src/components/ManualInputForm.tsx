import React, { useState } from 'react';
import { Building2, User, Clock, Target, Calendar, ArrowRight, Briefcase, Sparkles, Check } from 'lucide-react';
import { ManualMeetingRequest } from '../types/briefing';

interface ManualInputFormProps {
  onSubmit: (request: ManualMeetingRequest) => void;
  isLoading: boolean;
  onOpenCalendar: () => void;
}

export const ManualInputForm: React.FC<ManualInputFormProps> = ({
  onSubmit,
  isLoading,
  onOpenCalendar,
}) => {
  const [company, setCompany] = useState('Stripe');
  const [attendee, setAttendee] = useState('Patrick Collison');
  const [role, setRole] = useState('CEO & Co-founder');
  const [datetime, setDatetime] = useState('2026-11-20 14:00 UTC');
  const [goal, setGoal] = useState('Explore enterprise AI payment infrastructure and agentic commerce partnership');
  const [activePreset, setActivePreset] = useState<string>('Stripe');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!company.trim() || !attendee.trim() || !datetime.trim()) return;

    onSubmit({
      company_name: company.trim(),
      attendee_name: attendee.trim(),
      attendee_role: role.trim() || undefined,
      meeting_datetime: datetime.trim(),
      meeting_goal: goal.trim() || undefined,
    });
  };

  const loadPreset = (c: string, a: string, r: string, g: string, key: string) => {
    setCompany(c);
    setAttendee(a);
    setRole(r);
    setGoal(g);
    setActivePreset(key);
  };

  return (
    <div id="meeting-input-form" className="tavily-card p-4 sm:p-6 md:p-8 mb-6 no-print">
      {/* Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 sm:pb-5 mb-4 sm:mb-5 border-b border-[#EAE4D8]">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#2E5A44] bg-[#EAF2EC] px-2 py-0.5 rounded-md">
              Step 1
            </span>
            <h3 className="text-base sm:text-lg font-bold text-[#18181B] tracking-tight">
              Meeting Context &amp; Intelligence Target
            </h3>
          </div>
          <p className="text-xs text-[#71717A]">
            Define meeting parameters to compute the rolling 30-day temporal research boundary.
          </p>
        </div>

        {/* Secondary Calendar Trigger */}
        <button
          type="button"
          onClick={onOpenCalendar}
          className="tavily-btn-secondary px-3.5 py-2 sm:py-1.5 text-xs flex items-center justify-center gap-1.5 self-start sm:self-auto min-h-[36px] rounded-xl"
        >
          <Calendar className="h-3.5 w-3.5 text-[#2E5A44] shrink-0" />
          <span>Calendar Sync</span>
        </button>
      </div>

      {/* Preset Target Quick Fill Chips (Tavily Reference Pattern) */}
      <div className="mb-5 sm:mb-6 p-2.5 sm:p-3 rounded-xl bg-[#FAF8F5] border border-[#EAE4D8] flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold text-[#52525B] mr-1 w-full xs:w-auto">Quick Presets:</span>
        <button
          type="button"
          onClick={() =>
            loadPreset(
              'Stripe',
              'Patrick Collison',
              'CEO & Co-founder',
              'Explore enterprise AI payment infrastructure and agentic commerce partnership',
              'Stripe'
            )
          }
          className={`px-3 py-2 sm:py-1.5 min-h-[36px] rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
            activePreset === 'Stripe'
              ? 'bg-[#18181B] text-white shadow-2xs'
              : 'bg-white text-[#18181B] border border-[#EAE4D8] hover:bg-[#F4F0E8]'
          }`}
        >
          {activePreset === 'Stripe' && <Check className="h-3.5 w-3.5 text-[#4E876F] shrink-0" />}
          <span>Stripe (Patrick Collison)</span>
        </button>
        <button
          type="button"
          onClick={() =>
            loadPreset(
              'Databricks',
              'Ali Ghodsi',
              'CEO & Co-founder',
              'Data Intelligence & Generative AI Platform Strategy Evaluation',
              'Databricks'
            )
          }
          className={`px-3 py-2 sm:py-1.5 min-h-[36px] rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
            activePreset === 'Databricks'
              ? 'bg-[#18181B] text-white shadow-2xs'
              : 'bg-white text-[#18181B] border border-[#EAE4D8] hover:bg-[#F4F0E8]'
          }`}
        >
          {activePreset === 'Databricks' && <Check className="h-3.5 w-3.5 text-[#4E876F] shrink-0" />}
          <span>Databricks (Ali Ghodsi)</span>
        </button>
        <button
          type="button"
          onClick={() =>
            loadPreset(
              'Tavily',
              'Roy Elkabetz',
              'CEO',
              'Autonomous Search Integration for Agentic Workflows & MCP Server',
              'Tavily'
            )
          }
          className={`px-3 py-2 sm:py-1.5 min-h-[36px] rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
            activePreset === 'Tavily'
              ? 'bg-[#18181B] text-white shadow-2xs'
              : 'bg-white text-[#18181B] border border-[#EAE4D8] hover:bg-[#F4F0E8]'
          }`}
        >
          {activePreset === 'Tavily' && <Check className="h-3.5 w-3.5 text-[#4E876F] shrink-0" />}
          <span>Tavily (Roy Elkabetz)</span>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 sm:gap-4">
          {/* Target Company */}
          <div>
            <label className="block text-[11px] font-bold text-[#18181B] uppercase tracking-wider mb-1.5">
              Target Company *
            </label>
            <div className="relative">
              <Building2 className="h-4 w-4 absolute left-3.5 top-3.5 text-[#8C8C94]" />
              <input
                type="text"
                required
                value={company}
                onChange={(e) => {
                  setCompany(e.target.value);
                  setActivePreset('');
                }}
                placeholder="e.g. Stripe, Databricks, Snowflake"
                className="w-full min-h-[44px] bg-[#FAF8F5] focus:bg-white text-xs sm:text-sm text-[#18181B] pl-10 pr-3.5 py-2.5 sm:py-3 rounded-xl border border-[#EAE4D8] focus:border-[#2E5A44] focus:outline-none focus:ring-2 focus:ring-[#2E5A44]/15 transition-all placeholder:text-[#A1A1AA]"
              />
            </div>
          </div>

          {/* Primary Attendee */}
          <div>
            <label className="block text-[11px] font-bold text-[#18181B] uppercase tracking-wider mb-1.5">
              Primary Attendee *
            </label>
            <div className="relative">
              <User className="h-4 w-4 absolute left-3.5 top-3.5 text-[#8C8C94]" />
              <input
                type="text"
                required
                value={attendee}
                onChange={(e) => {
                  setAttendee(e.target.value);
                  setActivePreset('');
                }}
                placeholder="e.g. Patrick Collison"
                className="w-full min-h-[44px] bg-[#FAF8F5] focus:bg-white text-xs sm:text-sm text-[#18181B] pl-10 pr-3.5 py-2.5 sm:py-3 rounded-xl border border-[#EAE4D8] focus:border-[#2E5A44] focus:outline-none focus:ring-2 focus:ring-[#2E5A44]/15 transition-all placeholder:text-[#A1A1AA]"
              />
            </div>
          </div>

          {/* Attendee Role */}
          <div>
            <label className="block text-[11px] font-bold text-[#18181B] uppercase tracking-wider mb-1.5">
              Attendee Role / Title
            </label>
            <div className="relative">
              <Briefcase className="h-4 w-4 absolute left-3.5 top-3.5 text-[#8C8C94]" />
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="e.g. CEO, VP Engineering, Head of Product"
                className="w-full min-h-[44px] bg-[#FAF8F5] focus:bg-white text-xs sm:text-sm text-[#18181B] pl-10 pr-3.5 py-2.5 sm:py-3 rounded-xl border border-[#EAE4D8] focus:border-[#2E5A44] focus:outline-none focus:ring-2 focus:ring-[#2E5A44]/15 transition-all placeholder:text-[#A1A1AA]"
              />
            </div>
          </div>

          {/* Meeting Date & Time */}
          <div>
            <label className="block text-[11px] font-bold text-[#18181B] uppercase tracking-wider mb-1.5">
              Meeting Date &amp; Time (UTC) *
            </label>
            <div className="relative">
              <Clock className="h-4 w-4 absolute left-3.5 top-3.5 text-[#8C8C94]" />
              <input
                type="text"
                required
                value={datetime}
                onChange={(e) => setDatetime(e.target.value)}
                placeholder="e.g. 2026-11-20 14:00 UTC"
                className="w-full min-h-[44px] bg-[#FAF8F5] focus:bg-white text-xs sm:text-sm text-[#18181B] pl-10 pr-3.5 py-2.5 sm:py-3 rounded-xl border border-[#EAE4D8] focus:border-[#2E5A44] focus:outline-none focus:ring-2 focus:ring-[#2E5A44]/15 transition-all placeholder:text-[#A1A1AA]"
              />
            </div>
          </div>
        </div>

        {/* Meeting Objective */}
        <div>
          <label className="block text-[11px] font-bold text-[#18181B] uppercase tracking-wider mb-1.5">
            Meeting Objective &amp; Strategic Context
          </label>
          <div className="relative">
            <Target className="h-4 w-4 absolute left-3.5 top-3.5 text-[#8C8C94]" />
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Partnership discussion, enterprise sales discovery, technical evaluation"
              className="w-full min-h-[44px] bg-[#FAF8F5] focus:bg-white text-xs sm:text-sm text-[#18181B] pl-10 pr-3.5 py-2.5 sm:py-3 rounded-xl border border-[#EAE4D8] focus:border-[#2E5A44] focus:outline-none focus:ring-2 focus:ring-[#2E5A44]/15 transition-all placeholder:text-[#A1A1AA]"
            />
          </div>
        </div>

        {/* Action Button Row */}
        <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="flex items-center justify-center sm:justify-start gap-2 text-xs text-[#71717A]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#16A34A] shrink-0" />
            <span>Tavily Search + LangGraph Agentic Pipeline Ready</span>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full sm:w-auto min-h-[46px] tavily-btn-dark px-6 py-3 sm:py-2.5 text-xs font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm rounded-xl"
          >
            {isLoading ? (
              <>
                <div className="h-3.5 w-3.5 rounded-full border-2 border-white border-t-transparent animate-spin shrink-0" />
                <span>Running Research Pipeline...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-3.5 w-3.5 text-[#4E876F] shrink-0" />
                <span>Generate Executive Brief</span>
                <ArrowRight className="h-3.5 w-3.5 shrink-0" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
