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
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 no-print">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Prepare Meeting Intelligence</span>
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Generate an evidence-grounded, one-page executive brief covering the preceding 30 days.
          </p>
        </div>

        {/* Secondary Calendar Modal Trigger */}
        <button
          type="button"
          onClick={onOpenCalendar}
          className="text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 hover:text-slate-900 px-3 py-2 rounded-lg border border-slate-200 transition-colors flex items-center gap-1.5"
        >
          <Calendar className="h-3.5 w-3.5 text-slate-500" />
          <span>Calendar Sync</span>
        </button>
      </div>

      {/* Preset Quick Fill Chips */}
      <div className="mb-6 flex flex-wrap items-center gap-2 text-xs">
        <span className="text-slate-400 font-medium">Quick Demo Targets:</span>
        <button
          type="button"
          onClick={() => loadPreset('Stripe', 'Patrick Collison', 'CEO & Co-founder', 'Strategic Agentic Payment Infrastructure Review')}
          className="px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-medium transition-colors"
        >
          Stripe (Patrick Collison)
        </button>
        <button
          type="button"
          onClick={() => loadPreset('Databricks', 'Ali Ghodsi', 'CEO & Co-founder', 'Data Intelligence & Generative AI Platform Strategy')}
          className="px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-medium transition-colors"
        >
          Databricks (Ali Ghodsi)
        </button>
        <button
          type="button"
          onClick={() => loadPreset('Tavily', 'Roy Elkabetz', 'CEO', 'Autonomous Search Integration for Agentic Workflows')}
          className="px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-medium transition-colors"
        >
          Tavily (Roy Elkabetz)
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Target Company */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Target Company *
            </label>
            <div className="relative">
              <Building2 className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                required
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Stripe, Databricks, Snowflake"
                className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
              />
            </div>
          </div>

          {/* Attendee Name */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Primary Attendee *
            </label>
            <div className="relative">
              <User className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                required
                value={attendee}
                onChange={(e) => setAttendee(e.target.value)}
                placeholder="e.g. Patrick Collison"
                className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
              />
            </div>
          </div>

          {/* Attendee Role */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Attendee Role / Title
            </label>
            <input
              type="text"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="e.g. CEO, VP Engineering, Head of Product"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
            />
          </div>

          {/* Meeting Datetime */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Meeting Date & Time *
            </label>
            <div className="relative">
              <Clock className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                required
                value={datetime}
                onChange={(e) => setDatetime(e.target.value)}
                placeholder="e.g. 2026-11-20 14:00 UTC"
                className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
              />
            </div>
          </div>
        </div>

        {/* Meeting Goal */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            Meeting Objective / Context
          </label>
          <div className="relative">
            <Target className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Partnership discussion, enterprise sales discovery, technical evaluation"
              className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
            />
          </div>
        </div>

        {/* Submit Action */}
        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            disabled={isLoading}
            className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-indigo-200"
          >
            {isLoading ? (
              <>
                <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
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
