# PWA-Specific Patterns (zone.gymopspwa)

## Next.js Middleware (Auth + CORS + Device Detection)

```typescript
// middleware.ts — real pattern from zone.gymopspwa
export function middleware(request: NextRequest) {
  // 1. Inject Bearer token from cookie into headers
  const token = request.cookies.get('token')?.value;
  if (token) {
    requestHeaders.set('Authorization', `Bearer ${token}`);
  }

  // 2. CORS handling for API routes (OPTIONS preflight + actual)
  if (pathname.startsWith('/api/')) { /* CORS headers */ }

  // 3. Mobile/tablet detection via User-Agent + viewport cookie
  const isMobile = /Android|iPhone|iPad|iPod/i.test(userAgent);
}
```

## Client vs Server Components

```typescript
// Server Component (default — no 'use client')
// app/my-page/page.tsx
export const metadata: Metadata = { title: 'My Page | GymOps' };
export default function MyPage() { return <MyPageClient />; }

// Client Component ('use client' required)
// app/my-page/MyPageClient.tsx
'use client';
export const MyPageClient: FC = () => {
  const { user } = useAuth();
  return <div>Welcome, {user?.name}</div>;
};
```

## PWA Custom Hooks (14 hooks)

| Hook | Purpose |
|---|---|
| `useAuth` | Auth state + token management |
| `useAxios` | HTTP with auth headers |
| `usePushNotifications` | Firebase Cloud Messaging |
| `useTransactionWebSocket` | Real-time transaction updates |
| `useScreenLock` | Screen lock detection |
| `useNavigationOptimization` | Route prefetching |
| `useInfiniteSearchQuery` | Infinite scroll search |
| `usePersistedClient` | React Query persistence |
| `useFileDownload` | File download handling |
| `useMobile` / `useIsDesktop` | Device detection |

## Firebase Cloud Messaging

```typescript
// lib/firebase.ts
import { initializeApp } from 'firebase/app';
import { getMessaging } from 'firebase/messaging';

const app = initializeApp({
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  // ...
});
export const messaging = typeof window !== 'undefined' ? getMessaging(app) : null;
```

## Cloudflare Workers Deployment

Both PWA and QR Router use Cloudflare Workers via OpenNext adapter:

```bash
# PWA
npm run deploy  # opennextjs-cloudflare build && deploy

# QR Router
npm run deploy  # pre-deploy (lint+test) + opennextjs-cloudflare
```

Webpack config excludes Node.js modules (`fs`, `net`, `crypto`, etc.) and Firebase
from server-side bundles for Cloudflare compatibility.
