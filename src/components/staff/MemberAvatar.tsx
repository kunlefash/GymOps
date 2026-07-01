import { cn } from "@/lib/utils";
import type { MemberStatus } from "@/types";

interface MemberAvatarProps {
  initials: string;
  name: string;
  status: MemberStatus;
  size?: "sm" | "md";
  onClick?: () => void;
}

const ringColors: Record<MemberStatus, string> = {
  active: "ring-[#86EFAC]",
  expiring_soon: "ring-[#FCD34D]",
  expired: "ring-[#FCA5A5]",
};

export function MemberAvatar({
  initials,
  name,
  status,
  size = "md",
  onClick,
}: MemberAvatarProps) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center gap-1 min-w-[60px] focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-lg p-1"
      aria-label={`Open ${name}'s profile`}
    >
      <span
        className={cn(
          "rounded-full ring-2 bg-muted flex items-center justify-center font-semibold text-foreground",
          size === "md" ? "w-12 h-12 text-sm" : "w-9 h-9 text-xs",
          ringColors[status]
        )}
      >
        {initials}
      </span>
      <span className="text-xs text-muted-foreground truncate max-w-[56px] leading-tight">
        {name.split(" ")[0]}
      </span>
    </button>
  );
}
