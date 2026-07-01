"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  {
    href: "/shift",
    label: "Home",
    icon: (active: boolean) => (
      <svg
        viewBox="0 0 24 24"
        className={cn("w-6 h-6", active ? "fill-primary" : "fill-muted-foreground")}
      >
        <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" />
      </svg>
    ),
  },
  {
    href: "/shift/member",
    label: "Members",
    icon: (active: boolean) => (
      <svg
        viewBox="0 0 24 24"
        className={cn("w-6 h-6", active ? "fill-primary" : "fill-muted-foreground")}
      >
        <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
      </svg>
    ),
  },
  {
    href: "/shift/payment",
    label: "Payments",
    icon: (active: boolean) => (
      <svg
        viewBox="0 0 24 24"
        className={cn("w-6 h-6", active ? "fill-primary" : "fill-muted-foreground")}
      >
        <path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z" />
      </svg>
    ),
  },
  {
    href: "/shift/checkin",
    label: "Check-in",
    icon: (active: boolean) => (
      <svg
        viewBox="0 0 24 24"
        className={cn("w-6 h-6", active ? "fill-primary" : "fill-muted-foreground")}
      >
        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
      </svg>
    ),
  },
] as const;

export default function StaffLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex flex-col h-dvh bg-background max-w-md mx-auto">
      <main className="flex-1 overflow-y-auto">{children}</main>

      {/* Bottom nav — 4 tabs, 44px+ touch targets */}
      <nav
        className="flex-none border-t border-border bg-card"
        aria-label="Staff navigation"
      >
        <div className="flex items-stretch h-14">
          {NAV_ITEMS.map(({ href, label, icon }) => {
            const active =
              href === "/shift" ? pathname === "/shift" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex-1 flex flex-col items-center justify-center gap-0.5 text-[10px] font-medium",
                  active ? "text-primary" : "text-muted-foreground"
                )}
                aria-current={active ? "page" : undefined}
              >
                {icon(active)}
                {label}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
