import React, { useState } from 'react';
import { X, Calendar, AlertCircle, ArrowLeft, ArrowRight } from 'lucide-react';

interface CalendarSyncModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUseManual: () => void;
}

export const CalendarSyncModal: React.FC<CalendarSyncModalProps> = ({
  isOpen,
  onClose,
  onUseManual,
}) => {
  const [selectedDate, setSelectedDate] = useState('2026-11-20');
  const [syncNotice, setSyncNotice] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  if (!isOpen) return null;

  const handleSyncAttempt = async () => {
    setIsChecking(true);
    setSyncNotice(null);
    try {
      const res = await fetch('/api/briefings/calendar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date: selectedDate }),
      });
      const text = await res.text();
      if (text.includes('unavailable')) {
        setSyncNotice(
          'Google Calendar MCP is currently unconfigured in this environment. Please use the primary Manual Input form for instant meeting preparation.'
        );
      }
    } catch {
      setSyncNotice(
        'Calendar service unreachable. Please proceed with Manual Input.'
      );
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 no-print">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-xl overflow-hidden p-0 border border-[#EAE4D8]">
        {/* Header */}
        <div className="px-4 sm:px-6 py-3.5 sm:py-4 border-b border-[#EAE4D8] flex items-center justify-between bg-[#FAF8F5]">
          <div className="flex items-center space-x-2">
            <Calendar className="h-4 w-4 sm:h-5 sm:w-5 text-[#2E5A44] shrink-0" />
            <h3 className="text-sm font-bold text-[#18181B]">Calendar Integration</h3>
          </div>
          <button
            onClick={onClose}
            className="text-[#71717A] hover:text-[#18181B] p-1.5 rounded-lg transition-colors"
            aria-label="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-4 sm:p-6 space-y-3.5 sm:space-y-4">
          <p className="text-xs text-[#52525B] leading-relaxed">
            Connect your calendar to automatically ingest upcoming scheduled meetings, attendee metadata, and agendas.
          </p>

          <div className="space-y-1.5">
            <label className="block text-[11px] font-bold text-[#18181B] uppercase tracking-wider">
              Target Meeting Date
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full min-h-[42px] bg-[#FAF8F5] focus:bg-white text-xs text-[#18181B] px-3.5 py-2.5 rounded-xl border border-[#EAE4D8] focus:border-[#2E5A44] focus:outline-none focus:ring-2 focus:ring-[#2E5A44]/15 transition-all"
            />
          </div>

          <button
            onClick={handleSyncAttempt}
            disabled={isChecking}
            className="w-full min-h-[44px] tavily-btn-dark py-3 sm:py-2.5 text-xs font-semibold flex items-center justify-center space-x-2 disabled:opacity-50 rounded-xl"
          >
            {isChecking ? (
              <div className="h-3.5 w-3.5 rounded-full border-2 border-white border-t-transparent animate-spin shrink-0" />
            ) : (
              <>
                <span>Check Calendar Connection</span>
                <ArrowRight className="h-3.5 w-3.5 shrink-0" />
              </>
            )}
          </button>

          {syncNotice && (
            <div className="p-3 sm:p-3.5 rounded-xl bg-[#FFF8F0] border border-[#FED7AA] text-xs text-[#9A3412] flex items-start space-x-2.5">
              <AlertCircle className="h-4 w-4 text-[#EA580C] shrink-0 mt-0.5" />
              <div className="flex-1 space-y-2">
                <p className="leading-snug">{syncNotice}</p>
                <button
                  type="button"
                  onClick={onUseManual}
                  className="font-bold text-[#7C2D12] hover:underline flex items-center gap-1 text-xs"
                >
                  <ArrowLeft className="h-3 w-3 shrink-0" />
                  <span>Switch to Manual Input Form</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 sm:px-6 py-3 bg-[#FAF8F5] border-t border-[#EAE4D8] flex items-center justify-between text-xs">
          <span className="text-[#8C8C94] text-[11px]">Primary: Manual Input</span>
          <button
            type="button"
            onClick={onClose}
            className="text-[#52525B] hover:text-[#18181B] font-semibold text-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
