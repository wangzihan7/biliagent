//封装http请求，调用后端api
import axios from 'axios';
import type {
  AxiosError,
  AxiosInstance,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import { useAuthStore } from '@/stores/auth';

const instance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  timeout: 30000,
});

// Inject Authorization header when token exists
instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const auth = useAuthStore();
  if (auth.token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${auth.token}`;
  }
  return config;
});

// Basic error logging; you can extend this as needed
instance.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    // Optionally handle 401 globally here
    return Promise.reject(error);
  },
);

export default instance;
