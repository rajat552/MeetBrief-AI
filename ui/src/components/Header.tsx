import React from 'react';
import { Zap, Briefcase, Cpu, ExternalLink } from 'lucide-react';
import { GatewayStatusEvent } from '../types/briefing';

interface HeaderProps {
  gatewayStatus: GatewayStatusEvent | null;
}

export const Header: React.FC<HeaderProps> = ({ gatewayStatus }) => {
  return (
    <header className="w-full bg-[#FFFFFF]/95 backdrop-blur-md border-b border-[#EAE4D8] sticky top-0 z-40 shadow-xs no-print">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-2">
        {/* Brand Logo & Name */}
        <div className="flex items-center space-x-2.5 sm:space-x-3 min-w-0">
          <div className="h-9 w-9 sm:h-10 sm:w-10 rounded-xl bg-gradient-to-tr from-[#2E5A44] to-[#4E876F] flex items-center justify-center text-white shadow-sm shadow-[#2E5A44]/20 shrink-0">
            <Briefcase className="h-4 w-4 sm:h-5 sm:w-5 stroke-[2.2]" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-base sm:text-lg text-[#18181B] tracking-tight whitespace-nowrap">
                MeetBrief AI
              </span>
              <span className="hidden sm:inline-flex text-[11px] bg-[#EAF2EC] text-[#2E5A44] font-semibold px-2 py-0.5 rounded-full border border-[#D5E5DA] whitespace-nowrap">
                Autonomous Meeting Intelligence
              </span>
            </div>
            <p className="text-[11px] text-[#71717A] hidden lg:block whitespace-nowrap">
              Geek Room Global AI Hackathon 2026 — Problem Statement 05
            </p>
          </div>
        </div>

        {/* Inference Gateway Status Badge & Links */}
        <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
          {gatewayStatus ? (
            gatewayStatus.mode === 'bifrost_gateway' ? (
              <div
                className="flex items-center space-x-1.5 px-2.5 sm:px-3 py-1 rounded-full bg-[#EAF2EC] text-[#2E5A44] border border-[#D5E5DA] text-[11px] sm:text-xs font-semibold shadow-2xs whitespace-nowrap"
                title={gatewayStatus.reason || "Bifrost Gateway Active"}
              >
                <span className="h-2 w-2 rounded-full bg-[#16A34A] animate-pulse shrink-0" />
                <span className="hidden sm:inline">Bifrost AI Gateway (Active)</span>
                <span className="sm:hidden">Bifrost</span>
              </div>
            ) : gatewayStatus.mode === 'direct_provider_fallback' ? (
              <div
                className="flex items-center space-x-1.5 px-2.5 sm:px-3 py-1 rounded-full bg-[#EFF6FF] text-[#1D4ED8] border border-[#DBEAFE] text-[11px] sm:text-xs font-semibold shadow-2xs whitespace-nowrap"
                title={gatewayStatus.reason || "Direct Provider Active"}
              >
                <Zap className="h-3.5 w-3.5 text-[#2563EB] shrink-0" />
                <span className="hidden sm:inline">Direct Provider (Active)</span>
                <span className="sm:hidden">Direct LLM</span>
              </div>
            ) : (
              <div
                className="flex items-center space-x-1.5 px-2.5 sm:px-3 py-1 rounded-full bg-[#F4F0E8] text-[#71717A] border border-[#EAE4D8] text-[11px] sm:text-xs font-medium whitespace-nowrap"
                title={gatewayStatus.reason || "Deterministic Rules Fallback"}
              >
                <Cpu className="h-3.5 w-3.5 text-[#71717A] shrink-0" />
                <span className="hidden sm:inline">Rules Fallback</span>
                <span className="sm:hidden">Rules</span>
              </div>
            )
          ) : (
            <div className="flex items-center space-x-1.5 px-2.5 sm:px-3 py-1 rounded-full bg-[#F4F0E8] text-[#71717A] border border-[#EAE4D8] text-[11px] sm:text-xs font-medium whitespace-nowrap">
              <Cpu className="h-3 w-3 text-[#A1A1AA] animate-spin shrink-0" />
              <span className="hidden xs:inline">Checking Gateway...</span>
              <span className="xs:hidden">Checking...</span>
            </div>
          )}

          <a
            href="https://github.com/rajat552/MeetBrief-AI"
            target="_blank"
            rel="noreferrer"
            aria-label="GitHub Repository"
            className="text-xs text-[#52525B] hover:text-[#18181B] font-medium flex items-center space-x-1 transition-colors px-2 py-1.5 rounded-lg hover:bg-[#F4F0E8]"
          >
            <span className="hidden xs:inline">GitHub</span>
            <ExternalLink className="h-3.5 w-3.5 shrink-0" />
          </a>
        </div>
      </div>
    </header>
  );
};
