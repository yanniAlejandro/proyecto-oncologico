export interface Disease {
  id: string;
  name: string;
  description: string | null;
}

export interface DiseaseInput {
  name: string;
  description: string;
}
