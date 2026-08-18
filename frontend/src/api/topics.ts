//课题api
import http from './http';
import type { TopicListItem, TopicDetail, TopicReport, TopicReportTask, PaginatedResult } from '@/types/api';

export interface TopicCreatePayload {
  name: string;
  topic_type: string;
  description?: string;
}

export interface TopicUpdatePayload extends Partial<TopicCreatePayload> {}

export function listTopics(params?: { limit?: number; offset?: number; keyword?: string; topic_type?: string }) {
  return http.get<PaginatedResult<TopicListItem>>('/topics', { params });
}//获取课题列表

export function getTopic(topicId: string) {
  return http.get<TopicDetail>(`/topics/${topicId}`);
}//获取课题详情

export function createTopic(payload: TopicCreatePayload) {
  return http.post<TopicDetail>('/topics', payload);
}//创建课题

export function updateTopic(topicId: string, payload: TopicUpdatePayload) {
  return http.put<TopicDetail>(`/topics/${topicId}`, payload);
}//更新课题

export function deleteTopic(topicId: string) {
  return http.delete<void>(`/topics/${topicId}`);
}//删除课题

export function bindDatasetToTopic(topicId: string, datasetId: string) {
  return http.post<void>(`/topics/${topicId}/datasets`, {
    dataset_id: datasetId,
  });
}//绑定课题集

export function getTopicReport(topicId: string) {
  return http.get<TopicReport>(`/topics/${topicId}/report`);
}//获取课题报告

export function startTopicReport(topicId: string, force = false) {
  return http.post<TopicReportTask>(`/topics/${topicId}/report/async`, null, {
    params: { force },
  });//发送post请求给后端（课题报告接口）
}//启动课题报告

export function getTopicReportTask(topicId: string) {
  return http.get<TopicReportTask>(`/topics/${topicId}/report/async`);
}//获取课题报告任务
