import React, { useState } from 'react';
import { Building2, User, Clock, Target, Calendar, ArrowRight } from 'lucide-react';
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

  const loadPreset = (c: string, a: string, r: string, g: string) => {
    setCompany(c);
    setAttendee(a);
    setRole(r);
    setGoal(g);
  };

  return (
    <div className="glass-card p-6 sm:p-8 no-print">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-theme-primary tracking-tight flex items-center gap-2">
            <span>Prepare Meeting Intelligence</span>
          </h2>
          <p className="text-sm text-theme-muted mt-1">
            Generate an evidence-grounded, one-page executive brief covering the preceding 30 days.
          </p>
        </div>

        {/* Secondary Calendar Modal Trigger */}
        <button
          type="button"
          onClick={onOpenCalendar}
          className="text-xs font-medium text-theme-text bg-theme-glass hover:bg-[rgba(255,240,225,0.1)] px-3 py-2 rounded-xl border border-theme-glass-border transition-colors flex items-center gap-1.5 backdrop-blur-sm"
        >
          <Calendar className="h-3.5 w-3.5 text-theme-muted" />
          <span>Calendar Sync</span>
        </button>
      </div>

      {/* Preset Quick Fill Chips */}
      <div className="mb-6 flex flex-wrap items-center gap-2 text-xs">
        <span className="text-theme-muted font-medium">Quick Demo Targets:</span>
        <button
          type="button"
          onClick={() => loadPreset('Stripe', 'Patrick Collison', 'CEO & Co-founder', 'Strategic Agentic Payment Infrastructure Review')}
          className="px-2.5 py-1 rounded-lg bg-theme-glass text-theme-accent hover:border-theme-accent border border-theme-glass-border font-medium transition-all backdrop-blur-sm"
        >
          Stripe (Patrick Collison)
        </button>
        <button
          type="button"
          onClick={() => loadPreset('Databricks', 'Ali Ghodsi', 'CEO & Co-founder', 'Data Intelligence & Generative AI Platform Strategy')}
          className="px-2.5 py-1 rounded-lg bg-theme-glass text-theme-accent hover:border-theme-accent border border-theme-glass-border font-medium transition-all backdrop-blur-sm"
        >
          Databricks (Ali Ghodsi)
        </button>
        <button
          type="button"
          onClick={() => loadPreset('Tavily', 'Roy Elkabetz', 'CEO', 'Autonomous Search Integration for Agentic Workflows')}
          className="px-2.5 py-1 rounded-lg bg-theme-glass text-theme-accent hover:border-theme-accent border border-theme-glass-border font-medium transition-all backdrop-blur-sm"
        >
          Tavily (Roy Elkabetz)
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Target Company */}
          <div>
            <label className="block text-xs font-semibold text-theme-primary uppercase tracking-wider mb-1.5">
              Target Company *
            </label>
            <div className="relative">
              <Building2 className="h-4 w-4 absolute left-3 top-3 text-theme-muted" />
              <input
                type="text"
                required
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Stripe, Databricks, Snowflake"
                className="w-full pl-9 pr-3 py-2 text-sm rounded-xl border border-theme-glass-border focus:outline-none focus:ring-2 focus:ring-theme-primary focus:border-theme-primary bg-transparent text-theme-text placeholder:text-theme-muted transition-all"
              />
            </div>
          </div>

          {/* Attendee Name */}
          <div>
            <label className="block text-xs font-semibold text-theme-primary uppercase tracking-wider mb-1.5">
              Primary Attendee *
            </label>
            <div className="relative">
              <User className="h-4 w-4 absolute left-3 top-3 text-theme-muted" />
              <input
                type="text"
                required
                value={attendee}
                onChange={(e) => setAttendee(e.target.value)}
                placeholder="e.g. Patrick Collison"
                className="w-full pl-9 pr-3 py-2 text-sm rounded-xl border border-theme-glass-border focus:outline-none focus:ring-2 focus:ring-theme-primary focus:border-theme-primary bg-transparent text-theme-text placeholder:text-theme-muted transition-all"
              />
            </div>
          </div>

          {/* Attendee Role */}
          <div>
            <label className="block text-xs font-semibold text-theme-primary uppercase tracking-wider mb-1.5">
              Attendee Role / Title
            </label>
            <input
              type="text"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="e.g. CEO, VP Engineering, Head of Product"
              className="w-full px-3 py-2 text-sm rounded-xl border border-theme-glass-border focus:outline-none focus:ring-2 focus:ring-theme-primary focus:border-theme-primary bg-transparent text-theme-text placeholder:text-theme-muted transition-all"
            />
          </div>

          {/* Meeting Datetime */}
          <div>
            <label className="block text-xs font-semibold text-theme-primary uppercase tracking-wider mb-1.5">
              Meeting Date & Time *
            </label>
            <div className="relative">
              <Clock className="h-4 w-4 absolute left-3 top-3 text-theme-muted" />
              <input
                type="text"
                required
                value={datetime}
                onChange={(e) => setDatetime(e.target.value)}
                placeholder="e.g. 2026-11-20 14:00 UTC"
                className="w-full pl-9 pr-3 py-2 text-sm rounded-xl border border-theme-glass-border focus:outline-none focus:ring-2 focus:ring-theme-primary focus:border-theme-primary bg-transparent text-theme-text placeholder:text-theme-muted transition-all"
              />
            </div>
          </div>
        </div>

        {/* Meeting Goal */}
        <div>
          <label className="block text-xs font-semibold text-theme-primary uppercase tracking-wider mb-1.5">
            Meeting Objective / Context
          </label>
          <div className="relative">
            <Target className="h-4 w-4 absolute left-3 top-3 text-theme-muted" />
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Partnership discussion, enterprise sales discovery, technical evaluation"
              className="w-full pl-9 pr-3 py-2 text-sm rounded-xl border border-theme-glass-border focus:outline-none focus:ring-2 focus:ring-theme-primary focus:border-theme-primary bg-transparent text-theme-text placeholder:text-theme-muted transition-all"
            />
          </div>
        </div>

        {/* Submit Action */}
        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            disabled={isLoading}
            className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-brand-gradient hover:opacity-95 text-theme-btn-text font-semibold text-sm shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="h-4 w-4 border-2 border-theme-btn-text border-t-transparent rounded-full animate-spin" />
                <span>Running 5-Branch Intelligence Pipeline...</span>
              </>
            ) : (
              <>
                <span>Generate Executive Brief</span>
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
