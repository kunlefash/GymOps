import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getDiamondById } from '@/lib/rare-carat/diamonds';
import { DiamondIcon } from '@/components/rare-carat/DiamondIcon';

export default async function DiamondDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string>>;
}) {
  const { id } = await params;
  const sp = await searchParams;
  const diamond = getDiamondById(id);

  if (!diamond) {
    notFound();
  }

  const rationale = sp.rationale;
  const savingsPct = Math.round((1 - diamond.price / diamond.compValue) * 100);

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-gray-100 sticky top-0 bg-white z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/rare-carat" className="text-xl font-bold text-[#1B2D44]">
            rare <span className="text-[#D946EF]">♥</span> carat
          </Link>
          <Link href="/rare-carat/search" className="text-sm text-gray-500 hover:text-[#4B5EFF]">
            ← Back to results
          </Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        {rationale && (
          <div className="bg-[#f0f2ff] border border-[#4B5EFF]/30 rounded-xl px-5 py-4 mb-8 flex items-start gap-3">
            <span className="text-[#4B5EFF] text-lg leading-none">✦</span>
            <div>
              <p className="text-xs font-bold text-[#4B5EFF] uppercase tracking-wide mb-1">
                Why we picked this for you
              </p>
              <p className="text-sm text-gray-700 leading-relaxed">{rationale}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <div className="flex flex-col items-center justify-center bg-gray-50 rounded-2xl py-16">
            <DiamondIcon size={180} variant="dark" />
            <p className="text-xs text-gray-400 mt-4">360° viewer placeholder</p>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="bg-[#1B2D44] text-white text-[10px] font-bold px-2.5 py-1 rounded uppercase tracking-wide">
                {diamond.certified} Certified
              </span>
              <span className="bg-gray-100 text-gray-600 text-[10px] font-bold px-2.5 py-1 rounded uppercase tracking-wide">
                {diamond.priceScore} Price
              </span>
              {diamond.hasVideo && (
                <span className="bg-gray-100 text-gray-600 text-[10px] font-bold px-2.5 py-1 rounded uppercase tracking-wide">
                  Video Available
                </span>
              )}
            </div>

            <h1 className="text-2xl font-bold text-[#1B2D44] mb-1">
              {diamond.carat.toFixed(2)} Carat {diamond.shape[0].toUpperCase() + diamond.shape.slice(1)} Diamond
            </h1>
            <p className="text-sm text-gray-500 mb-6">Quality Score: {diamond.qualityScore}/100</p>

            <div className="grid grid-cols-2 gap-3 mb-6">
              {[
                { label: 'Shape', value: diamond.shape[0].toUpperCase() + diamond.shape.slice(1) },
                { label: 'Carat', value: diamond.carat.toFixed(2) },
                { label: 'Color', value: diamond.color },
                { label: 'Clarity', value: diamond.clarity },
                { label: 'Cut', value: diamond.cut },
                { label: 'Certified', value: diamond.certified },
              ].map((spec) => (
                <div key={spec.label} className="border border-gray-100 rounded-lg px-3 py-2">
                  <p className="text-[10px] text-gray-400 uppercase tracking-wide">{spec.label}</p>
                  <p className="text-sm font-semibold text-gray-900">{spec.value}</p>
                </div>
              ))}
            </div>

            <div className="border-t border-gray-100 pt-5 mb-6">
              <div className="flex items-baseline gap-3 mb-1">
                <span className="text-3xl font-bold text-gray-900">${diamond.price.toLocaleString()}</span>
                <span className="text-base text-gray-400 line-through">
                  ${diamond.compValue.toLocaleString()}
                </span>
              </div>
              <p className="text-sm font-semibold text-green-600">
                You save {savingsPct}% (${(diamond.compValue - diamond.price).toLocaleString()}) vs. comparable retail
              </p>
            </div>

            <button className="w-full bg-[#1B2D44] text-white font-semibold py-4 rounded-full hover:bg-[#253f5e] transition-colors mb-3">
              Choose this diamond
            </button>
            <p className="text-xs text-center text-gray-400">
              Free 30-day returns · Lifetime warranty · Free shipping &amp; insurance
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
