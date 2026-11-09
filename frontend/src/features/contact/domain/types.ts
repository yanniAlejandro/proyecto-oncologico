export interface ContactInfo {
  id: string;
  organization_name: string;
  address: string | null;
  phone: string | null;
  email: string | null;
  schedule: string | null;
  map_url: string | null;
}

export type ContactInput = Omit<ContactInfo, "id">;
