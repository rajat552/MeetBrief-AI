import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { ManualInputForm } from './components/ManualInputForm';
import { ExecutionTimeline } from './components/ExecutionTimeline';
import { ExecutiveBriefingView } from './components/ExecutiveBriefingView';
import { CalendarSyncModal } from './components/CalendarSyncModal';
import {
  ManualMeetingRequest,
  OnePageBriefing,
  GatewayStatusEvent,
  SourceDiscoveredEvent,
  ClaimsVerifiedEvent,
} from './types/briefing';
import { AlertTriangle } from 'lucide-react';

export const App: React.FC = () => {
  const [gatewayStatus, setGatewayStatus] = useState<GatewayStatusEvent | null>(null);
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState<string>('query_planning');
  const [stageDescription, setStageDescription] = useState<string>('Ready to prepare briefing.');
  const [sources, setSources] = useState<SourceDiscoveredEvent[]>([]);
  const [claimsStats, setClaimsStats] = useState<ClaimsVerifiedEvent | null>(null);
  const [streamingMarkdown, setStreamingMarkdown] = useState<string>('');
  const [briefing, setBriefing] = useState<OnePageBriefing | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState<boolean>(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Initial gateway health check
  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => {
        setGatewayStatus({
          mode: data.mode === 'bifrost_gateway' ? 'bifrost_gateway' : 'fallback_direct',
          endpoint: data.endpoint,
          primary_model: data.primary_model,
          fallback_model: data.fallback_model,
          virtual_key_active: data.virtual_key_active,
          reason: data.details,
        });
      })
      .catch(() => {
        setGatewayStatus({
          mode: 'fallback_direct',
          endpoint: 'Local direct',
          primary_model: 'Direct Fallback',
          fallback_model: 'Direct Fallback',
          virtual_key_active: false,
          reason: 'Health check probe timed out',
        });
      });
  }, []);

  const handleStartBriefing = async (request: ManualMeetingRequest) => {
    // Abort any prior request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsLoading(true);
    setIsComplete(false);
    setError(null);
    setStreamingMarkdown('');
    setBriefing(null);
    setSources([]);
    setClaimsStats(null);
    setCurrentStage('query_planning');
    setStageDescription('Calculating rolling 30-day temporal window relative to meeting...');

    try {
      const response = await fetch('/api/briefings/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported by browser.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          if (!part.trim()) continue;

          let eventType = 'message';
          let eventData = '';

          const lines = part.split('\n');
          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.substring(7).trim();
            } else if (line.startsWith('data: ')) {
              eventData = line.substring(6);
            }
          }

          if (!eventData) continue;

          try {
            switch (eventType) {
              case 'gateway_status': {
                const parsed = JSON.parse(eventData);
                setGatewayStatus(parsed);
                break;
              }
              case 'stage_update': {
                const parsed = JSON.parse(eventData);
                setCurrentStage(parsed.stage);
                setStageDescription(parsed.description);
                break;
              }
              case 'tool_status': {
                const parsed = JSON.parse(eventData);
                setStageDescription(`${parsed.tool}: ${parsed.status} (${parsed.branch || 'all branches'})`);
                break;
              }
              case 'source_discovered': {
                const parsed: SourceDiscoveredEvent = JSON.parse(eventData);
                setSources((prev) => [...prev, parsed]);
                break;
              }
              case 'claims_verified': {
                const parsed: ClaimsVerifiedEvent = JSON.parse(eventData);
                setClaimsStats(parsed);
                break;
              }
              case 'streaming': {
                const token = JSON.parse(eventData);
                setStreamingMarkdown((prev) => prev + token);
                break;
              }
              case 'complete': {
                const parsedBriefing: OnePageBriefing = JSON.parse(eventData);
                setBriefing(parsedBriefing);
                setIsComplete(true);
                setCurrentStage('complete');
                setStageDescription('Executive briefing successfully generated and grounded.');
                break;
              }
              case 'error': {
                const parsed = JSON.parse(eventData);
                setError(parsed.message || 'Execution error encountered.');
                break;
              }
              default:
                break;
            }
          } catch (e) {
            console.error('Failed to parse SSE payload:', eventType, eventData, e);
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        setStageDescription('Briefing generation cancelled.');
      } else {
        setError(err.message || 'Failed to generate briefing.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header gatewayStatus={gatewayStatus} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Notification */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 flex items-start space-x-3 no-print">
            <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-semibold text-sm">Execution Interrupted</h4>
              <p className="text-xs text-red-700 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Primary Manual Form */}
        <ManualInputForm
          onSubmit={handleStartBriefing}
          isLoading={isLoading}
          onOpenCalendar={() => setIsCalendarOpen(true)}
        />

        {/* Execution Timeline (visible when running or completed) */}
        {(isLoading || isComplete || sources.length > 0) && (
          <div className="mt-6">
            <ExecutionTimeline
              currentStage={currentStage}
              stageDescription={stageDescription}
              sources={sources}
              claimsStats={claimsStats}
              isComplete={isComplete}
            />
          </div>
        )}

        {/* Executive Briefing One-Page View */}
        <ExecutiveBriefingView
          briefing={briefing}
          streamingMarkdown={streamingMarkdown}
        />
      </main>

      {/* Calendar Fallback Modal */}
      <CalendarSyncModal
        isOpen={isCalendarOpen}
        onClose={() => setIsCalendarOpen(false)}
        onUseManual={() => setIsCalendarOpen(false)}
      />

      {/* Footer */}
      <footer className="w-full bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500 no-print mt-12">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>MeetBrief AI &copy; 2026 &bull; Autonomous Meeting Intelligence</span>
          <span className="text-slate-400">
            Maxim Bifrost AI Gateway &bull; Tavily Search &bull; Deterministic Evidence Grounding
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;
