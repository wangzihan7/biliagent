// Shared API-level types inferred from docs/frontend_ai_guide.md

export type UserRole = 'user' | 'admin';

export interface LoginResponse {
  user_id: string;
  user_name: string;
  role: UserRole;
  token: string;
}

export interface User {
  user_id: string;
  user_name: string;
  email?: string | null;
  role: UserRole;
  create_time?: string;
}

// Topic related types
export interface Topic {
  topic_id: string;
  name: string;
  topic_type: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface TopicListItem extends Topic {
  // Optional aggregated fields that backend may provide later
  conversations_count?: number;
  datasets_count?: number;
  reports_count?: number;
}

export interface ConversationSummary {
  conversation_id: string;
  user_id: string;
  conversation_name: string;
  topic_id?: string;
  create_time: string;
  update_time: string;
}

export interface DatasetSummary {
  dataset_id: string;
  name: string;
  keyword: string;
  video_count: number;
  comment_count: number;
  danmaku_count: number;
  created_at: string;
  updated_at?: string;
  user_id?: string;
  task_id?: string | null;
  data_path?: string | null;
}

export interface TopicDetail extends Topic {
  conversations: ConversationSummary[];
  datasets: DatasetSummary[];
}

export interface TopicReportTotals {
  datasets?: number;
  videos?: number;
  comments?: number;
  danmaku?: number;
}

export interface TopicReportTrendPoint {
  date: string;
  count?: number;
  comments?: number;
  comment_count?: number;
  danmaku?: number;
  danmaku_count?: number;
}

export interface TopicReportLabelValueItem {
  name: string;
  value: number;
}

export interface TopicReportKeyAnswer {
  conversation_id: string;
  conversation_name?: string;
  message_id: string;
  role: 'assistant' | 'user' | 'system';
  content: string;
  created_at: string;
}

export interface TopicReportChartsData {
  sentiment?: TopicReportLabelValueItem[];
  top_tags?: TopicReportLabelValueItem[];
  top_keywords?: TopicReportLabelValueItem[];
  trend?: TopicReportTrendPoint[];
}

export interface TopicReport {
  topic_id: string;
  topic_name: string;
  summary?: string;
  llm_summary?: string;
  totals?: TopicReportTotals;
  sentiment?: Record<string, number>;
  top_tags?: (string | TopicReportLabelValueItem)[];
  top_keywords?: (string | TopicReportLabelValueItem)[];
  trend?: TopicReportTrendPoint[];
  key_answers?: TopicReportKeyAnswer[];
  charts?: TopicReportChartsData;
}

export interface TopicReportTask {
  task_id: string;
  topic_id: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'missing';
  created_at: string;
  updated_at?: string;
  error?: string | null;
  report?: TopicReport;
}

// Conversation & message types

export interface Conversation extends ConversationSummary {}

export interface ChatMetrics {
  latency_ms: number;
  prompt_tokens_est: number;
  completion_tokens_est: number;
  total_tokens_est: number;
}

export interface MessageMetaData {
  metrics?: ChatMetrics;
  documents_preview?: unknown;
  is_important?: boolean;
}

export interface Message {
  message_id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  create_time: string;
  meta_data?: MessageMetaData;
}

// Logs & admin related types

export interface CrawlLogItem {
  user_id: string;
  task_id?: string | null;
  keyword?: string | null;
  status: string;
  error_msg?: string | null;
  video_count: number;
  comment_count: number;
  danmaku_count: number;
  created_at: string;
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
}

// Optional crawl params when creating tasks
export interface CrawlTaskParams {
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

export interface QueryLogItem {
  user_id: string;
  topic_id?: string | null;
  conversation_id?: string | null;
  status: string;
  error_msg?: string | null;
  query_text: string;
  created_at: string;
}

export interface ProxyConfig {
  use_proxy: boolean;
  extract_url?: string | null;
  refresh_interval_sec: number;
  test_url?: string | null;
  updated_at: string;
  default_extract_url?: string | null;
  default_refresh_interval_sec?: number | null;
  default_test_url?: string | null;
  runtime_proxy?: string | null;
  runtime_proxy_refreshed_at?: string | null;
}

export interface QuotaConfig {
  query_daily_limit: number;
  query_monthly_limit: number;
  crawl_daily_limit: number;
  crawl_monthly_limit: number;
  updated_at: string;
}

export interface UserQuotaOverride {
  user_id: string;
  user_name?: string | null;
  query_daily_limit?: number | null;
  query_monthly_limit?: number | null;
  crawl_daily_limit?: number | null;
  crawl_monthly_limit?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface VectorStoreStatus {
  dataset_id: string;
  dataset_name?: string;
  keyword?: string;
  path?: string;
  exists: boolean;
  doc_count: number;
  updated_at?: string | null;
}

export interface VectorStoreSearchHit {
  text: string;
  metadata: Record<string, any>;
}

export interface VectorStoreSearchResult {
  dataset_ids: string[];
  query: string;
  hits: VectorStoreSearchHit[];
}

export interface UserQuotaStatus {
  query_daily_limit: number;
  query_daily_used: number;
  query_monthly_limit: number;
  query_monthly_used: number;
  crawl_daily_limit: number;
  crawl_daily_used: number;
  crawl_monthly_limit: number;
  crawl_monthly_used: number;
}
