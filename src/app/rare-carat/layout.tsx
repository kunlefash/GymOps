import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], variable: '--font-rc-inter' });

export const metadata: Metadata = {
  title: 'Rare Carat — Diamond Decision Advisor',
  description: 'The smarter way to buy diamonds. AI price and quality scores on 900,000+ lab and natural diamonds.',
};

export default function RareCaratLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      className={inter.variable}
      style={{ fontFamily: 'var(--font-rc-inter), Inter, sans-serif' }}
    >
      {children}
    </div>
  );
}
