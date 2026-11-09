import type { Section, UserRole } from "@/shared/auth/roles";

export interface UserAccount {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  permissions: Section[];
}

export interface NewUserInput {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  permissions: Section[];
}

export interface UserChanges {
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
  permissions?: Section[];
  password?: string;
}

/** Salvaguardas del backend, para no ofrecer acciones que fallarían. */
export const isSelf = (u: UserAccount, currentUserId: string) => u.id === currentUserId;
