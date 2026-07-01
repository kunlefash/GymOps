import React from 'react';

interface AjayBubbleProps {
  message: React.ReactNode;
  className?: string;
}

export function AjayBubble({ message, className = '' }: AjayBubbleProps) {
  return (
    <div className={`flex items-start gap-4 px-6 pb-6 pt-4 max-w-2xl mx-auto w-full ${className}`}>
      <div className="flex-shrink-0 flex flex-col items-center gap-1">
        <div className="w-14 h-14 rounded-full bg-[#1B2D44] flex items-center justify-center text-white text-2xl border-2 border-white shadow-md select-none">
          <span role="img" aria-label="Ajay">🧑</span>
        </div>
        <span className="text-[10px] text-gray-400 font-medium tracking-wide">Ajay</span>
      </div>

      <div className="relative bg-white rounded-2xl shadow-sm border border-gray-100 px-5 py-4 flex-1 mt-1">
        {/* Speech bubble tail */}
        <div
          className="absolute left-[-9px] top-4 w-4 h-4 bg-white border-l border-t border-gray-100"
          style={{ transform: 'rotate(-45deg)', borderRadius: '2px' }}
        />
        <p className="text-gray-900 font-medium text-[15px] leading-relaxed">{message}</p>
      </div>
    </div>
  );
}
