export type DiamondShape = 'round' | 'oval' | 'cushion' | 'princess' | 'emerald' | 'pear' | 'marquise' | 'radiant';
export type DiamondOrigin = 'lab' | 'natural';
export type QualityTier = 'super-high' | 'balance' | 'maximize-size';
export type CutPreference = 'all-matching' | 'best-cut';
export type Priority = 'size' | 'sparkle' | 'value';

export interface Diamond {
  id: string;
  carat: number;
  shape: DiamondShape;
  color: string;
  clarity: string;
  cut: string;
  price: number;
  compValue: number;
  qualityScore: number;
  priceScore: 'Great' | 'Good' | 'Fair';
  certified: 'IGI' | 'GIA' | 'GCAL';
  hasVideo: boolean;
  caratScore: number;
  sparkleScore: number;
  valueScore: number;
}

export interface DiamondWithRationale extends Diamond {
  rationale: string;
  label?: string;
}

export interface Recommendation {
  primary: DiamondWithRationale;
  alternate1: DiamondWithRationale;
  alternate2: DiamondWithRationale;
  socialProof: string;
}

export interface QuizState {
  type?: string;
  origin?: DiamondOrigin;
  budget?: string;
  shape?: DiamondShape;
  quality?: QualityTier;
  cut?: CutPreference;
  priority?: Priority;
}
