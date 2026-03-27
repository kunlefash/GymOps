# QR Router-Specific Patterns (zone.zonepay.qrrouter)

## URL Structure

```
Main:     https://qr.zonepay.link/v{version}/{emvco}
Download: https://qr.zonepay.link/redirect/{memberId}/{version}/{emvco}
```

## Adding a New Bank

1. Add config to `app/_config/apps.ts` (iOS Universal Links + Android Intent)
2. Add download links to `app/_config/download-links.ts`
3. Place icon PNG at `public/apps/{bankid}.png`
4. Test on both iOS and Android devices

## Security — Input Sanitization

```typescript
// Whitelist-only query params (env: NEXT_PUBLIC_QUERY_WHITELIST)
export function sanitizeQueryParams(params: URLSearchParams): URLSearchParams {
  const whitelist = process.env.NEXT_PUBLIC_QUERY_WHITELIST?.split(',') || [];
  const sanitized = new URLSearchParams();
  for (const key of whitelist) {
    if (params.has(key)) sanitized.set(key, sanitize(params.get(key)!));
  }
  return sanitized;
}
```

## Security — Host Validation (prevents open redirects)

```typescript
export function isValidHost(url: string): boolean {
  const allowedHosts = ['apps.apple.com', 'play.google.com',
    process.env.NEXT_PUBLIC_DEEP_LINK_HOST];
  return allowedHosts.includes(new URL(url).host);
}
```

## Platform Association Files

- **Android**: `app/api/assetlinks/route.ts` -> `/.well-known/assetlinks.json`
- **iOS**: `app/api/apple-app-site-association/route.ts` -> `/apple-app-site-association`
