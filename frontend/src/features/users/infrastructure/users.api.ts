import type { Transport } from "@/shared/api/transport";
import type { NewUserInput, UserAccount, UserChanges } from "../domain/types";

export function createUsersApi(t: Transport) {
  return {
    list: () => t.request<UserAccount[]>("GET", "/users"),
    create: (input: NewUserInput) => t.request<UserAccount>("POST", "/users", { json: input }),
    update: (id: string, changes: UserChanges) => t.request<UserAccount>("PATCH", `/users/${id}`, { json: changes }),
  };
}
export type UsersApi = ReturnType<typeof createUsersApi>;
