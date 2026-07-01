"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { StatusBadge } from "@/components/ui/badge";
import { formatDate } from "@/lib/format";
import { mockMembers } from "@/lib/mock-data";
import { cn } from "@/lib/utils";
import type { Member } from "@/types";

type Step = "search" | "confirm" | "success";

export default function CheckInPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("search");
  const [query, setQuery] = useState("");
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const filtered = query
    ? mockMembers.filter(
        (m) =>
          m.name.toLowerCase().includes(query.toLowerCase()) ||
          m.phone.includes(query)
      )
    : mockMembers;

  function handleSelect(member: Member) {
    setSelectedMember(member);
    setStep("confirm");
  }

  function handleConfirm() {
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      setStep("success");
    }, 800);
  }

  if (step === "success" && selectedMember) {
    return (
      <div className="flex flex-col h-full items-center justify-center px-6 bg-background">
        <div className="text-center space-y-3 mb-8">
          <div className="w-16 h-16 rounded-full bg-[#DCFCE7] flex items-center justify-center mx-auto">
            <svg viewBox="0 0 24 24" className="w-8 h-8 fill-primary">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-foreground">Checked In!</h2>
          <p className="text-muted-foreground text-sm">
            {selectedMember.name} is in.
          </p>
        </div>

        <div className="w-full space-y-2 mb-8">
          <div className="flex justify-between text-sm bg-muted rounded-lg px-4 py-3">
            <span className="text-muted-foreground">Member</span>
            <span className="font-medium">{selectedMember.name}</span>
          </div>
          <div className="flex justify-between text-sm bg-muted rounded-lg px-4 py-3">
            <span className="text-muted-foreground">Membership</span>
            <StatusBadge status={selectedMember.status} />
          </div>
          <div className="flex justify-between text-sm bg-muted rounded-lg px-4 py-3">
            <span className="text-muted-foreground">Valid until</span>
            <span className="font-medium">{formatDate(selectedMember.expiryDate)}</span>
          </div>
          <div className="flex justify-between text-sm bg-muted rounded-lg px-4 py-3">
            <span className="text-muted-foreground">WhatsApp</span>
            <span className="font-medium text-primary flex items-center gap-1">
              <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 fill-current">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
              </svg>
              Confirmation sent
            </span>
          </div>
        </div>

        <div className="w-full space-y-3">
          <button
            onClick={() => {
              setStep("search");
              setQuery("");
              setSelectedMember(null);
            }}
            className="w-full h-14 rounded-lg bg-primary text-primary-foreground font-semibold text-base active:scale-[0.98] transition-transform"
          >
            Check In Another
          </button>
          <button
            onClick={() => router.push("/shift")}
            className="w-full h-14 rounded-lg border-2 border-border text-foreground font-semibold text-base active:bg-muted transition-colors"
          >
            Back to Shift
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center gap-3 px-4 pt-5 pb-3 border-b border-border">
        <button
          onClick={() =>
            step === "confirm" ? setStep("search") : router.back()
          }
          className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-muted -ml-2"
          aria-label="Go back"
        >
          <svg viewBox="0 0 24 24" className="w-5 h-5 fill-foreground">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
          </svg>
        </button>
        <h1 className="text-base font-semibold">
          {step === "search" ? "Check In Member" : "Confirm Check-In"}
        </h1>
      </header>

      {step === "search" && (
        <div className="flex flex-col flex-1 overflow-hidden">
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
                  onClick={() => handleSelect(member)}
                  className="w-full flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-muted active:bg-muted text-left"
                >
                  <span
                    className={cn(
                      "w-9 h-9 rounded-full bg-muted flex items-center justify-center text-xs font-semibold ring-2",
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
                  <StatusBadge status={member.status} />
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
      )}

      {step === "confirm" && selectedMember && (
        <div className="flex flex-col flex-1 px-4 pt-4">
          <div className="flex-1 space-y-3">
            <div className="flex items-center gap-4 p-4 bg-muted rounded-xl">
              <span
                className={cn(
                  "w-14 h-14 rounded-full bg-card flex items-center justify-center text-lg font-bold ring-2",
                  selectedMember.status === "active" && "ring-[#86EFAC]",
                  selectedMember.status === "expiring_soon" && "ring-[#FCD34D]",
                  selectedMember.status === "expired" && "ring-[#FCA5A5]"
                )}
              >
                {selectedMember.avatarInitials}
              </span>
              <div>
                <p className="font-semibold text-base">{selectedMember.name}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {selectedMember.phone}
                </p>
                <div className="mt-1">
                  <StatusBadge status={selectedMember.status} />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm px-1">
                <span className="text-muted-foreground">Plan</span>
                <span className="font-medium">{selectedMember.planName}</span>
              </div>
              <div className="flex justify-between text-sm px-1">
                <span className="text-muted-foreground">Valid until</span>
                <span className="font-medium">
                  {formatDate(selectedMember.expiryDate)}
                </span>
              </div>
            </div>

            {selectedMember.status === "expired" && (
              <div className="flex gap-2 p-3 rounded-lg bg-[#FEE2E2] border border-[#FCA5A5]">
                <svg
                  viewBox="0 0 24 24"
                  className="w-4 h-4 fill-[#B91C1C] flex-none mt-0.5"
                >
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
                </svg>
                <p className="text-xs text-[#B91C1C]">
                  Membership is expired. Consider recording a payment before
                  checking in.
                </p>
              </div>
            )}
          </div>

          <div className="pb-4 pt-2 space-y-3">
            <button
              onClick={handleConfirm}
              disabled={isSubmitting}
              className="w-full h-14 rounded-lg bg-primary text-primary-foreground font-semibold text-base flex items-center justify-center gap-2 disabled:opacity-70 active:scale-[0.98] transition-all"
            >
              {isSubmitting ? (
                <>
                  <span className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                  Checking in…
                </>
              ) : (
                "Confirm Check-In"
              )}
            </button>
            <button
              onClick={() => setStep("search")}
              className="w-full h-11 text-sm text-muted-foreground"
            >
              Choose a different member
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
