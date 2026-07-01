'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Suspense } from 'react';

const QUIZ_PATHS = [
  '/rare-carat/quiz',
  '/rare-carat/quiz/origin',
  '/rare-carat/quiz/budget',
  '/rare-carat/quiz/shape',
  '/rare-carat/quiz/quality',
  '/rare-carat/quiz/cut',
  '/rare-carat/quiz/priority',
];

function QuizChromeInner({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  const currentStep = QUIZ_PATHS.indexOf(pathname);
  const totalSteps = QUIZ_PATHS.length;
  const progressPct = currentStep >= 0 ? ((currentStep + 1) / totalSteps) * 100 : 14;

  function handleBack() {
    if (currentStep > 0) {
      router.push(`${QUIZ_PATHS[currentStep - 1]}?${searchParams.toString()}`);
    } else {
      router.push('/rare-carat');
    }
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Progress bar */}
      <div className="h-[3px] bg-gray-100">
        <div
          className="h-full bg-[#4B5EFF] transition-[width] duration-500 ease-out"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Chrome header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-50">
        <button
          onClick={handleBack}
          className="p-2 rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-50 transition-colors"
          aria-label="Go back"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 5l-7 7 7 7" />
          </svg>
        </button>

        <Link href="/rare-carat" className="flex flex-col items-center leading-none">
          <span className="text-[#1B2D44] font-bold text-base tracking-tight">
            rare <span className="text-[#D946EF]">&#9829;</span> carat
          </span>
          <span className="text-[10px] text-gray-400 mt-0.5">America&apos;s #1 Ring Marketplace</span>
        </Link>

        <Link
          href="/rare-carat"
          className="p-2 rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-50 transition-colors"
          aria-label="Close quiz"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </Link>
      </div>

      {/* Wave background container */}
      <div className="flex-1 relative overflow-hidden">
        <div className="relative z-10 pb-16">
          {children}
        </div>
        {/* Decorative bottom wave */}
        <div className="absolute bottom-0 left-0 right-0 pointer-events-none">
          <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" className="w-full h-20">
            <path
              d="M0 60 C360 120 720 0 1080 60 C1260 90 1380 50 1440 60 L1440 120 L0 120 Z"
              fill="#EAECF5"
            />
          </svg>
        </div>
      </div>
    </div>
  );
}

export function QuizChrome({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="animate-pulse text-gray-300 text-sm">Loading...</div>
      </div>
    }>
      <QuizChromeInner>{children}</QuizChromeInner>
    </Suspense>
  );
}
