import Link from 'next/link';

const pressLogos = [
  { name: 'The New York Times', text: 'The New York Times' },
  { name: 'New York Post', text: 'New York Post' },
  { name: 'Forbes', text: 'Forbes' },
  { name: 'USA Today', text: 'USA TODAY' },
];

const categories = [
  'Engagement rings',
  'Earrings',
  'Wedding rings',
  'Necklaces',
  '1 carat diamonds',
  'Three stone',
  'Solitaire',
  'Hoops',
];

export default function RareCaratHomepage() {
  return (
    <div className="min-h-screen bg-white" style={{ fontFamily: 'Inter, sans-serif' }}>
      {/* Announcement bar */}
      <div className="bg-[#8B1818] text-white text-sm py-2 px-4 flex items-center justify-between">
        <span className="hidden sm:block">(855) 720-4858</span>
        <p className="text-center font-medium flex-1">
          Summer Sale · Save up to 40%* · Diamonds, Rings and Jewelry
        </p>
        <div className="hidden sm:flex items-center gap-3 text-white/80 text-sm">
          <a href="#" className="hover:text-white transition-colors">Contact us</a>
          <span>|</span>
          <a href="#" className="hover:text-white transition-colors">Sign in</a>
        </div>
      </div>

      {/* Nav */}
      <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            {/* Logo */}
            <Link href="/rare-carat" className="flex flex-col leading-none">
              <span className="text-[#1B2D44] font-bold text-xl tracking-tight">
                rare <span className="text-[#D946EF]">&#9829;</span> carat
              </span>
              <span className="text-[9px] text-gray-400 font-normal tracking-widest uppercase">
                America&apos;s #1 Ring Marketplace
              </span>
            </Link>

            {/* Nav links */}
            <div className="hidden lg:flex items-center gap-6 text-[13px] text-gray-700 font-medium">
              {['Engagement rings', 'Wedding bands', 'Diamonds', 'Earrings', 'Necklaces', 'Bracelets', 'Gifts'].map(
                (item) => (
                  <a key={item} href="#" className="hover:text-[#1B2D44] transition-colors whitespace-nowrap">
                    {item}
                  </a>
                )
              )}
            </div>

            {/* Icons */}
            <div className="flex items-center gap-2">
              <button className="p-2 text-gray-500 hover:text-gray-800 transition-colors" aria-label="Search">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <circle cx="11" cy="11" r="8" />
                  <path d="M21 21l-4.35-4.35" />
                </svg>
              </button>
              <button className="p-2 text-gray-500 hover:text-gray-800 transition-colors" aria-label="Wishlist">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                </svg>
              </button>
              <button className="p-2 text-gray-500 hover:text-gray-800 transition-colors relative" aria-label="Cart">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <circle cx="9" cy="21" r="1" />
                  <circle cx="20" cy="21" r="1" />
                  <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
                </svg>
                <span className="absolute top-1 right-1 bg-[#4B5EFF] text-white text-[9px] rounded-full w-4 h-4 flex items-center justify-center font-bold">
                  0
                </span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-12 lg:py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Copy */}
          <div className="max-w-lg">
            <h1 className="text-[42px] sm:text-5xl font-bold text-[#1B2D44] leading-[1.1] tracking-tight mb-4">
              The smarter way<br />to buy diamonds
            </h1>
            <p className="text-gray-500 text-lg mb-8 leading-relaxed">
              Tell us what matters — we&apos;ll find your stone. AI price and quality scores on 900,000+ lab and natural diamonds.
            </p>

            {/* CTAs — KEY CHANGE: advisor is primary */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                href="/rare-carat/quiz"
                className="inline-flex items-center justify-center gap-2 bg-[#1B2D44] text-white font-semibold px-7 py-3.5 rounded-full hover:bg-[#253f5e] transition-colors text-base shadow-sm"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
                Find my diamond
              </Link>
              <Link
                href="/rare-carat/search"
                className="inline-flex items-center justify-center gap-2 border-2 border-[#1B2D44] text-[#1B2D44] font-semibold px-7 py-3.5 rounded-full hover:bg-gray-50 transition-colors text-base"
              >
                Search the catalog
              </Link>
            </div>

            {/* Press logos */}
            <div className="flex items-center gap-6 mt-10 flex-wrap">
              {pressLogos.map((logo) => (
                <span key={logo.name} className="text-gray-300 font-semibold text-sm tracking-tight">
                  {logo.text}
                </span>
              ))}
            </div>
          </div>

          {/* Right: Ring image placeholder */}
          <div className="flex items-center justify-center lg:justify-end">
            <div className="relative w-80 h-80 lg:w-96 lg:h-96">
              {/* Stylized diamond ring illustration */}
              <div className="w-full h-full rounded-full bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center shadow-inner">
                <svg viewBox="0 0 200 200" className="w-64 h-64" fill="none" xmlns="http://www.w3.org/2000/svg">
                  {/* Ring band */}
                  <ellipse cx="100" cy="160" rx="60" ry="20" fill="none" stroke="#C0A060" strokeWidth="8" />
                  <rect x="40" y="80" width="120" height="80" rx="4" fill="none" stroke="#C0A060" strokeWidth="8" />
                  <ellipse cx="100" cy="80" rx="60" ry="20" fill="#C8A870" stroke="#C0A060" strokeWidth="8" />
                  {/* Diamond */}
                  <polygon points="100,20 140,65 100,90 60,65" fill="white" stroke="#d0d8e8" strokeWidth="1.5" />
                  <polygon points="60,65 100,90 100,20" fill="#e8eef5" opacity="0.6" />
                  <polygon points="140,65 100,90 100,20" fill="#dce5f0" opacity="0.6" />
                  <line x1="100" y1="20" x2="100" y2="90" stroke="#ccd8e8" strokeWidth="0.8" />
                  <line x1="60" y1="65" x2="140" y2="65" stroke="#ccd8e8" strokeWidth="0.8" />
                  {/* Sparkles */}
                  <text x="148" y="35" fontSize="14" fill="#FFD700">✦</text>
                  <text x="40" y="50" fontSize="10" fill="#FFD700">✦</text>
                  <text x="155" y="70" fontSize="8" fill="#FFD700">·</text>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust strip */}
      <section className="border-t border-gray-100 py-5">
        <div className="max-w-5xl mx-auto px-4">
          <div className="flex flex-wrap items-center justify-center gap-8 text-sm text-gray-500 font-medium">
            <div className="flex items-center gap-2">
              <span className="text-green-500">★</span>
              <span>#1 on Trustpilot</span>
            </div>
            <div className="flex items-center gap-2">
              <span>♡</span>
              <span>100K+ happy couples</span>
            </div>
            <div className="flex items-center gap-2">
              <span>💡</span>
              <span>*Save based on comp. value</span>
            </div>
            <div className="flex items-center gap-2">
              <span>✦</span>
              <span>AI quality scores</span>
            </div>
          </div>
        </div>
      </section>

      {/* Category carousel */}
      <section className="py-10 border-t border-gray-100">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-6 overflow-x-auto pb-2 scrollbar-hide">
            {categories.map((cat) => (
              <a
                key={cat}
                href="#"
                className="flex flex-col items-center gap-3 flex-shrink-0 group"
              >
                <div className="w-20 h-20 rounded-full bg-gray-50 border border-gray-100 flex items-center justify-center group-hover:border-gray-300 transition-colors">
                  <svg viewBox="0 0 50 50" width="36" height="36" fill="none">
                    <circle cx="25" cy="25" r="18" fill="#e8eaf0" />
                    <polygon points="25,10 38,22 25,38 12,22" fill="white" stroke="#c0c8d8" strokeWidth="1" />
                  </svg>
                </div>
                <span className="text-xs text-gray-600 font-medium text-center whitespace-nowrap">
                  {cat}
                </span>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Demo notice */}
      <div className="fixed bottom-4 right-4 bg-[#1B2D44] text-white text-xs px-4 py-2.5 rounded-full shadow-lg opacity-90">
        🎯 Demo — Diamond Decision Advisor
      </div>
    </div>
  );
}
