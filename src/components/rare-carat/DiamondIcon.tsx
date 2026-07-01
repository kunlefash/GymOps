interface DiamondIconProps {
  size?: number;
  className?: string;
  variant?: 'default' | 'dark' | 'light';
}

export function DiamondIcon({ size = 80, className = '', variant = 'default' }: DiamondIconProps) {
  const fill = variant === 'dark' ? '#1B2D44' : '#ffffff';
  const stroke = variant === 'dark' ? '#2a4a6e' : '#c8d4e0';
  const facet = variant === 'dark' ? '#2a4a6e' : '#e0e8f0';

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 90"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Upper half (crown) */}
      <polygon
        points="50,4 94,36 6,36"
        fill={fill}
        stroke={stroke}
        strokeWidth="1.2"
        opacity="0.95"
      />
      {/* Lower half (pavilion) */}
      <polygon
        points="6,36 50,86 94,36"
        fill={fill}
        stroke={stroke}
        strokeWidth="1.2"
        opacity="0.85"
      />
      {/* Table facet (top center) */}
      <polygon
        points="50,4 70,36 30,36"
        fill={fill}
        stroke={facet}
        strokeWidth="0.8"
        opacity="0.5"
      />
      {/* Left upper facets */}
      <line x1="6" y1="36" x2="30" y2="36" stroke={facet} strokeWidth="0.6" opacity="0.7" />
      <line x1="94" y1="36" x2="70" y2="36" stroke={facet} strokeWidth="0.6" opacity="0.7" />
      {/* Pavilion facet lines */}
      <line x1="6" y1="36" x2="50" y2="86" stroke={facet} strokeWidth="0.6" opacity="0.5" />
      <line x1="94" y1="36" x2="50" y2="86" stroke={facet} strokeWidth="0.6" opacity="0.5" />
      <line x1="30" y1="36" x2="50" y2="86" stroke={facet} strokeWidth="0.5" opacity="0.4" />
      <line x1="70" y1="36" x2="50" y2="86" stroke={facet} strokeWidth="0.5" opacity="0.4" />
      {/* Crown facet lines */}
      <line x1="50" y1="4" x2="6" y2="36" stroke={facet} strokeWidth="0.6" opacity="0.5" />
      <line x1="50" y1="4" x2="94" y2="36" stroke={facet} strokeWidth="0.6" opacity="0.5" />
    </svg>
  );
}

export function OvalDiamondIcon({ size = 80, className = '', variant = 'default' }: DiamondIconProps) {
  const fill = variant === 'dark' ? '#1B2D44' : '#ffffff';
  const stroke = variant === 'dark' ? '#2a4a6e' : '#c8d4e0';
  const facet = variant === 'dark' ? '#2a4a6e' : '#dde6ef';

  return (
    <svg
      width={size}
      height={size * 1.2}
      viewBox="0 0 100 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <ellipse cx="50" cy="60" rx="45" ry="55" fill={fill} stroke={stroke} strokeWidth="1.2" />
      <ellipse cx="50" cy="60" rx="20" ry="25" fill={fill} stroke={facet} strokeWidth="0.8" opacity="0.5" />
      <line x1="50" y1="5" x2="5" y2="60" stroke={facet} strokeWidth="0.6" opacity="0.4" />
      <line x1="50" y1="5" x2="95" y2="60" stroke={facet} strokeWidth="0.6" opacity="0.4" />
      <line x1="5" y1="60" x2="50" y2="115" stroke={facet} strokeWidth="0.6" opacity="0.4" />
      <line x1="95" y1="60" x2="50" y2="115" stroke={facet} strokeWidth="0.6" opacity="0.4" />
      <line x1="5" y1="60" x2="95" y2="60" stroke={facet} strokeWidth="0.5" opacity="0.4" />
    </svg>
  );
}

export function CushionDiamondIcon({ size = 80, className = '' }: DiamondIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <rect x="10" y="10" width="80" height="80" rx="18" fill="white" stroke="#c8d4e0" strokeWidth="1.2" opacity="0.9" />
      <rect x="22" y="22" width="56" height="56" rx="12" fill="white" stroke="#dde6ef" strokeWidth="0.8" opacity="0.5" />
      <line x1="10" y1="10" x2="50" y2="50" stroke="#dde6ef" strokeWidth="0.5" opacity="0.5" />
      <line x1="90" y1="10" x2="50" y2="50" stroke="#dde6ef" strokeWidth="0.5" opacity="0.5" />
      <line x1="10" y1="90" x2="50" y2="50" stroke="#dde6ef" strokeWidth="0.5" opacity="0.5" />
      <line x1="90" y1="90" x2="50" y2="50" stroke="#dde6ef" strokeWidth="0.5" opacity="0.5" />
    </svg>
  );
}

export function RoundDiamondIcon({ size = 80, className = '', variant = 'default' }: DiamondIconProps) {
  const fill = variant === 'dark' ? '#1B2D44' : '#ffffff';
  const stroke = variant === 'dark' ? '#2a4a6e' : '#c8d4e0';
  const facet = variant === 'dark' ? '#2a4a6e' : '#dde6ef';

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <circle cx="50" cy="50" r="44" fill={fill} stroke={stroke} strokeWidth="1.2" />
      <circle cx="50" cy="50" r="18" fill={fill} stroke={facet} strokeWidth="0.8" opacity="0.5" />
      {[0, 45, 90, 135, 180, 225, 270, 315].map((angle) => {
        const rad = (angle * Math.PI) / 180;
        return (
          <line
            key={angle}
            x1={50 + 18 * Math.cos(rad)}
            y1={50 + 18 * Math.sin(rad)}
            x2={50 + 44 * Math.cos(rad)}
            y2={50 + 44 * Math.sin(rad)}
            stroke={facet}
            strokeWidth="0.6"
            opacity="0.5"
          />
        );
      })}
    </svg>
  );
}
