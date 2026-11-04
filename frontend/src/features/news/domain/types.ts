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

export interface NewsInput {
  title: string;
  summary: string;
  content: string;
  is_published: boolean;
}
