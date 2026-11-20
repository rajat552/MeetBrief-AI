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
import {
  AlertTriangle,
  User,
  Globe,
  FileText,
  ShieldCheck,
  Clock,
  CheckCircle2,
} from 'lucide-react';

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
          mode: (data.gateway?.mode || data.mode) as
            | 'bifrost_gateway'
            | 'direct_provider_fallback'
            | 'deterministic_fallback',
          endpoint: data.gateway?.endpoint || data.endpoint,
          primary_model: data.gateway?.primary_model || data.primary_model,
          fallback_model: data.gateway?.fallback_model || data.fallback_model,
          virtual_key_active: data.gateway?.virtual_key_active ?? data.virtual_key_active,
          reason: data.gateway?.reason || data.details || data.reason,
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
    <div className="min-h-screen bg-[#FAF8F5] text-[#18181B] flex flex-col font-sans selection:bg-[#2E5A44] selection:text-white">
      {/* Top Header */}
      <Header gatewayStatus={gatewayStatus} />

      {/* Main Content Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-3 sm:px-6 lg:px-8 py-5 sm:py-8 space-y-6 sm:space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-3 sm:space-y-4 max-w-3xl mx-auto pt-1 sm:pt-2 pb-1 sm:pb-2">
          {/* Hero Headline */}
          <h1 className="text-2xl xs:text-3xl sm:text-4xl md:text-5xl font-extrabold text-[#18181B] tracking-tight leading-tight">
            Enter Every Meeting{' '}
            <span className="bg-gradient-to-r from-[#2E5A44] to-[#4E876F] bg-clip-text text-transparent">
              Better Informed
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-xs sm:text-sm md:text-base text-[#71717A] max-w-2xl mx-auto leading-relaxed px-2">
            High-conviction executive dossiers assembled in under 2 minutes. Grounded by Tavily Search and routed via Maxim Bifrost.
          </p>

          {/* 3 Step Feature Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 max-w-4xl mx-auto mt-4 sm:mt-6 text-left">
            <div className="bg-white rounded-2xl border border-[#EAE4D8] p-3.5 sm:p-4 flex items-start gap-3 sm:gap-3.5 shadow-2xs hover:border-[#D5E5DA] transition-colors">
              <div className="h-8 w-8 sm:h-9 sm:w-9 rounded-xl bg-[#EAF2EC] border border-[#D5E5DA] flex items-center justify-center shrink-0 text-[#2E5A44]">
                <User className="h-4 w-4" />
              </div>
              <div>
                <h4 className="text-[11px] sm:text-xs font-bold text-[#18181B] uppercase tracking-wider">1. Meeting Context</h4>
                <p className="text-xs text-[#71717A] mt-0.5 sm:mt-1 leading-relaxed">Input target company, attendee name, and scheduled datetime.</p>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-[#EAE4D8] p-3.5 sm:p-4 flex items-start gap-3 sm:gap-3.5 shadow-2xs hover:border-[#D5E5DA] transition-colors">
              <div className="h-8 w-8 sm:h-9 sm:w-9 rounded-xl bg-[#EAF2EC] border border-[#D5E5DA] flex items-center justify-center shrink-0 text-[#2E5A44]">
                <Globe className="h-4 w-4" />
              </div>
              <div>
                <h4 className="text-[11px] sm:text-xs font-bold text-[#18181B] uppercase tracking-wider">2. 5-Branch Research</h4>
                <p className="text-xs text-[#71717A] mt-0.5 sm:mt-1 leading-relaxed">Concurrent crawl: news, launches, hiring & background strictly bounded to 30 days.</p>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-[#EAE4D8] p-3.5 sm:p-4 flex items-start gap-3 sm:gap-3.5 shadow-2xs hover:border-[#D5E5DA] transition-colors sm:col-span-2 lg:col-span-1">
              <div className="h-8 w-8 sm:h-9 sm:w-9 rounded-xl bg-[#EAF2EC] border border-[#D5E5DA] flex items-center justify-center shrink-0 text-[#2E5A44]">
                <FileText className="h-4 w-4" />
              </div>
              <div>
                <h4 className="text-[11px] sm:text-xs font-bold text-[#18181B] uppercase tracking-wider">3. Executive Dossier</h4>
                <p className="text-xs text-[#71717A] mt-0.5 sm:mt-1 leading-relaxed">Scannable one-page briefing (&lt; 600 words) with grounded citations.</p>
              </div>
            </div>
          </div>

          {/* Real README Facts Trust Strip */}
          <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-6 text-xs text-[#71717A] mt-5 sm:mt-6 pt-3.5 sm:pt-4 border-t border-[#EAE4D8] max-w-3xl mx-auto px-2">
            <div className="flex items-center gap-1.5 font-medium">
              <ShieldCheck className="h-4 w-4 text-[#2E5A44] shrink-0" />
              <span>65 Verified Tests (100% Pass)</span>
            </div>
            <div className="flex items-center gap-1.5 font-medium">
              <Clock className="h-4 w-4 text-[#2E5A44] shrink-0" />
              <span>Strict Rolling 30-Day Window</span>
            </div>
            <div className="flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="h-4 w-4 text-[#2E5A44] shrink-0" />
              <span>&lt; 600 Words in &lt; 2 Minutes</span>
            </div>
          </div>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="p-4 rounded-2xl bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] flex items-start space-x-3 no-print shadow-2xs max-w-4xl mx-auto">
            <AlertTriangle className="h-5 w-5 text-[#DC2626] flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-semibold text-sm text-[#991B1B]">Execution Interrupted</h4>
              <p className="text-xs text-[#B91C1C] mt-0.5">{error}</p>
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
          <div className="max-w-4xl mx-auto">
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

      {/* Minimalist Professional Footer */}
      <footer className="w-full bg-[#FAF8F5] border-t border-[#EAE4D8] py-6 sm:py-8 text-xs text-[#71717A] no-print mt-8 sm:mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-3 sm:gap-4 text-center md:text-left">
          {/* Left: Operational status indicator */}
          <div className="flex flex-wrap items-center justify-center md:justify-start gap-1.5 sm:gap-2">
            <span className="h-2 w-2 rounded-full bg-[#16A34A] animate-pulse shrink-0" />
            <span className="font-semibold text-[#18181B]">All systems operational</span>
            <span className="text-[#A1A1AA]">•</span>
            <span>Preceding 30-Day Bounded Web Signals</span>
          </div>

          {/* Right: Copyright & links */}
          <div className="flex flex-wrap items-center justify-center gap-x-4 sm:gap-x-5 gap-y-1 text-[#71717A]">
            <span>MeetBrief AI &copy; 2026</span>
            <a
              href="https://tavily.com"
              target="_blank"
              rel="noreferrer"
              className="hover:text-[#18181B] transition-colors"
            >
              Tavily Search
            </a>
            <a
              href="https://bifrost.maximhq.com"
              target="_blank"
              rel="noreferrer"
              className="hover:text-[#18181B] transition-colors"
            >
              Maxim Bifrost AI Gateway
            </a>
            <a
              href="https://github.com/rajat552/MeetBrief-AI"
              target="_blank"
              rel="noreferrer"
              className="hover:text-[#18181B] transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
