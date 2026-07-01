'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { AjayBubble } from '@/components/rare-carat/AjayBubble';

const BUDGET_RANGES = [
  { label: 'Under $1,000', value: 'under-1000', sub: 'Best for smaller stones' },
  { label: '$1,000 – $2,000', value: '1000-2000', sub: 'Popular for 1–1.5ct' },
  { label: '$2,000 – $3,500', value: '2000-3500', sub: 'Most shoppers choose this', popular: true },
  { label: '$3,500 – $5,000', value: '3500-5000', sub: 'Premium quality range' },
  { label: '$5,000+', value: '5000-plus', sub: 'No limits on quality' },
];

function BudgetContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const shape = searchParams.get('shape') || '';

  function handleSelect(budget: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set('budget', budget);
    router.push(`/rare-carat/quiz/shape?${params.toString()}`);
  }

  return (
    <div className="flex flex-col">
      <AjayBubble message="What's your budget? Most couples find their perfect stone in the $2,000–$3,500 range." />

      <div className="px-6 pb-6 max-w-xl mx-auto w-full">
        {shape && (
          <p className="text-xs text-gray-400 text-center mb-4">
            💡 Most shoppers choosing {shape} diamonds spend between $1,500–$3,500
          </p>
        )}

        <div className="flex flex-col gap-3">
          {BUDGET_RANGES.map((range) => (
            <button
              key={range.value}
              onClick={() => handleSelect(range.value)}
              className={`
                w-full flex items-center justify-between px-5 py-4 rounded-xl border-2 text-left
                transition-all duration-150 active:scale-[0.99]
                ${range.popular
                  ? 'border-[#4B5EFF] bg-[#f0f2ff] hover:bg-[#e8ebff]'
                  : 'border-gray-100 bg-white hover:border-[#4B5EFF] hover:bg-gray-50'
                }
              `}
            >
              <div>
                <p className={`font-semibold text-base ${range.popular ? 'text-[#4B5EFF]' : 'text-gray-900'}`}>
                  {range.label}
                </p>
                <p className="text-sm text-gray-400 mt-0.5">{range.sub}</p>
              </div>
              {range.popular && (
                <span className="bg-[#4B5EFF] text-white text-[10px] font-bold px-2.5 py-1 rounded-full whitespace-nowrap ml-3">
                  Most popular
                </span>
              )}
            </button>
          ))}
        </div>

        <p className="text-xs text-center text-gray-400 mt-5">
          Rare Carat can save you up to 21% vs other online retailers
        </p>
      </div>
    </div>
  );
}

export default function BudgetPage() {
  return (
    <Suspense>
      <BudgetContent />
    </Suspense>
  );
}
