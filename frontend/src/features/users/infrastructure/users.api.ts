import type { Transport } from "@/shared/api/transport";
import type { NewDoctorInput, UserAccount } from "../domain/types";

export function createUsersApi(t: Transport) {
  return {
    list: () => t.request<UserAccount[]>("GET", "/users"),
    createDoctor: (input: NewDoctorInput) =>
      t.request<UserAccount>("POST", "/users", { json: { ...input, role: "medico" } }),
    deactivate: (id: string) => t.request<void>("DELETE", `/users/${id}`),
  };
}
export type UsersApi = ReturnType<typeof createUsersApi>;
