import React from 'react';
import { Zap, Sparkles, Cpu, ExternalLink } from 'lucide-react';
import { GatewayStatusEvent } from '../types/briefing';

interface HeaderProps {
  gatewayStatus: GatewayStatusEvent | null;
}

export const Header: React.FC<HeaderProps> = ({ gatewayStatus }) => {
  return (
    <header className="w-full bg-[#FFFFFF]/95 backdrop-blur-md border-b border-[#EAE4D8] sticky top-0 z-40 shadow-xs no-print">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-[#2E5A44] to-[#4E876F] flex items-center justify-center text-white shadow-sm shadow-[#2E5A44]/20">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-[#18181B] tracking-tight">MeetBrief AI</span>
              <span className="text-xs bg-[#EAF2EC] text-[#2E5A44] font-semibold px-2.5 py-0.5 rounded-full border border-[#D5E5DA]">
                Autonomous Meeting Intelligence
              </span>
            </div>
            <p className="text-xs text-[#71717A] hidden sm:block">
              Geek Room Global AI Hackathon 2026 — Problem Statement 05
            </p>
          </div>
        </div>

        {/* Inference Gateway Status Badge */}
        <div className="flex items-center space-x-3 sm:space-x-4">
          {gatewayStatus ? (
            gatewayStatus.mode === 'bifrost_gateway' ? (
              <div
                className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#EAF2EC] text-[#2E5A44] border border-[#D5E5DA] text-xs font-semibold shadow-2xs"
                title={gatewayStatus.reason || "Bifrost Gateway Active"}
              >
                <span className="h-2 w-2 rounded-full bg-[#16A34A] animate-pulse" />
                <span className="hidden sm:inline">Bifrost AI Gateway (Active)</span>
                <span className="sm:hidden">Bifrost Active</span>
              </div>
            ) : gatewayStatus.mode === 'direct_provider_fallback' ? (
              <div
                className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#EFF6FF] text-[#1D4ED8] border border-[#DBEAFE] text-xs font-semibold shadow-2xs"
                title={gatewayStatus.reason || "Direct Provider Active"}
              >
                <Zap className="h-3.5 w-3.5 text-[#2563EB]" />
                <span className="hidden sm:inline">Inference: Direct Provider (Active)</span>
                <span className="sm:hidden">Direct LLM</span>
              </div>
            ) : (
              <div
                className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#F4F0E8] text-[#71717A] border border-[#EAE4D8] text-xs font-medium"
                title={gatewayStatus.reason || "Deterministic Rules Fallback"}
              >
                <Cpu className="h-3.5 w-3.5 text-[#71717A]" />
                <span className="hidden sm:inline">Inference: Deterministic Rules (Fallback)</span>
                <span className="sm:hidden">Rules Fallback</span>
              </div>
            )
          ) : (
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#F4F0E8] text-[#71717A] border border-[#EAE4D8] text-xs font-medium">
              <Cpu className="h-3.5 w-3.5 text-[#A1A1AA] animate-spin" />
              <span>Gateway Checking...</span>
            </div>
          )}

          <a
            href="https://github.com/rajat552/MeetBrief-AI"
            target="_blank"
            rel="noreferrer"
            className="text-xs text-[#52525B] hover:text-[#18181B] font-medium flex items-center space-x-1 transition-colors"
          >
            <span>GitHub</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </header>
  );
};
