# Step 03: Frontend Architecture

## Instructions
1. Define Next.js App Router structure
2. State management approach
3. Component hierarchy and design system integration

<template-output file="_bmad-output/planning-artifacts/architecture-{name}.md" section="frontend">
## 2. Frontend Architecture
### 2.1 Technology: Next.js 15 + TypeScript (strict)
### 2.2 Directory Structure
```
src/
├── app/                    # App Router pages
│   ├── (auth)/            # Auth group routes
│   ├── (dashboard)/       # Dashboard group routes
│   ├── api/               # API routes
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── components/
│   ├── ui/                # Base components (shadcn/ui)
│   └── features/          # Feature-specific components
├── lib/                   # Utilities, config
├── hooks/                 # Custom React hooks
├── services/              # API client layer
├── stores/                # State management (Zustand)
├── types/                 # Shared TypeScript types
└── styles/                # Global styles
```
### 2.3 State Management: Zustand (lightweight, TypeScript-native)
### 2.4 Routing: App Router with route groups
### 2.5 Styling: Tailwind CSS + shadcn/ui components
</template-output>
