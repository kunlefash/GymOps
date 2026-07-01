"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { MemberAvatar } from "@/components/staff/MemberAvatar";
import { StatusBadge } from "@/components/ui/badge";
import { formatNaira, formatDate } from "@/lib/format";
import { mockMembers, mockPlans } from "@/lib/mock-data";
import { cn } from "@/lib/utils";
import type { Member, MembershipPlan, PaymentMethod } from "@/types";

type Step = "select-member" | "payment-drawer" | "success";

export default function RecordPaymentPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("select-member");
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<MembershipPlan>(mockPlans[0]);
  const [method, setMethod] = useState<PaymentMethod>("cash");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Simulate payment submission
  function handleConfirmPayment() {
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      setStep("success");
    }, 1200);
  }

  // Calculate new expiry for display
  function getNewExpiry(): string {
    const base = new Date();
    if (selectedPlan.durationType === "monthly")
      base.setMonth(base.getMonth() + 1);
    else if (selectedPlan.durationType === "weekly")
      base.setDate(base.getDate() + 7);
    else base.setDate(base.getDate() + 1);
    return base.toISOString();
  }

  if (step === "success" && selectedMember) {
    return (
      <SuccessScreen
        member={selectedMember}
        plan={selectedPlan}
        method={method}
        newExpiry={getNewExpiry()}
        onCheckIn={() => router.push("/shift/checkin")}
        onDone={() => router.push("/shift")}
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center gap-3 px-4 pt-5 pb-3 border-b border-border">
        <button
          onClick={() => (step === "payment-drawer" ? setStep("select-member") : router.back())}
          className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-muted -ml-2"
          aria-label="Go back"
        >
          <svg viewBox="0 0 24 24" className="w-5 h-5 fill-foreground">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
          </svg>
        </button>
        <h1 className="text-base font-semibold">
          {step === "select-member" ? "Select Member" : "Record Payment"}
        </h1>
      </header>

      {step === "select-member" && (
        <MemberSelectStep
          onSelect={(member) => {
            setSelectedMember(member);
            setStep("payment-drawer");
          }}
        />
      )}

      {step === "payment-drawer" && selectedMember && (
        <PaymentDrawer
          member={selectedMember}
          plans={mockPlans}
          selectedPlan={selectedPlan}
          method={method}
          isSubmitting={isSubmitting}
          onPlanChange={setSelectedPlan}
          onMethodChange={setMethod}
          onConfirm={handleConfirmPayment}
        />
      )}
    </div>
  );
}

// ── Tap 1: Select member ──────────────────────────────────────────────────────
function MemberSelectStep({ onSelect }: { onSelect: (m: Member) => void }) {
  const [query, setQuery] = useState("");

  const filtered = query
    ? mockMembers.filter(
        (m) =>
          m.name.toLowerCase().includes(query.toLowerCase()) ||
          m.phone.includes(query)
      )
    : mockMembers;

  return (
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
              onClick={() => onSelect(member)}
              className="w-full flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-muted active:bg-muted transition-colors text-left"
            >
              <MemberAvatar
                initials={member.avatarInitials}
                name={member.name}
                status={member.status}
                size="sm"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-foreground truncate">
                  {member.name}
                </p>
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
  );
}

