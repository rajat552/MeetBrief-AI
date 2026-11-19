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
        className="px-3 py-1.5 rounded-xl bg-white border border-[#EAE4D8] hover:bg-[#FAF8F5] text-[#18181B] text-xs font-semibold shadow-2xs transition-all flex items-center space-x-1.5"
        title="Copy raw formatted Markdown"
      >
        {copied ? (
          <>
            <Check className="h-3.5 w-3.5 text-[#16A34A]" />
            <span className="text-[#16A34A]">Copied!</span>
          </>
        ) : (
          <>
            <Copy className="h-3.5 w-3.5 text-[#71717A]" />
            <span>Copy Markdown</span>
          </>
        )}
      </button>

      <button
        onClick={handlePrint}
        className="px-3 py-1.5 rounded-xl bg-white border border-[#EAE4D8] hover:bg-[#FAF8F5] text-[#18181B] text-xs font-semibold shadow-2xs transition-all flex items-center space-x-1.5"
        title="Print or export as clean PDF"
      >
        <Printer className="h-3.5 w-3.5 text-[#71717A]" />
        <span>Print / PDF</span>
      </button>
    </div>
  );
};
