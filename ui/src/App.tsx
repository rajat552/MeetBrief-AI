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
import { AlertTriangle, Sparkles, User, Globe, FileText, ShieldCheck, Clock, CheckCircle2 } from 'lucide-react';

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
          mode: data.mode as 'bifrost_gateway' | 'direct_provider_fallback' | 'deterministic_fallback',
          endpoint: data.endpoint,
          primary_model: data.primary_model,
          fallback_model: data.fallback_model,
          virtual_key_active: data.virtual_key_active,
          reason: data.details || data.reason,
        });
      })
      .catch(() => {
        setGatewayStatus({
          mode: 'deterministic_fallback',
          endpoint: 'Local deterministic',
          primary_model: 'Deterministic Rules',
          fallback_model: 'Deterministic Rules',
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
    <div className="min-h-screen glow-background text-theme-text flex flex-col font-sans">
      <Header gatewayStatus={gatewayStatus} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="text-center mb-8 no-print">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-theme-glass border border-theme-glass-border text-xs font-medium text-theme-accent mb-3 backdrop-blur-md">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Autonomous Pre-Meeting Intelligence</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-theme-primary tracking-tight">
            Enter Every Meeting <span className="bg-brand-gradient bg-clip-text text-transparent">Better Informed</span>
          </h1>
          <p className="text-sm sm:text-base text-theme-muted max-w-2xl mx-auto mt-2">
            Transform recent web intelligence into a scannable, source-grounded executive briefing covering the preceding 30 days.
          </p>

          {/* 3-Step "How It Works" Glass Strip */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 max-w-4xl mx-auto mt-6 text-left">
            <div className="glass-card p-4 flex items-start gap-3">
              <div className="h-8 w-8 rounded-xl bg-theme-glass border border-theme-glass-border flex items-center justify-center shrink-0 text-theme-accent">
                <User className="h-4 w-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-theme-primary uppercase tracking-wider">1. Meeting Context</h4>
                <p className="text-xs text-theme-muted mt-0.5">Input target company, attendee name, and scheduled datetime.</p>
              </div>
            </div>

            <div className="glass-card p-4 flex items-start gap-3">
              <div className="h-8 w-8 rounded-xl bg-theme-glass border border-theme-glass-border flex items-center justify-center shrink-0 text-theme-accent-2">
                <Globe className="h-4 w-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-theme-primary uppercase tracking-wider">2. 5-Branch Research</h4>
                <p className="text-xs text-theme-muted mt-0.5">Concurrent crawl: news, launches, hiring & background strictly bounded to 30 days.</p>
              </div>
            </div>

            <div className="glass-card p-4 flex items-start gap-3">
              <div className="h-8 w-8 rounded-xl bg-theme-glass border border-theme-glass-border flex items-center justify-center shrink-0 text-theme-success">
                <FileText className="h-4 w-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-theme-primary uppercase tracking-wider">3. Executive Dossier</h4>
                <p className="text-xs text-theme-muted mt-0.5">Scannable one-page briefing (&lt; 600 words) with grounded citations.</p>
              </div>
            </div>
          </div>

          {/* Real README Facts Trust Strip */}
          <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 text-xs text-theme-muted mt-5 pt-3 border-t border-theme-glass-border max-w-3xl mx-auto">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-theme-success" />
              <span>44 Verified Unit &amp; Security Tests</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-theme-accent" />
              <span>Strict Rolling 30-Day Window</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-theme-accent-2" />
              <span>&lt; 600 Words in &lt; 2 Minutes</span>
            </div>
          </div>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="mb-6 p-4 glass-card border-theme-danger/50 text-theme-text flex items-start space-x-3 no-print">
            <AlertTriangle className="h-5 w-5 text-theme-danger flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-semibold text-sm text-theme-danger">Execution Interrupted</h4>
              <p className="text-xs text-theme-muted mt-0.5">{error}</p>
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
      <footer className="w-full bg-theme-glass/40 border-t border-theme-glass-border py-6 text-center text-xs text-theme-muted no-print mt-12 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>MeetBrief AI &copy; 2026 &bull; Autonomous Meeting Intelligence</span>
          <span className="text-theme-muted">
            Maxim Bifrost AI Gateway &bull; Tavily Search &bull; Deterministic Evidence Grounding
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;
