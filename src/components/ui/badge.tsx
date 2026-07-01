import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import type { MemberStatus } from "@/types";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "status";
  status?: MemberStatus;
}

const statusStyles: Record<MemberStatus, string> = {
  active: "bg-[#DCFCE7] text-[#15803D] border border-[#86EFAC]",
  expiring_soon: "bg-[#FEF3C7] text-[#B45309] border border-[#FCD34D]",
  expired: "bg-[#FEE2E2] text-[#B91C1C] border border-[#FCA5A5]",
};

const statusLabels: Record<MemberStatus, string> = {
  active: "ACTIVE",
  expiring_soon: "EXPIRING SOON",
  expired: "EXPIRED",
};

export function StatusBadge({ status }: { status: MemberStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wide",
        statusStyles[status]
      )}
    >
      {statusLabels[status]}
    </span>
  );
}

export function Badge({ className, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-muted text-muted-foreground",
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
