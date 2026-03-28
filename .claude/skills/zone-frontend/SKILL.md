---
name: zone-frontend
description: Frontend development standards for GymOps Platform.
  Use when working in any src/*/ module that contains
  React, Next.js, or TypeScript frontend code. Covers three apps -
  client dashboard, consumer PWA, and QR router.
version: 1.1.0
triggers:
  keywords:
    - frontend
    - react
    - next.js
    - typescript ui
    - vite
    - tailwind
  files:
    - src/clientdashboard/**
    - src/gymopspwa/**
    - src/gymops.qrrouter/**
    - modules/**/package.json
  intents:
    - implement_frontend_feature
    - fix_frontend_bug
    - update_ui_component
    - add_frontend_tests
    - review_frontend_architecture
---

# Zone Frontend Development Standards

Standards for frontend development across the GymOps Platform repo.

---

## Frontend Modules

| Module | Framework | UI Library | State/Data | Validation | Deploy | Pkg Mgr |
|---|---|---|---|---|---|---|
| src/components | React 18.3 + Vite 5.4 | MUI 5 + TailwindCSS 3.1 | Redux Toolkit 1.8 | Yup 1.4 | — | Yarn |
| zone.gymopspwa | Next.js 15.2 + React 19 | shadcn/ui + Radix + TailwindCSS 3.4 | TanStack Query 5.83 | Zod 3.24 | Cloudflare Workers | npm |
| zone.gymops.qrrouter | Next.js 15.5 + React 19.1 | shadcn/ui + TailwindCSS 4 | — | — | Cloudflare Workers | npm |

### Shared Stack

| Technology | All Apps | Purpose |
|---|---|---|
| TypeScript | 5.x | Type safety |
| Axios | ✓ | HTTP client |
| Vitest | ✓ | Testing framework |
| Testing Library | ✓ | Component testing |
| React Hook Form | 7.x | Form handling |
| Node.js | 18+ | Runtime |

---

## Quick Start

```bash
# Client Dashboard (React + Vite)
cd src/clientdashboard/src/Zone.ClientDashboard
yarn install && yarn dev         # http://localhost:3001
yarn test && yarn coverage       # Tests + coverage

# Consumer PWA (Next.js 15 + Cloudflare)
cd src/gymopspwa
npm install && npm run dev
npm run lint && npm run build
npm run deploy                   # Cloudflare Workers

# QR Router (Next.js 15 + Cloudflare)
cd src/gymops.qrrouter
npm install && npm run dev
npm run pre-deploy               # Lint + test
npm run deploy                   # Cloudflare Workers
```

### CI Dependency Installation

In CI/headless contexts (zone-dev, zone-qa workflows), **always** use deterministic install commands that fail if the lock file would change:

| Module | CI Install Command |
|---|---|
| src/components | `yarn install --frozen-lockfile` |
| zone.gymopspwa | `npm ci` |
| zone.gymops.qrrouter | `npm ci` |

**Never** run `npm install` or `yarn install` (without `--frozen-lockfile`) in CI — these regenerate lock files and create noisy diffs.

---

## Project Structure

### Client Dashboard (React SPA)

```
src/components/src/Zone.ClientDashboard/src/
├── api/calls/               # API call modules (40+)
├── auth/                    # AutoLogout, PersistLogin, RequireAuth, RequirePermission
├── components/              # 27 component categories (buttons, inputs, tables, etc.)
├── context/                 # React context providers
├── hooks/                   # useAxiosFetch, useAuth, useQuery
├── layout/                  # DashboardLayout, LoginLayout
├── pages/dashboard/         # transactions, settlements, disputes, merchants, wallet
├── redux/                   # store.ts + 15 Redux slices
├── routes/                  # Route config
└── utils/                   # enums, interfaces, types, validators
```

### Consumer PWA (Next.js App Router)

