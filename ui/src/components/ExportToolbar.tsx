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
    <div className="flex items-center space-x-1.5 sm:space-x-2 no-print shrink-0">
      <button
        onClick={handleCopy}
        className="px-2.5 sm:px-3 py-1.5 min-h-[36px] rounded-xl bg-white border border-[#EAE4D8] hover:bg-[#FAF8F5] text-[#18181B] text-xs font-semibold shadow-2xs transition-all flex items-center space-x-1.5 shrink-0"
        title="Copy raw formatted Markdown"
      >
        {copied ? (
          <>
            <Check className="h-3.5 w-3.5 text-[#16A34A] shrink-0" />
            <span className="text-[#16A34A]">Copied!</span>
          </>
        ) : (
          <>
            <Copy className="h-3.5 w-3.5 text-[#71717A] shrink-0" />
            <span className="hidden xs:inline">Copy Markdown</span>
            <span className="xs:hidden">Copy</span>
          </>
        )}
      </button>

      <button
        onClick={handlePrint}
        className="px-2.5 sm:px-3 py-1.5 min-h-[36px] rounded-xl bg-white border border-[#EAE4D8] hover:bg-[#FAF8F5] text-[#18181B] text-xs font-semibold shadow-2xs transition-all flex items-center space-x-1.5 shrink-0"
        title="Print or export as clean PDF"
      >
        <Printer className="h-3.5 w-3.5 text-[#71717A] shrink-0" />
        <span className="hidden xs:inline">Print / PDF</span>
        <span className="xs:hidden">Print</span>
      </button>
    </div>
  );
};
