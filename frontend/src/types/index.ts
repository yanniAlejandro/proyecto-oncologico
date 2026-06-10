export type UserRole = 'administrador' | 'encargado' | 'medico';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
}

export interface News {
  id: string;
  title: string;
  summary: string | null;
  content: string;
  author_name: string | null;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface Disease {
  id: string;
  name: string;
  description: string | null;
}

export interface DiagnosticGuide {
  id: string;
  disease_id: string;
  disease_name: string;
  title: string;
  content: string;
  author_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface TreatmentProtocol {
  id: string;
  disease_id: string;
  disease_name: string;
  title: string;
  content: string;
  author_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  title: string;
  description: string | null;
  file_name: string;
  file_url: string;
  file_type: string | null;
  uploader_name: string | null;
  created_at: string;
}

export interface InterestLink {
  id: string;
  title: string;
  url: string;
  description: string | null;
  sort_order: number;
  is_active: boolean;
}

export interface ContactInfo {
  id: string;
  organization_name: string;
  address: string | null;
  phone: string | null;
  email: string | null;
  schedule: string | null;
  map_url: string | null;
}

export interface UserAccount {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}
