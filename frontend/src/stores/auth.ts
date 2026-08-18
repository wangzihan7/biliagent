import { defineStore } from 'pinia';
import type { LoginResponse, UserRole, UserResponse } from '@/types/api';

interface AuthState {
  userId: string;
  userName: string;
  email: string;
  role: UserRole | '';
  token: string;
}

const STORAGE_KEY = 'biliagent_auth';

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    userId: '',
    userName: '',
    email: '',
    role: '',
    token: '',
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    isAdmin: (state) => state.role === 'admin',
  },
  actions: {
    setAuth(payload: LoginResponse) {
      this.userId = payload.user_id;
      this.userName = payload.user_name;
      this.email = '';
      this.role = payload.role;
      this.token = payload.token;
      this.persist();
    },
    setUser(user: UserResponse) {
      this.userName = user.user_name;
      this.userId = user.user_id;
      this.email = user.email || '';
      if (user.role) this.role = user.role;
      this.persist();
    },
    clear() {
      this.userId = '';
      this.userName = '';
      this.role = '';
      this.token = '';
      localStorage.removeItem(STORAGE_KEY);
    },
    persist() {
      const raw = JSON.stringify({
        userId: this.userId,
        userName: this.userName,
        email: this.email,
        role: this.role,
        token: this.token,
      });
      localStorage.setItem(STORAGE_KEY, raw);
    },
    restore() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return;
        const parsed = JSON.parse(raw) as AuthState;
        this.userId = parsed.userId;
        this.userName = parsed.userName;
        this.email = parsed.email || '';
        this.role = parsed.role;
        this.token = parsed.token;
      } catch {
        // ignore
      }
    },
    logout() {
      this.clear();
    },
  },
});