```
zone.gymopspwa/
├── app/                     # Next.js App Router
│   ├── layout.tsx           # Root (server) → ClientLayout (client)
│   ├── api/                 # 21 API routes
│   ├── login/               # Auth flow
│   ├── start-payment/       # Payment initiation
│   ├── confirm-payments/    # Payment confirmation
│   ├── history/             # Transaction history
│   └── terminals/           # Terminal management
├── components/
│   ├── ui/                  # shadcn/ui (51 components) — DO NOT MODIFY
│   ├── pwa/                 # PWA payment components (52)
│   ├── auth/                # Auth components (10)
│   └── ui-elements/         # Custom elements (10)
├── hooks/                   # 14 custom hooks
├── lib/                     # axiosConfig, firebase, pwa-config, utils
├── providers/               # QueryProvider, AuthProvider, ThemeProvider
├── middleware.ts             # Auth token injection + CORS + device detection
└── types/                   # TypeScript definitions
```

### QR Router (Next.js Deep Link Router)

```
zone.gymops.qrrouter/
├── app/
│   ├── [version]/[emvco]/           # Main QR deep link: /v1/{emvco}
│   │   ├── page.tsx                 # Server entry
│   │   └── DeepLinkClient.tsx       # Client routing logic
│   ├── redirect/[memberId]/[version]/[emvco]/  # Bank download flow
│   ├── _components/                 # app-picker, modal, download-link
│   ├── _config/                     # apps.ts (bank configs), download-links.ts
│   ├── _lib/                        # platform detection, analytics, sanitize
│   └── api/                         # assetlinks (Android) + AASA (iOS)
├── components/                      # shadcn/ui
└── public/apps/                     # Bank app icons
```

---

## Architecture Patterns

### State Management — Dashboard (Redux Toolkit)

```typescript
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

const authSlice = createSlice({
  name: 'auth',
  initialState: { user: null, isLoading: false },
  reducers: {
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
    },
  },
});

// Typed hooks
import { useAppSelector, useAppDispatch } from '@/redux/store';
const user = useAppSelector((state) => state.auth.user);
```

### Data Fetching — Dashboard (useAxiosFetch)

```typescript
const [{ data, isLoading, error }, doFetch] = useAxiosFetch<Response>({
  method: 'GET',
  url: '/api/transactions',
  params: { page: 1, limit: 20 },
});
```

Error formats handled automatically: `{ message }`, `{ Message }`, `{ responseMessage }`,
`{ detail }`, `{ errors: [{ message }] }`, `{ data: { errors: [{ errorMessage }] } }`

### Data Fetching — PWA (TanStack Query + Axios)

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/axiosConfig';

export function useTransactions() {
  return useQuery({
    queryKey: ['transactions'],
    queryFn: async () => {
      const { data } = await api.get('/api/transactions');
      return data;
    },
  });
}

export function useCreatePayment() {
  return useMutation({
    mutationFn: async (payment: PaymentRequest) => {
      const { data } = await api.post('/api/payments', payment);
      return data;
    },
  });
}
```

### Permission-Based Routing — Dashboard

```typescript
<Route
  element={
    <RequirePermission
      requiredPermissions={[PermissionsList?.['view-transactions']]}
    />
  }
>
  <Route path='transactions' element={<Transactions />} />
</Route>
```

### Product Context Propagation — Dashboard

All settlement, wallet, and reporting API calls **must** include the active `productId`:

| Endpoint Type | How to Send |
|---|---|
| GET (balance, history, reports) | Query param: `?productId=X` |
| POST (liquidation/withdrawal) | Body field: `{ productId }` |

This enables pggateway to route to the correct settlement API deployment per product.

---

## Form Handling

### Dashboard: React Hook Form + Yup

```typescript
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

const schema = yup.object({
  email: yup.string().email().required(),
  amount: yup.number().positive().required(),
});

