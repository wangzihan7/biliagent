//日志api
import http from './http';
import type { CrawlLogItem, PaginatedResult, QueryLogItem } from '@/types/api';

export function getMyCrawlLogs(params?: { limit?: number; offset?: number }) {
  return http.get<PaginatedResult<CrawlLogItem>>('/logs/crawl', { params });
}

export function getAdminCrawlLogs(params?: { limit?: number; offset?: number }) {
  return http.get<PaginatedResult<CrawlLogItem>>('/admin/crawl-logs', { params });
}

export function getMyQueryLogs(params?: { limit?: number }) {
  return http.get<QueryLogItem[]>('/logs/query', { params });
}

export function getAdminQueryLogs(params?: { limit?: number }) {
  return http.get<QueryLogItem[]>('/admin/query-logs', { params });
}
