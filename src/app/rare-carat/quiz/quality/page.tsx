'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { AjayBubble } from '@/components/rare-carat/AjayBubble';
import { QuizCard } from '@/components/rare-carat/QuizCard';
import { DiamondIcon } from '@/components/rare-carat/DiamondIcon';

const TIERS = [
  {
    value: 'super-high',
    title: 'Super High Quality',
    subtitle: 'Ultra white, no visible imperfections',
    details: [
      { label: 'Color', value: 'F Color+' },
      { label: 'Clarity', value: 'VVS2 Clarity+' },
      { label: 'Carat (Max)', value: '1.96' },
    ],
  },
  {
    value: 'balance',
    title: 'Balance Size & Quality',
    subtitle: 'Pretty white, no imperfections to naked eye',
    recommended: true,
    details: [
      { label: 'Color', value: 'H Color+' },
      { label: 'Clarity', value: 'VS2 Clarity+' },
      { label: 'Carat (Max)', value: '2.58' },
    ],
  },
  {
    value: 'maximize-size',
    title: 'Maximize Size',
    subtitle: 'Slight yellow with small imperfections',
    details: [
      { label: 'Color', value: 'K Color+' },
      { label: 'Clarity', value: 'SI2 Clarity+' },
      { label: 'Carat (Max)', value: '2.58' },
    ],
  },
];

function QualityContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  function handleSelect(quality: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set('quality', quality);
    router.push(`/rare-carat/quiz/cut?${params.toString()}`);
  }

  return (
    <div className="flex flex-col">
      <AjayBubble message="What quality are you aiming for? We can adjust color & quality later." />

      <div className="px-6 pb-6 max-w-3xl mx-auto w-full">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {TIERS.map((tier) => (
            <QuizCard
              key={tier.value}
              onClick={() => handleSelect(tier.value)}
              icon={<DiamondIcon size={48} />}
              title={tier.title}
              subtitle={tier.subtitle}
              recommended={tier.recommended}
              details={tier.details}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function QualityPage() {
  return (
    <Suspense>
      <QualityContent />
    </Suspense>
  );
}
