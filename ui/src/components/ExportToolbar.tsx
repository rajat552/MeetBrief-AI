import React, { useState } from 'react';
import { Copy, Check, Printer } from 'lucide-react';

interface ExportToolbarProps {
  markdownContent: string;
}

export const ExportToolbar: React.FC<ExportToolbarProps> = ({ markdownContent }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(markdownContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy markdown:', err);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="flex items-center space-x-2 no-print">
      <button
        onClick={handleCopy}
        className="px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium shadow-sm transition-colors flex items-center space-x-1.5"
        title="Copy raw formatted Markdown"
      >
        {copied ? (
          <>
            <Check className="h-3.5 w-3.5 text-emerald-600" />
            <span className="text-emerald-700">Copied!</span>
          </>
        ) : (
          <>
            <Copy className="h-3.5 w-3.5 text-slate-500" />
            <span>Copy Markdown</span>
          </>
        )}
      </button>

      <button
        onClick={handlePrint}
        className="px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium shadow-sm transition-colors flex items-center space-x-1.5"
        title="Print or export as clean PDF"
      >
        <Printer className="h-3.5 w-3.5 text-slate-500" />
        <span>Print / PDF</span>
      </button>
    </div>
  );
};
