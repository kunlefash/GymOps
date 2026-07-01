import { cn } from "@/lib/utils";
import type { SyncStatus } from "@/types";

interface SyncChipProps {
  status: SyncStatus;
  pendingCount?: number;
}

export function SyncChip({ status, pendingCount = 0 }: SyncChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium",
        status === "synced" && "bg-[#DCFCE7] text-[#15803D]",
        status === "pending" && "bg-[#FEF3C7] text-[#B45309]",
        status === "failed" && "bg-[#FEE2E2] text-[#B91C1C]"
      )}
    >
      <span
        className={cn(
          "w-1.5 h-1.5 rounded-full",
          status === "synced" && "bg-[#15803D]",
          status === "pending" && "bg-[#B45309]",
          status === "failed" && "bg-[#B91C1C]"
        )}
      />
      {status === "synced" && "Synced ✓"}
      {status === "pending" && `${pendingCount} pending`}
      {status === "failed" && "Sync failed"}
    </span>
  );
}
