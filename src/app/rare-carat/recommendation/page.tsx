import Link from 'next/link';
import { getRecommendation } from '@/lib/rare-carat/recommendation';
import type { DiamondWithRationale, Priority } from '@/lib/rare-carat/types';
import { DiamondIcon } from '@/components/rare-carat/DiamondIcon';

function StoneCard({
  diamond,
  isPrimary,
  searchParamsString,
}: {
  diamond: DiamondWithRationale;
  isPrimary: boolean;
  searchParamsString: string;
}) {
  const detailHref = `/rare-carat/diamond/${diamond.id}?rationale=${encodeURIComponent(diamond.rationale)}${
    searchParamsString ? `&${searchParamsString}` : ''
  }`;

  return (
    <div
      className={`rounded-2xl border-2 bg-white overflow-hidden flex flex-col ${
        isPrimary ? 'border-[#4B5EFF] shadow-xl' : 'border-gray-100 shadow-sm'
      }`}
    >
      {isPrimary && (
        <div className="bg-[#4B5EFF] text-white text-xs font-bold text-center py-2 tracking-wide uppercase">
          Your Best Match
        </div>
      )}
      {!isPrimary && diamond.label && (
        <div className="bg-gray-100 text-gray-600 text-xs font-bold text-center py-2 tracking-wide uppercase">
          {diamond.label}
        </div>
      )}

      <div className="flex items-center justify-center bg-gradient-to-b from-gray-50 to-white py-8">
        <DiamondIcon size={isPrimary ? 96 : 72} variant="dark" />
      </div>

      <div className="px-5 pb-5 flex-1 flex flex-col">
        <h3 className={`font-bold ${isPrimary ? 'text-xl' : 'text-base'} text-gray-900 mb-1`}>
          {diamond.carat.toFixed(2)} ct {diamond.shape[0].toUpperCase() + diamond.shape.slice(1)}
        </h3>
        <p className="text-xs text-gray-500 mb-3">
          {diamond.color} Color · {diamond.clarity} Clarity · {diamond.cut} Cut · {diamond.certified} Certified
        </p>

        <div className="flex items-baseline gap-2 mb-3">
          <span className={`font-bold text-gray-900 ${isPrimary ? 'text-2xl' : 'text-lg'}`}>
            ${diamond.price.toLocaleString()}
          </span>
          <span className="text-xs text-gray-400 line-through">${diamond.compValue.toLocaleString()}</span>
          <span className="text-xs font-semibold text-green-600">
            Save {Math.round((1 - diamond.price / diamond.compValue) * 100)}%
          </span>
        </div>

        <div className="bg-[#f0f2ff] border border-[#4B5EFF]/20 rounded-lg p-3 mb-4 flex-1">
          <p className="text-sm text-gray-700 leading-relaxed">{diamond.rationale}</p>
        </div>

        <Link
          href={detailHref}
          className={`text-center font-semibold rounded-full transition-colors ${
            isPrimary
              ? 'bg-[#1B2D44] text-white py-3 hover:bg-[#253f5e]'
              : 'border-2 border-gray-200 text-gray-700 py-2.5 hover:border-[#4B5EFF] hover:text-[#4B5EFF]'
          }`}
        >
          {isPrimary ? 'Choose this diamond' : 'View this stone'}
        </Link>
      </div>
    </div>
  );
}

export default async function RecommendationPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string>>;
}) {
  const params = await searchParams;
  const shape = params.shape || 'oval';
  const priority = (params.priority as Priority) || 'value';
  const budget = params.budget || '2000-3500';

  const recommendation = getRecommendation(shape, priority, budget);

  const paramsString = new URLSearchParams(params).toString();
  const searchHref = `/rare-carat/search?recommended=1&${paramsString}`;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/rare-carat" className="text-xl font-bold text-[#1B2D44]">
            rare <span className="text-[#D946EF]">♥</span> carat
          </Link>
          <Link href={searchHref} className="text-sm text-gray-500 hover:text-[#4B5EFF]">
            See all results →
          </Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="text-center mb-10">
          <p className="text-[#4B5EFF] font-semibold text-sm mb-2 tracking-wide uppercase">
            Based on your answers
          </p>
          <h1 className="text-3xl sm:text-4xl font-bold text-[#1B2D44] mb-3">
            You&apos;ve found your stone.
          </h1>
          <p className="text-gray-500 max-w-xl mx-auto">
            We compared thousands of {shape} diamonds in your budget and picked the one that best matches what
            matters most to you: <span className="font-semibold text-gray-700">{priority}</span>.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start mb-8">
          <StoneCard
            diamond={recommendation.alternate1}
            isPrimary={false}
            searchParamsString={paramsString}
          />
          <div className="md:-mt-6">
            <StoneCard diamond={recommendation.primary} isPrimary searchParamsString={paramsString} />
          </div>
          <StoneCard
            diamond={recommendation.alternate2}
            isPrimary={false}
            searchParamsString={paramsString}
          />
        </div>

        <div className="bg-white border border-gray-100 rounded-xl px-6 py-4 flex items-center gap-3 max-w-xl mx-auto mb-10">
          <span className="text-xl">✓</span>
          <p className="text-sm text-gray-600">{recommendation.socialProof}</p>
        </div>

        <div className="text-center">
          <Link href={searchHref} className="text-sm text-gray-400 hover:text-[#4B5EFF] underline">
            Not quite right? See all results
          </Link>
        </div>
      </main>
    </div>
  );
}
