import React from 'react';

interface QuizCardProps {
  onClick: () => void;
  icon?: React.ReactNode;
  title: string;
  subtitle?: string;
  recommended?: boolean;
  details?: Array<{ label: string; value: string }>;
  className?: string;
  selected?: boolean;
}

export function QuizCard({
  onClick,
  icon,
  title,
  subtitle,
  recommended,
  details,
  className = '',
  selected = false,
}: QuizCardProps) {
  return (
    <button
      onClick={onClick}
      className={`
        relative overflow-hidden bg-[#1B2D44] text-white rounded-2xl p-6
        text-center transition-all duration-150
        hover:bg-[#253f5e] active:scale-[0.97]
        flex flex-col items-center gap-3
        ${selected ? 'ring-2 ring-[#4B5EFF] ring-offset-2' : ''}
        ${className}
      `}
    >
      {recommended && (
        <div className="absolute top-0 right-0 w-28 h-28 overflow-hidden rounded-tr-2xl">
          <div
            className="absolute bg-[#D946EF] text-white font-bold py-1"
            style={{
              top: '18px',
              right: '-28px',
              width: '120px',
              fontSize: '10px',
              textAlign: 'center',
              transform: 'rotate(45deg)',
              letterSpacing: '0.05em',
            }}
          >
            Recommended
          </div>
        </div>
      )}

      {icon && (
        <div className="mb-1 flex items-center justify-center">{icon}</div>
      )}

      <h3 className="font-bold text-base leading-tight uppercase tracking-wide">{title}</h3>

      {subtitle && (
        <p className="text-gray-300 text-sm font-normal leading-snug">{subtitle}</p>
      )}

      {details && details.length > 0 && (
        <div className="w-full mt-3 pt-3 border-t border-white/20 space-y-1.5 text-left">
          {details.map((d) => (
            <div key={d.label} className="flex justify-between text-sm gap-2">
              <span className="text-gray-300 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full border border-gray-400 inline-block" />
                {d.label}
              </span>
              <span className="font-semibold text-white">{d.value}</span>
            </div>
          ))}
        </div>
      )}
    </button>
  );
}
