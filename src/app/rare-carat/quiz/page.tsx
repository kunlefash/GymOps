'use client';

import { useRouter } from 'next/navigation';
import { Suspense } from 'react';
import { AjayBubble } from '@/components/rare-carat/AjayBubble';
import { QuizCard } from '@/components/rare-carat/QuizCard';

function QuizIntroContent() {
  const router = useRouter();

  const options = [
    {
      value: 'complete-ring',
      icon: (
        <svg viewBox="0 0 50 50" width="52" height="52" fill="none">
          <circle cx="25" cy="25" r="16" stroke="white" strokeWidth="5" fill="none" />
          <polygon points="25,8 34,18 16,18" fill="white" opacity="0.9" />
          <line x1="25" y1="8" x2="25" y2="18" stroke="white" strokeWidth="0.8" opacity="0.5" />
          <line x1="16" y1="18" x2="34" y2="18" stroke="white" strokeWidth="0.8" opacity="0.5" />
          <line x1="16" y1="18" x2="25" y2="28" stroke="white" strokeWidth="0.8" opacity="0.5" />
          <line x1="34" y1="18" x2="25" y2="28" stroke="white" strokeWidth="0.8" opacity="0.5" />
        </svg>
      ),
      label: 'Complete ring',
    },
    {
      value: 'loose-diamond',
      icon: (
        <svg viewBox="0 0 50 50" width="52" height="52" fill="none">
          <polygon points="25,4 46,20 25,46 4,20" fill="white" opacity="0.95" stroke="rgba(255,255,255,0.3)" strokeWidth="0.5" />
          <polygon points="25,4 35,20 25,46" fill="white" opacity="0.6" />
          <line x1="4" y1="20" x2="46" y2="20" stroke="rgba(255,255,255,0.4)" strokeWidth="0.8" />
          <line x1="25" y1="4" x2="25" y2="20" stroke="rgba(255,255,255,0.4)" strokeWidth="0.8" />
        </svg>
      ),
      label: 'Loose diamond',
    },
    {
      value: 'other',
      icon: (
        <svg viewBox="0 0 50 50" width="52" height="52" fill="none">
          <polygon points="25,6 29,19 44,19 32,28 36,41 25,33 14,41 18,28 6,19 21,19" fill="white" opacity="0.9" />
        </svg>
      ),
      label: 'Other jewelry',
    },
  ];

  function handleSelect(type: string) {
    router.push(`/rare-carat/quiz/origin?type=${type}`);
  }

  return (
    <div className="flex flex-col">
      <AjayBubble message="Hey, Ajay here 👋 What can I help you find?" />

      <div className="px-6 pb-6 max-w-2xl mx-auto w-full">
        <div className="grid grid-cols-3 gap-3">
          {options.map((opt) => (
            <QuizCard
              key={opt.value}
              onClick={() => handleSelect(opt.value)}
              icon={opt.icon}
              title={opt.label}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function QuizIntroPage() {
  return (
    <Suspense>
      <QuizIntroContent />
    </Suspense>
  );
}
