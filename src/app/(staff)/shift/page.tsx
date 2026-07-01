"use client";

import Link from "next/link";
import { SyncChip } from "@/components/staff/SyncChip";
import { MemberAvatar } from "@/components/staff/MemberAvatar";
import { StatusBadge } from "@/components/ui/badge";
import { formatNaira } from "@/lib/format";
import {
  mockSession,
  mockMembers,
  mockTodaySummary,
  recentMemberIds,
} from "@/lib/mock-data";

export default function ShiftHomePage() {
  const recentMembers = recentMemberIds
    .map((id) => mockMembers.find((m) => m.id === id))
    .filter(Boolean) as typeof mockMembers;

  return (
    <div className="flex flex-col h-full">
      {/* Top bar */}
      <header className="flex items-start justify-between px-4 pt-5 pb-3">
        <div>
          <h1 className="text-base font-semibold text-foreground leading-tight">
            {mockSession.businessName}
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {mockSession.staffName}
          </p>
        </div>
        <SyncChip
          status={mockSession.syncStatus}
          pendingCount={mockSession.pendingCount}
        />
      </header>

      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-5">
        {/* Recent members */}
        <section aria-label="Recent members">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
            Recent Members
          </p>
          <div className="flex gap-1 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-none">
            {recentMembers.map((member) => (
              <MemberAvatar
                key={member.id}
                initials={member.avatarInitials}
                name={member.name}
                status={member.status}
              />
            ))}
          </div>
        </section>

        {/* 3 primary action buttons — the entire shift UI lives here */}
        <section aria-label="Shift actions" className="space-y-3">
          <Link
            href="/shift/payment"
            className="flex items-center gap-3 w-full h-14 px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-base shadow-sm active:scale-[0.98] transition-transform"
          >
            <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current flex-none">
              <path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z" />
            </svg>
            Record Payment
          </Link>

          <Link
            href="/shift/checkin"
            className="flex items-center gap-3 w-full h-14 px-4 rounded-lg border-2 border-primary text-primary bg-card font-semibold text-base active:bg-[#DCFCE7] transition-colors"
          >
            <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current flex-none">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
            </svg>
            Check In Member
          </Link>

          <Link
            href="/shift/member"
            className="flex items-center gap-3 w-full h-14 px-4 rounded-lg border-2 border-border text-foreground bg-card font-semibold text-base active:bg-muted transition-colors"
          >
            <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current flex-none">
              <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
            </svg>
            Find Member
          </Link>
        </section>

        {/* Today's summary */}
        <section aria-label="Today's summary">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
            Today
          </p>
          <div className="grid grid-cols-3 gap-2">
            <SummaryCard
              label="Check-ins"
              value={String(mockTodaySummary.checkInsCount)}
            />
            <SummaryCard
              label="Payments"
              value={formatNaira(mockTodaySummary.paymentsTotal)}
              subValue={`${mockTodaySummary.paymentsCount} transactions`}
            />
            <SummaryCard
              label="Active"
              value={String(mockTodaySummary.activeMembersOnShift)}
              subValue="members"
            />
          </div>
        </section>

        {/* Expiring soon alert */}
        {mockMembers.some((m) => m.status === "expiring_soon") && (
          <section aria-label="Expiry alerts">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
              Expiring Soon
            </p>
            <div className="space-y-2">
              {mockMembers
                .filter((m) => m.status === "expiring_soon")
                .map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-[#FEF3C7] border border-[#FCD34D]"
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-8 h-8 rounded-full bg-[#FCD34D] flex items-center justify-center text-xs font-semibold text-[#B45309]">
                        {member.avatarInitials}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-[#92400E]">
                          {member.name}
                        </p>
                        <p className="text-xs text-[#B45309]">{member.planName}</p>
                      </div>
                    </div>
                    <StatusBadge status={member.status} />
                  </div>
                ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  subValue,
}: {
  label: string;
  value: string;
  subValue?: string;
}) {
  return (
    <div className="flex flex-col gap-0.5 bg-card rounded-lg p-3 border border-border">
      <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
        {label}
      </span>
      <span className="text-lg font-bold text-foreground leading-tight">{value}</span>
      {subValue && (
        <span className="text-[10px] text-muted-foreground">{subValue}</span>
      )}
    </div>
  );
}
