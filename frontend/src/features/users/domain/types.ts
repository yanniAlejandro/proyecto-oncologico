import type { Section, UserRole } from "@/shared/auth/roles";

export interface UserAccount {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  permissions: Section[];
}

export interface NewDoctorInput {
  email: string;
  password: string;
  full_name: string;
}

/** Solo las cuentas de médico activas se pueden desactivar (regla del backend). */
export const canDeactivate = (u: UserAccount) => u.is_active && u.role === "medico";
