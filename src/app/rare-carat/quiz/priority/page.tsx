'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { AjayBubble } from '@/components/rare-carat/AjayBubble';
import { QuizCard } from '@/components/rare-carat/QuizCard';

const PRIORITIES = [
  {
    value: 'size',
    label: 'Size',
    subtitle: 'Biggest stone at my budget',
    icon: (
      <svg viewBox="0 0 50 50" width="44" height="44" fill="none">
        <polygon points="25,4 45,18 25,46 5,18" fill="white" opacity="0.95" />
        <polygon points="12,18 25,46 38,18" fill="white" opacity="0.5" />
      </svg>
    ),
  },
  {
    value: 'sparkle',
    label: 'Sparkle',
    subtitle: 'Most light, most fire',
    icon: (
      <svg viewBox="0 0 50 50" width="44" height="44" fill="none">
        <polygon points="25,16 31,25 25,34 19,25" fill="white" />
        <text x="25" y="10" fontSize="14" fill="white" textAnchor="middle">✦</text>
        <text x="10" y="22" fontSize="9" fill="white" textAnchor="middle" opacity="0.8">✦</text>
        <text x="40" y="22" fontSize="9" fill="white" textAnchor="middle" opacity="0.8">✦</text>
        <text x="25" y="46" fontSize="10" fill="white" textAnchor="middle" opacity="0.7">✦</text>
      </svg>
    ),
  },
  {
    value: 'value',
    label: 'Value',
    subtitle: 'Best stone for my money',
    icon: (
      <svg viewBox="0 0 50 50" width="44" height="44" fill="none">
        <circle cx="25" cy="25" r="19" fill="none" stroke="white" strokeWidth="2.5" />
        <text x="25" y="32" fontSize="20" fill="white" textAnchor="middle" fontWeight="bold">$</text>
      </svg>
    ),
  },
];

function PriorityContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  function handleSelect(priority: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set('priority', priority);
    router.push(`/rare-carat/recommendation?${params.toString()}`);
  }

  return (
    <div className="flex flex-col">
      <AjayBubble message="Last question — what matters most to you?" />

      <div className="px-6 pb-6 max-w-2xl mx-auto w-full">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {PRIORITIES.map((p) => (
            <QuizCard
              key={p.value}
              onClick={() => handleSelect(p.value)}
              icon={p.icon}
              title={p.label}
              subtitle={p.subtitle}
            />
          ))}
        </div>
        <p className="text-xs text-center text-gray-400 mt-5">
          We&apos;ll use this to find your best match — and explain exactly why.
        </p>
      </div>
    </div>
  );
}

export default function PriorityPage() {
  return (
    <Suspense>
      <PriorityContent />
    </Suspense>
  );
}
