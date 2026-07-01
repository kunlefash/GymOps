'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { AjayBubble } from '@/components/rare-carat/AjayBubble';

function CutContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  function handleSelect(cut: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set('cut', cut);
    router.push(`/rare-carat/quiz/priority?${params.toString()}`);
  }

  return (
    <div className="flex flex-col">
      <AjayBubble message="Cut is the most important of the 4Cs — it's what makes a diamond sparkle:" />

      <div className="px-6 pb-4 max-w-xl mx-auto w-full">
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => handleSelect('all-matching')}
            className="bg-[#1B2D44] text-white rounded-2xl p-6 text-center hover:bg-[#253f5e] active:scale-[0.97] transition-all"
          >
            <h3 className="font-bold text-base mb-1">Show Me All Matching Diamonds</h3>
            <p className="text-gray-300 text-xs">Max size 2.58 carat</p>
          </button>
          <button
            onClick={() => handleSelect('best-cut')}
            className="bg-[#2a3f5c] text-white rounded-2xl p-6 text-center hover:bg-[#34507a] active:scale-[0.97] transition-all"
          >
            <h3 className="font-bold text-base mb-1">Find Me the Best Cut Diamonds*</h3>
            <p className="text-gray-300 text-xs">Max size 2.58 carat</p>
          </button>
        </div>

        <p className="text-xs text-gray-400 text-center mt-5 leading-relaxed">
          *We&apos;ll have our gemologists filter out the diamonds that match our advanced ideals on
          depth percentage, table percentage, crown angle, girdle percentage, girdle thickness, polish, and
          symmetry.
        </p>
      </div>
    </div>
  );
}

export default function CutPage() {
  return (
    <Suspense>
      <CutContent />
    </Suspense>
  );
}
