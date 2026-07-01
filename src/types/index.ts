export type MemberStatus = "active" | "expiring_soon" | "expired";
export type PaymentMethod = "cash" | "bank_transfer";
export type SyncStatus = "synced" | "pending" | "failed";

export interface Member {
  id: string;
  name: string;
  phone: string;
  status: MemberStatus;
  planName: string;
  expiryDate: string; // ISO date string
  avatarInitials: string;
}

export interface Payment {
  id: string;
  memberId: string;
  memberName: string;
  amount: number; // kobo
  method: PaymentMethod;
  planName: string;
  newExpiryDate: string;
  createdAt: string;
  receiptSent: boolean;
}

export interface CheckIn {
  id: string;
  memberId: string;
  memberName: string;
  timestamp: string;
}

export interface StaffSession {
  staffId: string;
  staffName: string;
  businessName: string;
  syncStatus: SyncStatus;
  pendingCount: number;
}

export interface TodaySummary {
  checkInsCount: number;
  paymentsTotal: number; // kobo
  paymentsCount: number;
  activeMembersOnShift: number;
}

export interface MembershipPlan {
  id: string;
  name: string;
  price: number; // kobo
  durationType: "daily" | "weekly" | "monthly";
}
