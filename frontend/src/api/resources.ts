import { apiClient } from './client';
import type {
  ContactInfo,
  DiagnosticGuide,
  Disease,
  Document,
  InterestLink,
  News,
  TreatmentProtocol,
  UserAccount,
} from '../types';

export const newsApi = {
  list: (search?: string) => apiClient.get<News[]>('/news', { params: { search } }).then((r) => r.data),
  listManage: (search?: string) => apiClient.get<News[]>('/news/manage', { params: { search } }).then((r) => r.data),
  create: (payload: Partial<News>) => apiClient.post<News>('/news', payload).then((r) => r.data),
  update: (id: string, payload: Partial<News>) => apiClient.put<News>(`/news/${id}`, payload).then((r) => r.data),
  remove: (id: string) => apiClient.delete(`/news/${id}`),
};

export const diseasesApi = {
  list: (search?: string) => apiClient.get<Disease[]>('/diseases', { params: { search } }).then((r) => r.data),
  create: (payload: { name: string; description?: string }) =>
    apiClient.post<Disease>('/diseases', payload).then((r) => r.data),
};

export const guidesApi = {
  list: (search?: string) =>
    apiClient.get<DiagnosticGuide[]>('/diagnostic-guides', { params: { search } }).then((r) => r.data),
  get: (id: string) => apiClient.get<DiagnosticGuide>(`/diagnostic-guides/${id}`).then((r) => r.data),
  create: (payload: { disease_id: string; title: string; content: string }) =>
    apiClient.post<DiagnosticGuide>('/diagnostic-guides', payload).then((r) => r.data),
  update: (id: string, payload: Partial<{ disease_id: string; title: string; content: string }>) =>
    apiClient.put<DiagnosticGuide>(`/diagnostic-guides/${id}`, payload).then((r) => r.data),
  remove: (id: string) => apiClient.delete(`/diagnostic-guides/${id}`),
};

export const protocolsApi = {
  list: (search?: string) =>
    apiClient.get<TreatmentProtocol[]>('/treatment-protocols', { params: { search } }).then((r) => r.data),
  get: (id: string) => apiClient.get<TreatmentProtocol>(`/treatment-protocols/${id}`).then((r) => r.data),
  create: (payload: { disease_id: string; title: string; content: string }) =>
    apiClient.post<TreatmentProtocol>('/treatment-protocols', payload).then((r) => r.data),
  update: (id: string, payload: Partial<{ disease_id: string; title: string; content: string }>) =>
    apiClient.put<TreatmentProtocol>(`/treatment-protocols/${id}`, payload).then((r) => r.data),
  remove: (id: string) => apiClient.delete(`/treatment-protocols/${id}`),
};

export const documentsApi = {
  list: (search?: string) => apiClient.get<Document[]>('/documents', { params: { search } }).then((r) => r.data),
  create: (payload: { title: string; description?: string; file_name: string; file_url: string; file_type?: string }) =>
    apiClient.post<Document>('/documents', payload).then((r) => r.data),
  remove: (id: string) => apiClient.delete(`/documents/${id}`),
};

export const linksApi = {
  list: () => apiClient.get<InterestLink[]>('/interest-links').then((r) => r.data),
};

export const contactApi = {
  get: () => apiClient.get<ContactInfo>('/contact').then((r) => r.data),
};

export const usersApi = {
  list: () => apiClient.get<UserAccount[]>('/users').then((r) => r.data),
  create: (payload: { email: string; password: string; full_name: string }) =>
    apiClient.post<UserAccount>('/users', { ...payload, role: 'medico' }).then((r) => r.data),
  deactivate: (id: string) => apiClient.delete(`/users/${id}`),
};
