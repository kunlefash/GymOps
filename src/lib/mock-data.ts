import type { Member, MembershipPlan, StaffSession, TodaySummary } from "@/types";

export const mockSession: StaffSession = {
  staffId: "staff-1",
  staffName: "Amara Okonkwo",
  businessName: "IronBody Gym",
  syncStatus: "synced",
  pendingCount: 0,
};

export const mockPlans: MembershipPlan[] = [
  { id: "plan-1", name: "Monthly", price: 1500000, durationType: "monthly" },
  { id: "plan-2", name: "Weekly", price: 500000, durationType: "weekly" },
  { id: "plan-3", name: "Daily Drop-in", price: 100000, durationType: "daily" },
];

export const mockMembers: Member[] = [
  {
    id: "m-1",
    name: "Chidi Okeke",
    phone: "+2348012345678",
    status: "active",
    planName: "Monthly",
    expiryDate: new Date(Date.now() + 18 * 24 * 60 * 60 * 1000).toISOString(),
    avatarInitials: "CO",
  },
  {
    id: "m-2",
    name: "Fatima Bello",
    phone: "+2348098765432",
    status: "expiring_soon",
    planName: "Monthly",
    expiryDate: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
    avatarInitials: "FB",
  },
  {
    id: "m-3",
    name: "Tunde Adeyemi",
    phone: "+2348055512345",
    status: "expired",
    planName: "Weekly",
    expiryDate: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    avatarInitials: "TA",
  },
  {
    id: "m-4",
    name: "Ngozi Eze",
    phone: "+2348033344455",
    status: "active",
    planName: "Monthly",
    expiryDate: new Date(Date.now() + 25 * 24 * 60 * 60 * 1000).toISOString(),
    avatarInitials: "NE",
  },
  {
    id: "m-5",
    name: "Emeka Nwosu",
    phone: "+2348077788899",
    status: "active",
    planName: "Daily Drop-in",
    expiryDate: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString(),
    avatarInitials: "EN",
  },
];

export const mockTodaySummary: TodaySummary = {
  checkInsCount: 14,
  paymentsTotal: 7500000, // ₦75,000
  paymentsCount: 5,
  activeMembersOnShift: 14,
};

export const recentMemberIds = ["m-1", "m-2", "m-3", "m-4", "m-5"];
