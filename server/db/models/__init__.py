# -*- coding: utf-8 -*-
# 数据模型聚合，便于 Base.metadata.create_all 引用

from server.db.models.user_model import UserModel
from server.db.models.conversation_model import ConversationModel
from server.db.models.message_model import MessageModel
from server.db.models.keyword_model import KeywordExtractionModel
from server.db.models.video_item_model import VideoItemModel
from server.db.models.video_comment_model import VideoCommentModel
from server.db.models.video_danmaku_model import VideoDanmakuModel
from server.db.models.crawl_task_model import CrawlTaskModel
from server.db.models.dataset_model import DatasetModel
from server.db.models.topic_model import TopicModel
from server.db.models.topic_conversation_model import TopicConversationModel
from server.db.models.topic_dataset_model import TopicDatasetModel
from server.db.models.query_log_model import QueryLogModel
from server.db.models.crawl_log_model import CrawlLogModel
from server.db.models.proxy_config_model import ProxyConfigModel
from server.db.models.crawler_config_model import CrawlerConfigModel
