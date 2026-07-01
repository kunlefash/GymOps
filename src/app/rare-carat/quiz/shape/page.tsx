'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { AjayBubble } from '@/components/rare-carat/AjayBubble';
import { QuizCard } from '@/components/rare-carat/QuizCard';
import { RoundDiamondIcon, OvalDiamondIcon, CushionDiamondIcon } from '@/components/rare-carat/DiamondIcon';

const SHAPES = [
  { value: 'round', label: 'Round', pct: '40%', Icon: RoundDiamondIcon },
  { value: 'oval', label: 'Oval', pct: '15%', Icon: OvalDiamondIcon },
  { value: 'cushion', label: 'Cushion', pct: '15%', Icon: CushionDiamondIcon },
];

function ShapeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  function handleSelect(shape: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set('shape', shape);
    router.push(`/rare-carat/quiz/quality?${params.toString()}`);
  }

  return (
    <div className="flex flex-col">
      <AjayBubble
        message={
          <>
            What shape are you looking for?
            <br />
            <span className="text-xs text-gray-400 font-normal">
              ✋ See shapes on a hand <span className="text-[#4B5EFF] cursor-pointer hover:underline">here</span>.
            </span>
          </>
        }
      />

      <div className="px-6 pb-4 max-w-2xl mx-auto w-full">
        <div className="grid grid-cols-3 gap-3">
          {SHAPES.map(({ value, label, pct, Icon }) => (
            <QuizCard
              key={value}
              onClick={() => handleSelect(value)}
              icon={<Icon size={44} />}
              title={label}
              subtitle={`${pct} people choose this`}
            />
          ))}
        </div>

        <button
          onClick={() => handleSelect('round')}
          className="w-full mt-4 border-2 border-gray-200 text-[#4B5EFF] font-medium py-3 rounded-xl hover:border-[#4B5EFF] transition-colors text-sm"
        >
          See other shapes
        </button>
      </div>
    </div>
  );
}

export default function ShapePage() {
  return (
    <Suspense>
      <ShapeContent />
    </Suspense>
  );
}
