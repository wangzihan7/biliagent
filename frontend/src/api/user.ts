//用户api
import http from './http';
import type { User, UserResponse } from '@/types/api';

// http 已配置基础路径 /api/v1
export function getMe() {
  return http.get<UserResponse>('/users/me');
}

export function updateMe(payload: { email?: string; old_password?: string; new_password?: string }) {
  return http.put<UserResponse>('/users/me', payload);
}
