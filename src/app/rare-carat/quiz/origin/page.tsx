'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { AjayBubble } from '@/components/rare-carat/AjayBubble';
import { QuizCard } from '@/components/rare-carat/QuizCard';

function OriginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  function handleSelect(origin: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set('origin', origin);
    router.push(`/rare-carat/quiz/budget?${params.toString()}`);
  }

  return (
    <div className="flex flex-col">
      <AjayBubble
        message={
          <>
            Looking for <strong>natural</strong> or <strong>lab created</strong> diamonds? We search
            both.{' '}
            <span className="text-[#4B5EFF] cursor-pointer hover:underline">Learn the difference here.</span>
          </>
        }
      />

      <div className="px-6 pb-6 max-w-xl mx-auto w-full">
        <div className="grid grid-cols-2 gap-4">
          <QuizCard
            onClick={() => handleSelect('natural')}
            icon={
              <svg viewBox="0 0 50 50" width="48" height="48" fill="none">
                <circle cx="25" cy="30" r="12" fill="#10B981" opacity="0.8" />
                <path d="M25 18 Q30 8 40 6 Q35 16 25 18Z" fill="#10B981" opacity="0.7" />
                <path d="M25 18 Q20 8 10 6 Q15 16 25 18Z" fill="#10B981" opacity="0.6" />
                <polygon points="25,5 32,15 25,20 18,15" fill="white" opacity="0.9" />
              </svg>
            }
            title="Natural"
            subtitle="Conflict-free, mined"
          />
          <div className="relative">
            <QuizCard
              onClick={() => handleSelect('lab')}
              icon={
                <svg viewBox="0 0 50 50" width="48" height="48" fill="none">
                  <rect x="18" y="28" width="14" height="16" rx="2" fill="rgba(255,255,255,0.3)" />
                  <polygon points="25,4 36,18 25,25 14,18" fill="white" opacity="0.95" />
                  <line x1="14" y1="18" x2="36" y2="18" stroke="rgba(255,255,255,0.4)" strokeWidth="0.8" />
                  <line x1="25" y1="4" x2="25" y2="18" stroke="rgba(255,255,255,0.4)" strokeWidth="0.8" />
                </svg>
              }
              title="Lab Created"
              subtitle="Man-made, chemically identical"
            />
            <div className="absolute top-2 right-2 bg-[#10B981] text-white text-[9px] font-bold px-2 py-0.5 rounded-full tracking-wide">
              Eco-friendly
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function OriginPage() {
  return (
    <Suspense>
      <OriginContent />
    </Suspense>
  );
}
