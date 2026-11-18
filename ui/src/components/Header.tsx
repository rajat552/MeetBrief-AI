import React from 'react';
import { ShieldCheck, AlertCircle, Sparkles, Cpu, ExternalLink } from 'lucide-react';
import { GatewayStatusEvent } from '../types/briefing';

interface HeaderProps {
  gatewayStatus: GatewayStatusEvent | null;
}

export const Header: React.FC<HeaderProps> = ({ gatewayStatus }) => {
  return (
    <header className="w-full bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm no-print">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-800 flex items-center justify-center text-white shadow-md shadow-indigo-200">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-slate-900 tracking-tight">MeetBrief AI</span>
              <span className="text-xs bg-indigo-50 text-indigo-700 font-medium px-2 py-0.5 rounded-full border border-indigo-200">
                Autonomous Meeting Intelligence
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">
              Geek Room Global AI Hackathon 2026 — Problem Statement 05
            </p>
          </div>
        </div>

        {/* Inference Gateway Status Badge */}
        <div className="flex items-center space-x-4">
          {gatewayStatus ? (
            gatewayStatus.mode === 'bifrost_gateway' ? (
              <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-medium">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                <span>Bifrost AI Gateway (:8080)</span>
              </div>
            ) : (
              <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200 text-xs font-medium" title={gatewayStatus.reason || "Gateway Offline"}>
                <AlertCircle className="h-3.5 w-3.5 text-amber-600" />
                <span>Inference: Direct Provider Fallback</span>
              </div>
            )
          ) : (
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-600 border border-slate-200 text-xs font-medium">
              <Cpu className="h-3.5 w-3.5 text-slate-500" />
              <span>Gateway Checking...</span>
            </div>
          )}

          <a
            href="https://github.com/rajat552/MeetBrief-AI"
            target="_blank"
            rel="noreferrer"
            className="text-xs text-slate-600 hover:text-indigo-600 font-medium flex items-center space-x-1 transition-colors"
          >
            <span>GitHub</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </header>
  );
};
