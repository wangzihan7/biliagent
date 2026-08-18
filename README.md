# BiliAgent · B 站舆情分析助手

爬取 B 站视频、评论、弹幕，沉淀成可复用的数据集，然后用 RAG 对话式追问，
并汇总成带图表的课题报告。

> ⚠️ **仅供学习研究**。使用爬虫功能请遵守 B 站的 robots 协议与用户协议，
> 控制请求频率，不要用于商业用途或大规模数据采集。

---

## 🚀 第一次使用？

**请看 → [安装指南.md](安装指南.md)**

从装 Python 开始，一步步带你配好环境跑起来。
已经配好的话，往下看「启动」那节即可。

---

## 它能做什么

```
① 输入关键词           →  爬取 B 站视频 + 评论 + 弹幕，存进 MySQL
② 数据集自动向量化      →  存进 FAISS
③ 挂到「课题」下        →  一个课题可以关联多个数据集
④ 对话式追问           →  基于这些数据做 RAG 问答，答案带视频链接
⑤ 生成课题报告          →  词云、情感分布、时间趋势、LLM 总结
```

---

## 技术栈

| 层 | 用什么 |
|---|---|
| 后端 | Python + FastAPI + SQLAlchemy |
| 关系库 | MySQL 8（库名 `bilibili_analysis`，16 张表） |
| 向量库 | FAISS（本地文件，无需部署） |
| RAG 流程 | LangGraph（四节点 CRAG） |
| 前端 | Vue 3 + Vite + TypeScript + Element Plus + ECharts |
| 模型 | 硅基流动：生成 DeepSeek-V3.2 / 打分改写 Qwen2.5-7B / 嵌入 Qwen3-Embedding-8B |
| 爬虫 | requests + 线程池，支持代理轮换与登录态 |

代码规模：Python 约 7,000 行、Vue 约 4,100 行、TypeScript 约 900 行。

---

## 启动

**前提**：MySQL 已运行，`.env` 和 `frontend/.env` 都配好了。

需要开**两个**终端窗口，或者直接双击项目根目录的两个 bat 文件。

### 窗口 1 · 后端

```powershell
.venv\Scripts\python.exe server_extended.py
```

启动后 http://127.0.0.1:8300/docs 可以看到接口文档。

### 窗口 2 · 前端

```powershell
cd frontend
npm run dev
```

浏览器打开 **http://127.0.0.1:5173**

---

## 项目结构

```
BiliAgent/
├── server_extended.py       后端入口（端口 8300，含端口占用自动递增）
├── init_db.py               建表脚本
├── requirements.txt
├── .env.example             配置模板 ← 复制成 .env 再填
│
├── bili_server/             【RAG 内核】不依赖 Web 层，可独立运行
│   ├── workflow.py          LangGraph 组图
│   ├── nodes.py             四个节点：检索 / 打分 / 改写 / 生成
│   ├── edges.py             条件边：决定走生成还是重新检索
│   ├── grader.py            打分器 + 问题改写器
│   ├── generate_chain.py    生成用的 prompt
│   ├── graph.py             状态定义
│   └── document_loader.py   FAISS 封装
│
├── blibli_get/              【爬虫】
│   ├── 哔哩哔哩视频信息.py    视频搜索与详情
│   ├── blibli评论爬取.py      评论（含二级回复）
│   ├── bibli弹幕.py          弹幕
│   ├── pipeline.py          并发抓取 + 串行写库
│   └── config.py            代理与 Cookie 管理
│
├── server/                  【Web 层】四层架构
│   ├── api_router.py        路由聚合
│   ├── routers/             6 个领域路由：认证/聊天/爬虫/数据集/课题/日志
│   ├── services/            业务编排（11 个模块）
│   ├── db/
│   │   ├── models/          16 张表的 ORM
│   │   ├── repository/      数据访问
│   │   └── session.py       引擎与会话
│   ├── chat/                问答 Agent
│   ├── memory/              基于数据库的对话记忆
│   ├── auth/                自研 HS256 JWT
│   └── schemas/             请求/响应模型
│
├── frontend/                【前端】
│   └── src/
│       ├── views/           课题/数据集/爬虫/问答/报告/管理 等页面
│       ├── api/             接口封装
│       ├── composables/     SSE 流式解析
│       └── stores/          Pinia 状态
│
├── vectorstores/            FAISS 索引（不进 git，可重建）
└── runs/                    爬虫运行时落盘的 Excel（不进 git）
```

---

## RAG 流程

```
              ┌──────────────┐
   开始 ────► │   retrieve   │ ◄──────────┐
              │  改写 + 检索  │            │
              └──────┬───────┘            │
                     ▼                    │
              ┌──────────────┐            │
              │grade_documents│           │
              │   逐块打分    │            │
              └──────┬───────┘            │
           ┌─────────┴─────────┐          │
       有文档留下          全被否决        │
           ▼                   ▼          │
    ┌─────────────┐   ┌────────────────┐  │
    │  generate   │   │transform_query ├──┘
    └──────┬──────┘   └────────────────┘
           ▼
          END
```

**双模型设计**：打分和改写用便宜的 Qwen2.5-7B，生成答案才上 DeepSeek-V3.2。

**流式输出**：通过 `astream_events` 捕获事件，用 `langgraph_node == "generate"`
过滤掉打分模型产生的 token，只把答案推给前端。

---

## 数据存在哪

```
MySQL（bilibili_analysis）        FAISS
├─ user_info / conversation      vectorstores/ds_<md5>/
├─ message_history                 ├─ index.faiss   向量矩阵
├─ video_item / comment / danmaku  └─ index.pkl     原文 + 映射
├─ dataset / crawl_task
├─ topic / topic_dataset
└─ query_log / crawl_log
```

索引目录名是「所选数据集 ID 组合」的 md5，所以选不同的数据集组合会生成不同的索引。

---

## 可调参数（`.env`）

```
USE_PROXY=false              是否启用代理轮换
SERVER_PORT=8300             后端端口
```

爬虫限流参数在 `blibli_get/pipeline.py` 顶部，都可以用环境变量覆盖：

```
BILI_CRAWLER_MAX_ITEMS=5         每关键词抓几个视频
BILI_CRAWLER_MAX_COMMENTS=10     每视频抓几条评论
BILI_CRAWLER_MAX_DANMAKU=50      每视频抓几条弹幕
BILI_CRAWLER_CONCURRENCY=5       并发线程数
```

**默认值定得很保守**，是有意的限流设计。加大之前请先考虑对方服务器的承受能力。

---

## 已知问题

这些是分析代码时发现的，尚未修复，记录在此：

| 位置 | 问题 |
|---|---|
| `bili_server/document_loader.py` | `OpenAIEmbeddings` 缺 `check_embedding_ctx_length=False`，对接非 OpenAI 模型时向量会失真（**影响检索质量，优先级最高**） |
| `server/services/auth_service.py:71` | `raise` 了一个字符串而非异常类，会抛 TypeError（500 而非 401） |
| `bili_server/workflow.py` | `transform_query → retrieve` 循环无次数上限，可能撞递归限制 |
| `server_extended.py` | CORS `allow_origins=["*"]` 配 `allow_credentials=True` 是无效组合 |
| `server/db/repository/user_repository.py` | 密码用裸 SHA256 无盐 |

---

## 文档

- 第一次配环境 → [安装指南.md](安装指南.md)
- 日常启动与命令速查 → [启动说明.md](启动说明.md)
