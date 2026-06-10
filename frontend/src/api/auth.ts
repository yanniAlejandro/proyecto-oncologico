import { apiClient } from './client';
import type { User } from '../types';

export async function login(email: string, password: string): Promise<string> {
  const { data } = await apiClient.post<{ access_token: string }>('/auth/login', { email, password });
  return data.access_token;
}

export async function getMe(): Promise<User> {
  const { data } = await apiClient.get<User>('/auth/me');
  return data;
}
