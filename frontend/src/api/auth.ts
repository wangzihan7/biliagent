//认证api
import http from './http';
import type { LoginResponse, UserQuotaStatus } from '@/types/api';

// 用户名 + 密码登录
export function loginApi(data: { user_name: string; password: string }) {
  return http.post<LoginResponse>('/users/login', data);
}

export function registerApi(data: {
  user_name: string;
  password: string;
  role: 'user' | 'admin';
}) {
  return http.post('/users/register', data);
}

export function getMyQuotaStatus() {
  return http.get<UserQuotaStatus>('/users/me/quota');
}