// ── Tap 2+3: Payment drawer ───────────────────────────────────────────────────
function PaymentDrawer({
  member,
  plans,
  selectedPlan,
  method,
  isSubmitting,
  onPlanChange,
  onMethodChange,
  onConfirm,
}: {
  member: Member;
  plans: MembershipPlan[];
  selectedPlan: MembershipPlan;
  method: PaymentMethod;
  isSubmitting: boolean;
  onPlanChange: (p: MembershipPlan) => void;
  onMethodChange: (m: PaymentMethod) => void;
  onConfirm: () => void;
}) {
  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Member context */}
      <div className="px-4 py-3 bg-muted/50 border-b border-border">
        <div className="flex items-center gap-3">
          <span className="w-10 h-10 rounded-full bg-muted ring-2 ring-[#86EFAC] flex items-center justify-center text-sm font-semibold">
            {member.avatarInitials}
          </span>
          <div>
            <p className="text-sm font-semibold">{member.name}</p>
            <StatusBadge status={member.status} />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pt-4 pb-2 space-y-5">
        {/* Plan selector */}
        <fieldset>
          <legend className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
            Plan
          </legend>
          <div className="space-y-2">
            {plans.map((plan) => (
              <button
                key={plan.id}
                onClick={() => onPlanChange(plan)}
                className={cn(
                  "w-full flex items-center justify-between px-4 h-14 rounded-lg border-2 text-sm font-medium transition-colors",
                  selectedPlan.id === plan.id
                    ? "border-primary bg-[#DCFCE7] text-[#15803D]"
                    : "border-border bg-card text-foreground"
                )}
              >
                <span>{plan.name}</span>
                <span data-amount className={cn(selectedPlan.id === plan.id ? "text-[#15803D]" : "text-foreground")}>
                  {formatNaira(plan.price)}
                </span>
              </button>
            ))}
          </div>
        </fieldset>

        {/* Payment method toggle */}
        <fieldset>
          <legend className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
            Payment Method
          </legend>
          <div className="flex rounded-lg border border-border overflow-hidden">
            {(["cash", "bank_transfer"] as PaymentMethod[]).map((m) => (
              <button
                key={m}
                onClick={() => onMethodChange(m)}
                className={cn(
                  "flex-1 h-11 text-sm font-medium transition-colors",
                  method === m
                    ? "bg-primary text-primary-foreground"
                    : "bg-card text-muted-foreground"
                )}
              >
                {m === "cash" ? "Cash" : "Bank Transfer"}
              </button>
            ))}
          </div>
        </fieldset>

        {/* Amount summary */}
        <div className="flex items-center justify-between px-4 py-3 rounded-lg bg-muted">
          <span className="text-sm text-muted-foreground">Total</span>
          <span data-amount className="text-foreground">
            {formatNaira(selectedPlan.price)}
          </span>
        </div>
      </div>

      {/* CTA — pinned to bottom */}
      <div className="px-4 pb-4 pt-2 border-t border-border">
        <button
          onClick={onConfirm}
          disabled={isSubmitting}
          className="w-full h-14 rounded-lg bg-primary text-primary-foreground font-semibold text-base flex items-center justify-center gap-2 disabled:opacity-70 active:scale-[0.98] transition-all"
        >
          {isSubmitting ? (
            <>
              <span className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
              Sending receipt…
            </>
          ) : (
            <>
              Record Payment · {formatNaira(selectedPlan.price)}
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// ── Success screen ────────────────────────────────────────────────────────────
function SuccessScreen({
  member,
  plan,
  method,
  newExpiry,
  onCheckIn,
  onDone,
}: {
  member: Member;
  plan: MembershipPlan;
  method: PaymentMethod;
  newExpiry: string;
  onCheckIn: () => void;
  onDone: () => void;
}) {
  return (
    <div className="flex flex-col h-full bg-primary items-center justify-center px-6 text-primary-foreground">
      {/* Hero */}
      <div className="text-center space-y-2 mb-8">
        <div className="w-16 h-16 rounded-full bg-primary-foreground/20 flex items-center justify-center mx-auto mb-4">
          <svg viewBox="0 0 24 24" className="w-8 h-8 fill-primary-foreground">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold">{member.name}</h2>
        <p data-amount className="text-primary-foreground">
          {formatNaira(plan.price)}
        </p>
        <p className="text-primary-foreground/90 font-medium flex items-center justify-center gap-1">
          <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
          </svg>
          Receipt sent ✓
        </p>
      </div>

      {/* Details */}
      <div className="w-full space-y-2 mb-10">
        <div className="flex justify-between text-sm bg-primary-foreground/10 rounded-lg px-4 py-3">
          <span className="text-primary-foreground/80">Plan</span>
          <span className="font-medium">{plan.name}</span>
        </div>
        <div className="flex justify-between text-sm bg-primary-foreground/10 rounded-lg px-4 py-3">
          <span className="text-primary-foreground/80">Method</span>
          <span className="font-medium capitalize">
            {method === "bank_transfer" ? "Bank Transfer" : "Cash"}
          </span>
        </div>
        <div className="flex justify-between text-sm bg-primary-foreground/10 rounded-lg px-4 py-3">
          <span className="text-primary-foreground/80">Membership renewed ·</span>
          <span className="font-medium">Valid until {formatDate(newExpiry)}</span>
        </div>
      </div>

      {/* Exit CTAs */}
      <div className="w-full space-y-3">
        <button
          onClick={onCheckIn}
          className="w-full h-14 rounded-lg bg-primary-foreground text-primary font-semibold text-base active:scale-[0.98] transition-transform"
        >
          Check In {member.name.split(" ")[0]}
        </button>
        <button
          onClick={onDone}
          className="w-full h-14 rounded-lg border-2 border-primary-foreground/40 text-primary-foreground font-semibold text-base active:scale-[0.98] transition-transform"
        >
          Done
        </button>
      </div>
    </div>
  );
}