const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: yupResolver(schema),
});
```

### PWA: React Hook Form + Zod

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  amount: z.number().min(1, 'Amount must be positive'),
  recipient: z.string().min(1, 'Recipient is required'),
});

type FormData = z.infer<typeof schema>;

const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
  resolver: zodResolver(schema),
});
```

---

## PWA-Specific Patterns

For middleware, client/server component conventions, custom hooks, Firebase Cloud Messaging, and Cloudflare Workers deployment, see [reference/pwa-patterns.md](reference/pwa-patterns.md).

---

## QR Router-Specific Patterns

For URL structure, adding new banks, input sanitization, host validation, and platform association files, see [reference/qr-router-patterns.md](reference/qr-router-patterns.md).

---

## Component Conventions

### Naming

| Element | Convention | Example |
|---|---|---|
| Components | PascalCase | `PrimaryButton.tsx` |
| Hooks | camelCase + `use` prefix | `useAxiosFetch.ts` |
| Utils | camelCase | `formatCurrency.ts` |
| Types/Interfaces | PascalCase | `TransactionType` |
| Enums | PascalCase | `Permission` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_FILE_SIZE` |

### File Structure

```
components/buttons/
├── PrimaryButton.tsx       # Component
├── PrimaryButton.test.tsx  # Tests (co-located)
├── index.ts                # Barrel export
└── types.ts                # Types (if complex)
```

---

## Styling Guide

### TailwindCSS vs MUI (Dashboard only)

| Use Case | Use |
|---|---|
| Layout, spacing, typography | TailwindCSS utilities |
| Complex data tables | MUI `DataGrid` |
| Date pickers | MUI `DatePicker` |
| Icons | MUI Icons |
| Custom buttons, inputs | TailwindCSS + custom |

### Dashboard Color Palette

```
primary-500:   #753bbd  (Purple — brand)
secondary-500: #12836f  (Green — success)
dark-500:      #160846  (Dark purple — backgrounds)
alert-500:     #ffc700  (Yellow — warnings)
completed-500: #2effa9  (Mint — success states)
active-500:    #28A44A  (Green — active status)
inactive-500:  #EFBA00  (Gold — inactive status)
```

### Classname Merging — `cn()` utility

```typescript
import { cn } from '@/utils/cn';   // or @/lib/utils

<button className={cn(
  'px-4 py-2 rounded',
  isActive && 'bg-primary-500',
  disabled && 'opacity-50 cursor-not-allowed'
)} />
```

---

## TypeScript Rules

```typescript
// ✅ Interface for object shapes (extendable)
interface User { id: string; name: string; }

// ✅ Type for unions/primitives
type Status = 'pending' | 'approved' | 'rejected';

// ✅ Generics for reusable types
interface ApiResponse<T> { data: T; message: string; success: boolean; }

// ❌ NEVER use `any` without justification
```

- Enums in `utils/enums/` (Dashboard) or inline (PWA/QR)
- Shared interfaces in `utils/interfaces/` (Dashboard) or `types/` (PWA)

---

## Testing

- Framework: **Vitest** + **Testing Library**
- Minimum coverage: **≥80%** (Dashboard). Run `yarn coverage`
- Tests co-located: `Component.test.tsx` or `__tests__/Component.test.tsx`

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

describe('PrimaryButton', () => {
  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<PrimaryButton label="Click" onClick={handleClick} />);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

QR Router: also run `npm run test:associations` to verify iOS/Android association files.

---

## Forbidden Actions

| ❌ Never | ✅ Instead |
|---|---|
| Use inline styles | TailwindCSS utilities |
| Use `any` without justification | Proper TypeScript types |
| Modify shadcn/ui components directly | Extend or wrap |
| Hardcode colors | Semantic theme palette |
| Skip error/loading states | Handle both in every async UI |
| Import from deep paths | Use `@/` path aliases |
| Commit `console.log` / hardcode URLs | Remove; use `NEXT_PUBLIC_*` env vars |
| Skip mobile testing / allow open redirects | Test iOS+Android; validate hosts |
