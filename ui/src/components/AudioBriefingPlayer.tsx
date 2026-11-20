import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Headphones, Radio, Sparkles, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { OnePageBriefing, AudioBriefingResponse } from '../types/briefing';

interface AudioBriefingPlayerProps {
  briefing: OnePageBriefing;
}

export const AudioBriefingPlayer: React.FC<AudioBriefingPlayerProps> = ({ briefing }) => {
  const [audioData, setAudioData] = useState<AudioBriefingResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(90);
  const [playbackRate, setPlaybackRate] = useState<number>(1.0);
  const [showScript, setShowScript] = useState<boolean>(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<number | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Stop audio when briefing changes
  useEffect(() => {
    stopPlayback();
    setAudioData(null);
    setCurrentTime(0);
  }, [briefing.briefing_id]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopPlayback();
    };
  }, []);

  const stopPlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsPlaying(false);
  };

  const fetchAudioBriefing = async (): Promise<AudioBriefingResponse | null> => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/briefings/audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(briefing),
      });
      if (!res.ok) {
        throw new Error(`Failed to generate audio briefing (HTTP ${res.status})`);
      }
      const data: AudioBriefingResponse = await res.json();
      setAudioData(data);
      setDuration(data.duration_estimated_seconds || 90);
      return data;
    } catch (err) {
      console.warn('Audio endpoint error, using client-side fallback:', err);
      // Emergency client-side fallback
      const fallbackData: AudioBriefingResponse = {
        spoken_script: `Here is your executive briefing for ${briefing.target_company}. Meeting with ${briefing.target_attendee}. Strategic context: ${briefing.card1_executive_snapshot.slice(0, 200)}. You are fully prepared.`,
        duration_estimated_seconds: 75,
        provider: 'browser_tts_fallback',
        voice_id: 'browser-default',
        generated_at: new Date().toISOString(),
      };
      setAudioData(fallbackData);
      setDuration(75);
      return fallbackData;
    } finally {
      setIsLoading(false);
    }
  };

  const handleTogglePlay = async () => {
    if (isPlaying) {
      pausePlayback();
      return;
    }

    let currentAudio = audioData;
    if (!currentAudio) {
      currentAudio = await fetchAudioBriefing();
    }

    if (!currentAudio) return;

    // Check if Omnidimension returned audio binary/URL
    if (currentAudio.provider === 'omnidimension' && (currentAudio.audio_base64 || currentAudio.audio_url)) {
      playBinaryAudio(currentAudio);
    } else {
      // Use resilient Web Speech API synthesis
      playWebSpeech(currentAudio.spoken_script, currentAudio.duration_estimated_seconds);
    }
  };

  const playBinaryAudio = (data: AudioBriefingResponse) => {
    if (!audioRef.current) {
      const audio = new Audio(data.audio_base64 || data.audio_url);
      audio.playbackRate = playbackRate;
      audio.onended = () => {
        setIsPlaying(false);
        setCurrentTime(0);
      };
      audio.ontimeupdate = () => {
        setCurrentTime(Math.floor(audio.currentTime));
      };
      audioRef.current = audio;
    }
    audioRef.current.playbackRate = playbackRate;
    audioRef.current.play();
    setIsPlaying(true);
  };

  const playWebSpeech = (script: string, totalSec: number) => {
    if (!('speechSynthesis' in window)) {
      alert('Your browser does not support Web Speech synthesis.');
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(script);
    utterance.rate = playbackRate;
    utterance.pitch = 1.0;

    // Pick best natural English voice if available
    const voices = window.speechSynthesis.getVoices();
    const naturalVoice = voices.find(
      (v) => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Premium') || v.name.includes('Google') || v.name.includes('Samantha'))
    );
    if (naturalVoice) {
      utterance.voice = naturalVoice;
    }

    utterance.onend = () => {
      setIsPlaying(false);
      setCurrentTime(0);
      if (timerRef.current) clearInterval(timerRef.current);
    };

    utterance.onerror = () => {
      setIsPlaying(false);
      if (timerRef.current) clearInterval(timerRef.current);
    };

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
    setIsPlaying(true);

    // Simulate progress bar based on rate
    if (timerRef.current) clearInterval(timerRef.current);
    const interval = 1000 / playbackRate;
    timerRef.current = window.setInterval(() => {
      setCurrentTime((prev) => {
        if (prev >= totalSec) {
          clearInterval(timerRef.current!);
          return totalSec;
        }
        return prev + 1;
      });
    }, interval);
  };

  const pausePlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsPlaying(false);
  };

  const cycleSpeed = () => {
    const nextRate = playbackRate === 1.0 ? 1.25 : playbackRate === 1.25 ? 1.5 : 1.0;
    setPlaybackRate(nextRate);
    if (audioRef.current) {
      audioRef.current.playbackRate = nextRate;
    }
    // If Web Speech is currently playing, resume with new speed
    if (isPlaying && audioData && audioData.provider === 'browser_tts_fallback') {
      window.speechSynthesis.cancel();
      playWebSpeech(audioData.spoken_script, audioData.duration_estimated_seconds);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="w-full bg-gradient-to-r from-indigo-900 via-slate-900 to-indigo-950 rounded-2xl p-4 sm:p-5 text-white shadow-lg border border-indigo-500/20 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Left info badge */}
        <div className="flex items-center space-x-3.5">
          <div className="h-11 w-11 rounded-xl bg-indigo-600/30 border border-indigo-400/30 flex items-center justify-center text-indigo-300 shadow-inner">
            {isPlaying ? (
              <Radio className="h-5 w-5 text-indigo-400 animate-pulse" />
            ) : (
              <Headphones className="h-5 w-5 text-indigo-300" />
            )}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-sm tracking-tight text-white">
                90s Executive Audio Brief
              </span>
              {audioData?.provider === 'omnidimension' ? (
                <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                  <Sparkles className="h-2.5 w-2.5" />
                  Omnidimension Voice AI
                </span>
              ) : (
                <span className="text-[10px] bg-indigo-500/20 text-indigo-200 border border-indigo-400/30 px-2 py-0.5 rounded-full font-medium">
                  Voice Assistant Mode
                </span>
              )}
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Spoken audio briefing for commute & pre-meeting review • {briefing.target_attendee} ({briefing.target_company})
            </p>
          </div>
        </div>

        {/* Right audio controls */}
        <div className="flex items-center space-x-3 self-end sm:self-center">
          {/* Speed Toggle */}
          <button
            onClick={cycleSpeed}
            className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-indigo-200 transition-colors"
            title="Toggle playback speed"
          >
            {playbackRate}x
          </button>

          {/* Transcript view toggle */}
          <button
            onClick={() => setShowScript(!showScript)}
            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 flex items-center space-x-1 transition-colors"
            title="Read spoken transcript"
          >
            <FileText className="h-3 w-3" />
            <span className="hidden sm:inline">Script</span>
            {showScript ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </button>

          {/* Big Play / Pause Button */}
          <button
            onClick={handleTogglePlay}
            disabled={isLoading}
            className={`h-10 px-4 rounded-xl flex items-center space-x-2 font-semibold text-xs shadow-md transition-all ${
              isPlaying
                ? 'bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-amber-500/20'
                : 'bg-indigo-500 hover:bg-indigo-400 text-white shadow-indigo-500/25'
            } disabled:opacity-50`}
          >
            {isLoading ? (
              <>
                <div className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Generating...</span>
              </>
            ) : isPlaying ? (
              <>
                <Pause className="h-4 w-4 fill-current" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="h-4 w-4 fill-current ml-0.5" />
                <span>Listen Audio (90s)</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Progress scrub bar */}
      <div className="mt-3.5 pt-3 border-t border-slate-800/80 flex items-center space-x-3">
        <span className="text-[11px] font-mono text-slate-400 w-9 text-right">
          {formatTime(currentTime)}
        </span>
        <div className="flex-1 bg-slate-800 h-2 rounded-full overflow-hidden relative">
          <div
            className="bg-gradient-to-r from-indigo-500 to-indigo-400 h-full rounded-full transition-all duration-300"
            style={{ width: `${Math.min(100, (currentTime / duration) * 100)}%` }}
          />
        </div>
        <span className="text-[11px] font-mono text-slate-400 w-9">
          {formatTime(duration)}
        </span>
      </div>

      {/* Spoken Transcript Accordion */}
      {showScript && (
        <div className="mt-3.5 p-3.5 bg-slate-950/60 rounded-xl border border-indigo-500/20 text-xs text-slate-200 leading-relaxed animate-fadeIn">
          <div className="flex items-center justify-between mb-1.5 text-indigo-300 font-semibold text-[11px] uppercase tracking-wider">
            <span>🎙️ Spoken Executive Script (~{audioData?.duration_estimated_seconds || 90}s)</span>
            <span className="text-slate-400 normal-case font-normal">
              {audioData?.provider === 'omnidimension' ? 'Synthesized via Omnidimension' : 'Web Speech Synthesizer'}
            </span>
          </div>
          <p className="font-normal text-slate-300 italic">
            "{audioData?.spoken_script || 'Generating high-density spoken script from executive dossier...'}"
          </p>
        </div>
      )}
    </div>
  );
};
