import Link from 'next/link';

interface SearchPageProps {
  searchParams: Promise<Record<string, string>>;
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const params = await searchParams;
  const shape = params.shape || '';
  const budget = params.budget || '';
  const recommended = params.recommended || '';

  return (
    <div className="min-h-screen bg-white" style={{ fontFamily: 'Inter, sans-serif' }}>
      {/* Minimal nav */}
      <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link href="/rare-carat" className="flex flex-col leading-none">
            <span className="text-[#1B2D44] font-bold text-lg tracking-tight">
              rare <span className="text-[#D946EF]">&#9829;</span> carat
            </span>
          </Link>
          <Link href="/rare-carat/quiz" className="text-sm text-[#4B5EFF] font-medium hover:underline">
            ← Back to advisor
          </Link>
        </div>
      </nav>

      {/* Filter bar */}
      <div className="border-b border-gray-100 py-4 px-4 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <p className="text-sm text-gray-500 mb-3">
            Search for Diamonds
            {shape && (
              <span className="ml-2 text-gray-700 font-medium">· {shape.charAt(0).toUpperCase() + shape.slice(1)}</span>
            )}
          </p>

          {/* Lab / Natural toggle */}
          <div className="flex items-center gap-3 mb-4">
            <button className="bg-[#1B2D44] text-white px-5 py-1.5 rounded-full text-sm font-medium">Lab</button>
            <button className="border border-gray-200 text-gray-600 px-5 py-1.5 rounded-full text-sm font-medium hover:border-gray-400">Natural</button>
            <span className="text-[#4B5EFF] text-sm ml-2 cursor-pointer hover:underline">What&apos;s the difference?</span>
          </div>

          {/* Filter sliders (static display) */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-xs text-gray-500">
            {[
              { label: 'SHAPE', value: shape || 'Oval' },
              { label: 'CARAT', value: '2.0 – 3.0' },
              { label: 'COLOR', value: 'K – H' },
              { label: 'CUT', value: 'RC Ideal' },
              { label: 'CLARITY', value: 'VS2 – FL' },
              { label: 'PRICE', value: `$350 – $${budget ? parseInt(budget.replace(/\D/g, '') || '2500').toLocaleString() : '3,500'}` },
            ].map((f) => (
              <div key={f.label} className="flex flex-col gap-1">
                <span className="font-semibold text-gray-400 text-[10px] tracking-wider">{f.label}</span>
                <div className="h-1 bg-[#4B5EFF] rounded-full w-3/4" />
                <span className="text-gray-600 font-medium">{f.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* If coming from recommendation, show pinned stone banner */}
        {recommended && (
          <div className="mb-6 bg-blue-50 border border-blue-100 rounded-xl p-4 flex items-center justify-between gap-4">
            <div>
              <p className="text-xs text-[#4B5EFF] font-semibold uppercase tracking-wide mb-1">Your recommended stone</p>
              <p className="text-sm text-gray-700 font-medium">Pinned at top of results based on your quiz answers</p>
            </div>
            <Link
              href={`/rare-carat/recommendation?shape=${shape}&budget=${budget}`}
              className="text-xs text-[#4B5EFF] font-semibold hover:underline whitespace-nowrap"
            >
              Back to recommendation →
            </Link>
          </div>
        )}

        {/* Results header */}
        <div className="flex items-center justify-between mb-6">
          <p className="text-gray-500 text-sm">
            <span className="text-gray-900 font-semibold">920,754</span> lab-grown diamonds found
          </p>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 text-sm text-gray-600 border border-gray-200 px-3 py-1.5 rounded-lg hover:border-gray-400">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
              </svg>
              Visual
            </button>
            <select className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-600 bg-white">
              <option>Best Value</option>
              <option>Price: Low</option>
              <option>Price: High</option>
              <option>Carat: High</option>
            </select>
          </div>
        </div>

        {/* Preset chips */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {['<1ct', '1ct+', '1.5ct+', '2ct+', '2.5ct+', '3ct+', 'Sweet Spot', 'Top Quality', 'Budget'].map((chip) => (
            <button
              key={chip}
              className="px-3 py-1 rounded-full text-xs font-medium border border-gray-200 text-gray-600 hover:border-[#4B5EFF] hover:text-[#4B5EFF] transition-colors"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* AI picks */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-[#4B5EFF]">✦</span>
            <h3 className="font-semibold text-gray-900">Top AI picks</h3>
            <span className="text-gray-400 text-sm">· Based on your filters</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { label: 'Overall pick', carat: '2.47ct', color: 'H', clarity: 'VS1', cut: 'RC Ideal Cut', price: '$2,280', compValue: '$3,420', quality: '15/15', labelColor: 'bg-green-500' },
              { label: 'Biggest size', carat: '2.58ct', color: 'I', clarity: 'VS2', cut: 'RC Ideal Cut', price: '$2,180', compValue: '$3,280', quality: '14/15', labelColor: 'bg-purple-500' },
              { label: 'Highest quality', carat: '2.31ct', color: 'G', clarity: 'VS1', cut: 'RC Ideal Cut', price: '$2,280', compValue: '$3,250', quality: '15/15', labelColor: 'bg-blue-500' },
            ].map((card) => (
              <Link
                key={card.label}
                href={`/rare-carat/diamond/oval-001?rationale=${encodeURIComponent('Recommended for your search priorities')}`}
                className="border border-gray-100 rounded-xl overflow-hidden hover:shadow-md transition-shadow group"
              >
                <div className="relative">
                  <span className={`absolute top-2 left-2 z-10 text-white text-[10px] font-bold px-2 py-0.5 rounded-full ${card.labelColor}`}>
                    {card.label}
                  </span>
                  <div className="bg-gray-50 h-44 flex items-center justify-center">
                    <svg viewBox="0 0 100 90" width="80" height="80" fill="none">
                      <ellipse cx="50" cy="45" rx="40" ry="40" fill="white" stroke="#d0d8e8" strokeWidth="1.5" />
                      <ellipse cx="50" cy="45" rx="18" ry="18" fill="white" stroke="#e0e8f0" strokeWidth="0.8" opacity="0.6" />
                    </svg>
                  </div>
                </div>
                <div className="p-3">
                  <p className="font-semibold text-gray-900 text-sm">{card.carat} · {card.color} · {card.clarity}</p>
                  <p className="text-gray-400 text-xs mb-2">{card.cut}</p>
                  <p className="font-bold text-gray-900">{card.price}</p>
                  <p className="text-gray-400 text-xs">Comp. value: <s>{card.compValue}</s></p>
                  <p className="text-green-600 text-xs font-medium mt-1">✓ {card.quality} quality</p>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Back to advisor CTA */}
        <div className="mt-8 py-8 border-t border-gray-100 text-center">
          <p className="text-gray-500 text-sm mb-3">Looking for a personal recommendation?</p>
          <Link
            href="/rare-carat/quiz"
            className="inline-flex items-center gap-2 bg-[#1B2D44] text-white font-semibold px-6 py-3 rounded-full hover:bg-[#253f5e] transition-colors text-sm"
          >
            ✦ Get a personalized recommendation
          </Link>
        </div>
      </div>
    </div>
  );
}
