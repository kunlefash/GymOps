"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { StatusBadge } from "@/components/ui/badge";
import { formatDate, formatNaira, daysUntilExpiry } from "@/lib/format";
import { mockMembers } from "@/lib/mock-data";
import { cn } from "@/lib/utils";
import type { Member } from "@/types";

export default function FindMemberPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);

  const filtered = query
    ? mockMembers.filter(
        (m) =>
          m.name.toLowerCase().includes(query.toLowerCase()) ||
          m.phone.includes(query)
      )
    : mockMembers;

  if (selectedMember) {
    return (
      <MemberProfile
        member={selectedMember}
        onBack={() => setSelectedMember(null)}
        onRecordPayment={() => router.push("/shift/payment")}
        onCheckIn={() => router.push("/shift/checkin")}
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      <header className="flex items-center gap-3 px-4 pt-5 pb-3 border-b border-border">
        <button
          onClick={() => router.back()}
          className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-muted -ml-2"
          aria-label="Go back"
        >
          <svg viewBox="0 0 24 24" className="w-5 h-5 fill-foreground">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
          </svg>
        </button>
        <h1 className="text-base font-semibold">Find Member</h1>
      </header>

      <div className="px-4 pt-3 pb-2">
        <div className="relative">
          <svg
            viewBox="0 0 24 24"
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 fill-muted-foreground"
          >
            <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
          </svg>
          <input
            type="search"
            placeholder="Search by name or phone"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-9 pr-4 h-11 rounded-lg border border-border bg-muted text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            autoFocus
          />
        </div>
      </div>

      <ul className="flex-1 overflow-y-auto px-4 space-y-1 pb-4">
        {filtered.map((member) => (
          <li key={member.id}>
            <button
              onClick={() => setSelectedMember(member)}
              className="w-full flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-muted active:bg-muted text-left"
            >
              <span
                className={cn(
                  "w-9 h-9 rounded-full bg-muted flex items-center justify-center text-xs font-semibold ring-2 flex-none",
                  member.status === "active" && "ring-[#86EFAC]",
                  member.status === "expiring_soon" && "ring-[#FCD34D]",
                  member.status === "expired" && "ring-[#FCA5A5]"
                )}
              >
                {member.avatarInitials}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold truncate">{member.name}</p>
                <p className="text-xs text-muted-foreground">{member.phone}</p>
              </div>
              <div className="flex flex-col items-end gap-1">
                <StatusBadge status={member.status} />
                <span className="text-[10px] text-muted-foreground">
                  {member.planName}
                </span>
              </div>
            </button>
          </li>
        ))}
        {filtered.length === 0 && (
          <li className="py-10 text-center text-sm text-muted-foreground">
            No members found
          </li>
        )}
      </ul>
    </div>
  );
}

function MemberProfile({
  member,
  onBack,
  onRecordPayment,
  onCheckIn,
}: {
  member: Member;
  onBack: () => void;
  onRecordPayment: () => void;
  onCheckIn: () => void;
}) {
  const days = daysUntilExpiry(member.expiryDate);

  return (
    <div className="flex flex-col h-full">
      <header className="flex items-center gap-3 px-4 pt-5 pb-3 border-b border-border">
        <button
          onClick={onBack}
          className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-muted -ml-2"
          aria-label="Go back"
        >
          <svg viewBox="0 0 24 24" className="w-5 h-5 fill-foreground">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
          </svg>
        </button>
        <h1 className="text-base font-semibold">Member Profile</h1>
      </header>

      <div className="flex-1 overflow-y-auto px-4 pt-4 pb-4 space-y-4">
        {/* Identity card */}
        <div className="flex items-center gap-4 p-4 bg-muted rounded-xl">
          <span
            className={cn(
              "w-14 h-14 rounded-full bg-card flex items-center justify-center text-lg font-bold ring-2",
              member.status === "active" && "ring-[#86EFAC]",
              member.status === "expiring_soon" && "ring-[#FCD34D]",
              member.status === "expired" && "ring-[#FCA5A5]"
            )}
          >
            {member.avatarInitials}
          </span>
          <div>
            <p className="font-bold text-lg leading-tight">{member.name}</p>
            <p className="text-sm text-muted-foreground">{member.phone}</p>
            <div className="mt-1.5">
              <StatusBadge status={member.status} />
            </div>
          </div>
        </div>

        {/* Membership details */}
        <div className="rounded-xl border border-border overflow-hidden">
          <div className="px-4 py-2.5 bg-muted/50 border-b border-border">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Membership
            </p>
          </div>
          <div className="divide-y divide-border">
            <Row label="Plan" value={member.planName} />
            <Row label="Expires" value={formatDate(member.expiryDate)} />
            <Row
              label="Days remaining"
              value={
                days > 0 ? `${days} days` : days === 0 ? "Today" : "Expired"
              }
              valueClass={
                days <= 0
                  ? "text-destructive font-semibold"
                  : days <= 7
                  ? "text-[#B45309] font-semibold"
                  : "text-foreground"
              }
            />
          </div>
        </div>

        {/* Expired warning */}
        {member.status === "expired" && (
          <div className="flex gap-2 p-3 rounded-lg bg-[#FEE2E2] border border-[#FCA5A5]">
            <svg
              viewBox="0 0 24 24"
              className="w-4 h-4 fill-[#B91C1C] flex-none mt-0.5"
            >
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
            </svg>
            <p className="text-xs text-[#B91C1C]">
              Membership expired. Record a payment to renew access.
            </p>
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="px-4 pb-4 pt-2 border-t border-border space-y-3">
        <button
          onClick={onRecordPayment}
          className="w-full h-14 rounded-lg bg-primary text-primary-foreground font-semibold text-base active:scale-[0.98] transition-transform"
        >
          Record Payment
        </button>
        <button
          onClick={onCheckIn}
          className="w-full h-14 rounded-lg border-2 border-primary text-primary font-semibold text-base active:bg-[#DCFCE7] transition-colors"
        >
          Check In
        </button>
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="flex justify-between items-center px-4 py-3">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={cn("text-sm font-medium text-foreground", valueClass)}>
        {value}
      </span>
    </div>
  );
}
