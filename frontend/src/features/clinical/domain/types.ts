/** Guías de diagnóstico y protocolos de tratamiento comparten forma y pantalla. */

export type ClinicalKind = "guide" | "protocol";

export interface ClinicalDoc {
  id: string;
  disease_id: string;
  disease_name: string;
  title: string;
  content: string;
  author_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClinicalInput {
  disease_id: string;
  title: string;
  content: string;
}

export const CLINICAL_COPY = {
  guide: {
    endpoint: "/diagnostic-guides",
    queryKey: "diagnostic-guides",
    title: "Guías de Diagnóstico",
    subtitle: "Protocolos y criterios diagnósticos por enfermedad",
    newLabel: "+ Nueva guía",
    createTitle: "Nueva guía de diagnóstico",
    editTitle: "Editar guía",
    loading: "Cargando guías...",
    empty: "No se encontraron guías.",
    loadError: "Error al cargar las guías. Verifica tu sesión.",
    noun: "la guía",
  },
  protocol: {
    endpoint: "/treatment-protocols",
    queryKey: "treatment-protocols",
    title: "Protocolos de Tratamiento",
    subtitle: "Protocolos terapéuticos institucionales — acceso público",
    newLabel: "+ Nuevo protocolo",
    createTitle: "Nuevo protocolo de tratamiento",
    editTitle: "Editar protocolo",
    loading: "Cargando protocolos...",
    empty: "No se encontraron protocolos.",
    loadError: "Error al cargar los protocolos.",
    noun: "el protocolo",
  },
} as const satisfies Record<ClinicalKind, Record<string, string>>;
