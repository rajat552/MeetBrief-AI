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
        className="px-3 py-1.5 rounded-xl bg-theme-glass border border-theme-primary/30 hover:border-theme-primary hover:bg-[rgba(255,240,225,0.1)] text-theme-text text-xs font-medium shadow-sm transition-all flex items-center space-x-1.5 backdrop-blur-sm"
        title="Copy raw formatted Markdown"
      >
        {copied ? (
          <>
            <Check className="h-3.5 w-3.5 text-theme-success" />
            <span className="text-theme-success">Copied!</span>
          </>
        ) : (
          <>
            <Copy className="h-3.5 w-3.5 text-theme-muted" />
            <span>Copy Markdown</span>
          </>
        )}
      </button>

      <button
        onClick={handlePrint}
        className="px-3 py-1.5 rounded-xl bg-theme-glass border border-theme-primary/30 hover:border-theme-primary hover:bg-[rgba(255,240,225,0.1)] text-theme-text text-xs font-medium shadow-sm transition-all flex items-center space-x-1.5 backdrop-blur-sm"
        title="Print or export as clean PDF"
      >
        <Printer className="h-3.5 w-3.5 text-theme-muted" />
        <span>Print / PDF</span>
      </button>
    </div>
  );
};
