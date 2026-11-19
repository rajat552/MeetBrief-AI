import React, { useState } from 'react';
import { X, Calendar, AlertCircle, ArrowLeft } from 'lucide-react';

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#080B11]/85 backdrop-blur-md p-4 no-print">
      <div className="glass-card max-w-md w-full shadow-2xl overflow-hidden p-0 border border-theme-glass-border">
        <div className="px-6 py-4 border-b border-theme-glass-border flex items-center justify-between bg-theme-glass/40">
          <div className="flex items-center space-x-2">
            <Calendar className="h-5 w-5 text-theme-accent" />
            <h3 className="text-base font-bold text-theme-primary">Calendar Integration (Optional)</h3>
          </div>
          <button
            onClick={onClose}
            className="text-theme-muted hover:text-theme-primary p-1 rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <p className="text-sm text-theme-muted">
            Select a date to query your scheduled meetings via Google Calendar MCP:
          </p>

          <div>
            <label className="block text-xs font-semibold text-theme-primary uppercase tracking-wider mb-1.5">
              Target Date
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-xl border border-theme-glass-border focus:outline-none focus:ring-2 focus:ring-theme-primary bg-transparent text-theme-text"
            />
          </div>

          {syncNotice && (
            <div className="p-3.5 rounded-xl bg-theme-glass border border-theme-glass-border flex items-start space-x-2.5 text-xs text-theme-muted">
              <AlertCircle className="h-4 w-4 text-theme-accent shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-theme-primary mb-0.5">Calendar Unavailable</p>
                <p>{syncNotice}</p>
              </div>
            </div>
          )}

          <div className="flex items-center space-x-3 pt-2">
            <button
              type="button"
              onClick={handleSyncAttempt}
              disabled={isChecking}
              className="flex-1 py-2 px-4 rounded-xl bg-brand-gradient hover:opacity-95 text-theme-btn-text font-semibold text-xs transition-all disabled:opacity-50"
            >
              {isChecking ? 'Checking MCP...' : 'Sync Calendar Date'}
            </button>
            <button
              type="button"
              onClick={() => {
                onClose();
                onUseManual();
              }}
              className="py-2 px-4 rounded-xl bg-theme-glass hover:bg-[rgba(255,240,225,0.1)] border border-theme-glass-border text-theme-text font-medium text-xs transition-colors flex items-center space-x-1 backdrop-blur-sm"
            >
              <ArrowLeft className="h-3.5 w-3.5 text-theme-muted" />
              <span>Use Manual Form</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
