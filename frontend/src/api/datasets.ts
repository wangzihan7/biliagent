//课题集api
import http from './http';
import type { DatasetSummary, PaginatedResult } from '@/types/api';

export type DatasetListItem = DatasetSummary;

export function listDatasets(params?: { keyword?: string; limit?: number; offset?: number }) {
  return http.get<PaginatedResult<DatasetListItem>>('/datasets', { params });
}

export interface CrawlTaskRequest {
  keyword: string;
  page: number;
  max_items: number;
  dataset_name: string;
  max_comments?: number | null;
  max_replies?: number | null;
  max_comment_pages?: number | null;
  max_danmaku?: number | null;
  user_id?: string;
}

export interface CrawlTaskResponse {
  task_id: string;
  status: string;
  keyword: string;
  page: number;
  max_items: number;
  video_count: number;
  comment_count: number;
  danmaku_count: number;
  created_at: string;
  updated_at: string;
}

export function createCrawlTask(payload: CrawlTaskRequest) {
  return http.post<CrawlTaskResponse>('/crawl', payload);
}

export function exportDataset(datasetId: string, format: 'jsonl' | 'csv') {
  return http.get<Blob>(`/datasets/${datasetId}/export`, {
    params: { format },
    responseType: 'blob',
  });
}

export function deleteDataset(datasetId: string) {
  return http.delete(`/datasets/${datasetId}`);
}
