//管理员api



import http from './http';
import type {
  User,
  DatasetSummary,
  PaginatedResult,
} from '@/types/api';

export function listUsers(params?: { skip?: number; limit?: number }) {
  return http.get<User[]>('/users', { params });
}

export function resetUserPassword(userId: string, newPassword: string) {
  return http.post(`/admin/users/${userId}/reset-password`, {
    new_password: newPassword,
  });
}

export function listDatasetsBrief(params?: { limit?: number; offset?: number }) {
  return http.get<PaginatedResult<DatasetSummary>>('/datasets', { params: { limit: 200, offset: 0, ...params } });
}
