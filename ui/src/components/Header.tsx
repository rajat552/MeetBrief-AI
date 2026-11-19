import React from 'react';
import { ShieldCheck, Zap, Sparkles, Cpu, ExternalLink } from 'lucide-react';
import { GatewayStatusEvent } from '../types/briefing';

interface HeaderProps {
  gatewayStatus: GatewayStatusEvent | null;
}

export const Header: React.FC<HeaderProps> = ({ gatewayStatus }) => {
  return (
    <header className="w-full bg-[rgba(8,11,17,0.85)] backdrop-blur-xl border-b border-theme-glass-border sticky top-0 z-40 shadow-sm no-print">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-2xl bg-brand-gradient flex items-center justify-center text-theme-btn-text shadow-sm">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-theme-primary tracking-tight">MeetBrief AI</span>
              <span className="text-xs bg-theme-glass text-theme-accent-2 font-medium px-2.5 py-0.5 rounded-full border border-theme-glass-border backdrop-blur-md">
                Autonomous Meeting Intelligence
              </span>
            </div>
            <p className="text-xs text-theme-muted hidden sm:block">
              Geek Room Global AI Hackathon 2026 — Problem Statement 05
            </p>
          </div>
        </div>

        {/* Inference Gateway Status Badge */}
        <div className="flex items-center space-x-4">
          {gatewayStatus ? (
            gatewayStatus.mode === 'bifrost_gateway' ? (
              <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-theme-glass text-theme-success border border-theme-glass-border text-xs font-medium backdrop-blur-sm" title={gatewayStatus.reason || "Bifrost Gateway Active"}>
                <ShieldCheck className="h-3.5 w-3.5 text-theme-success" />
                <span>Bifrost AI Gateway (Active)</span>
              </div>
            ) : gatewayStatus.mode === 'direct_provider_fallback' ? (
              <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-theme-glass text-theme-accent border border-theme-glass-border text-xs font-medium backdrop-blur-sm" title={gatewayStatus.reason || "Direct Provider Active"}>
                <Zap className="h-3.5 w-3.5 text-theme-accent" />
                <span>Inference: Direct Provider (Active)</span>
              </div>
            ) : (
              <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-theme-glass text-theme-muted border border-theme-glass-border text-xs font-medium backdrop-blur-sm" title={gatewayStatus.reason || "Deterministic Rules Fallback"}>
                <Cpu className="h-3.5 w-3.5 text-theme-muted" />
                <span>Inference: Deterministic Rules (Fallback)</span>
              </div>
            )
          ) : (
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-theme-glass text-theme-muted border border-theme-glass-border text-xs font-medium backdrop-blur-sm">
              <Cpu className="h-3.5 w-3.5 text-theme-muted" />
              <span>Gateway Checking...</span>
            </div>
          )}

          <a
            href="https://github.com/rajat552/MeetBrief-AI"
            target="_blank"
            rel="noreferrer"
            className="text-xs text-theme-muted hover:text-theme-primary font-medium flex items-center space-x-1 transition-colors"
          >
            <span>GitHub</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </header>
  );
};
