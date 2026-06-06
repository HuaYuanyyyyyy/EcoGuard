

[TOC]



# EcoGuard

基于 RAG（检索增强生成）的环保合规智能审查系统。支持上传大气污染物排放标准 PDF 构建知识库，用户可通过自然语言对话或上传排污许可 MHTML 文件，自动对照国标/地标判断是否达标，结果通过 SSE 流式推送。



## **技术栈**

| 层次 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| LLM 调用 | LangChain + OpenAI 兼容接口 |
| 向量数据库 | ChromaDB |
| 对象存储 | MinIO |
| 关系数据库 | MySQL（SQLAlchemy ORM） |
| 混合检索 | BM25（jieba 分词）+ 向量检索 + RRF 融合 |
| 精排 | Cohere Rerank（rerank-multilingual-v3.0） |
| 流式响应 | Server-Sent Events（SSE） |
| 前端 | Vue 3 |



## **数据流图**

**文件上传：**
```
用户上传 PDF
    ↓
FastAPI 接收
    ↓
    ├── MinIO（存原始文件）
    ├── MySQL（存文件元数据：文件名、上传时间、文件ID等）
    └── Chroma（切块 chunk_size=500 → embedding → 存向量）
```

**对话合规查询：**
```
用户自然语言输入
    ↓
parse_input（LLM 一次调用：意图识别 + 污染物数据提取）
    ↓
    ├─ intent=compliance → 并发检测每项污染物
    │       ↓
    │   hybrid_search（BM25 + 向量检索 → RRF 融合 → Cohere Rerank）
    │       ↓
    │   LLM 判断合规性（JSON）
    │       ↓
    │   SSE 逐项推送 result_item
    │       ↓
    │   所有完成后流式输出 summary_chunk
    │
    └─ intent=chat → 普通问答，流式输出 chat_chunk
```

**MHTML 文件审查：**
```
用户上传排污许可 .mhtml 文件
    ↓
HTML 解析（处理 rowspan/colspan 复杂表格）
    ↓
LLM 结构化提取（污染物名称 + 浓度限值 + 参照标准文件）
    ↓
按 GB 编号模糊匹配已上传 PDF → hybrid_search_by_filename 定向检索
    ↓
LLM 判断合规性 → SSE 流式推送
```



## **项目目录结构**

```
EcoGuard/
├── app/
│   ├── api/
│   │   ├── file.py            # 文件管理接口
│   │   └── chat.py            # 问答 & MHTML 审查接口
│   ├── service/
│   │   ├── file_service.py    # PDF 上传/删除（三端同步）
│   │   ├── rag_service.py     # 合规检测核心流程
│   │   ├── mhtml_service.py   # MHTML 解析与结构化提取
│   │   └── minio_service.py   # MinIO 文件存储
│   ├── prompts/
│   │   ├── parse.py           # 意图识别 + 数据提取提示词
│   │   ├── compliance.py      # 合规判断提示词
│   │   ├── summary.py         # 自然语言总结提示词
│   │   ├── system.py          # 系统角色提示词
│   │   └── intent.py          # 意图分类提示词
│   ├── model/
│   │   └── file.py            # 数据库模型
│   ├── core/
│   │   ├── embedding.py       # 自定义 Embeddings 适配器
│   │   ├── chroma.py          # ChromaDB 初始化
│   │   ├── hybrid_search.py   # BM25 + 向量 + RRF + Rerank
│   │   └── rerank.py          # Cohere Rerank 封装
│   ├── config.py              # 配置项（pydantic-settings）
│   ├── database.py            # SQLAlchemy 初始化
│   └── main.py                # FastAPI 入口
├── frontend/                  # Vue 3 前端
└── demo/                      # BM25 / 混合检索 / Rerank 调试脚本
```



## **接口清单**

**文件管理：**

- `POST /files/upload` 上传一个或多个 PDF 标准文件（同名自动覆盖）
- `GET /files/list` 获取已上传文件列表
- `DELETE /files/{file_id}` 删除文件，MinIO / Chroma / MySQL 三端同步清理

**合规审查：**

- `POST /chat/query` 自然语言查询，SSE 流式响应
- `POST /chat/check-mhtml` 上传 MHTML 文件，SSE 流式审查
- `POST /chat/debug-mhtml` 调试端点，返回 MHTML 解析中间结果（不走 RAG）

**SSE 事件类型：**

| type | 说明 |
|------|------|
| `result_item` | 单项污染物检测结果 JSON |
| `summary_chunk` | 总结报告文字片段（流式） |
| `chat_chunk` | 普通问答文字片段（流式） |
| `done` | 响应结束信号 |



## **数据库表设计（MySQL）**

```mysql
CREATE TABLE files (
    id          VARCHAR(36) PRIMARY KEY,
    file_name   VARCHAR(255),
    minio_path  VARCHAR(255),
    file_size   INT,
    upload_time DATETIME,
    status      VARCHAR(20)    -- 'active' / 'deleted'
);
```
