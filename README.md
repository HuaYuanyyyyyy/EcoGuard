

[TOC]



# EcoGuard

基于排污许可国家标准文档的知识库增强索引存储，对用户提问污染物是否符合文档标准，使用LLM进行格式化输出。





## **数据流图**

```
用户上传PDF
    ↓
FastAPI接收
    ↓
    ├── MinIO（存原始文件）
    ├── MySQL（存文件元数据：文件名、上传时间、文件ID等）
    └── Chroma（切块→embedding→存向量）

用户输入污染物数据
    ↓
FastAPI接收
    ↓
每个污染物单独去Chroma检索
    ↓
把检索结果+污染物数据发给LLM
    ↓
LLM返回JSON
    ↓
Vue渲染成表格
```



## **项目目录结构**

```
EcoGuard/
├── app/
│   ├── api/
│   │   ├── file.py        # 文件管理接口
│   │   └── chat.py        # 问答接口
│   ├── service/
│   │   ├── file_service.py    # 文件业务逻辑
│   │   ├── rag_service.py     # 检索+问答逻辑
│   │   └── minio_service.py   # MinIO操作
│   ├── model/
│   │   └── file.py        # 数据库模型
│   ├── core/
│   │   ├── embedding.py   # MyEmbeddings类
│   │   └── chroma.py      # Chroma初始化
│   └── main.py            # FastAPI入口
```



## **接口清单**

文件管理：

- `POST /files/upload` 上传文件
- `GET /files/list` 文件列表，支持分页和查询
- `DELETE /files/{file_id}` 删除文件，同步三个库
- `PUT /files/{file_id}` 更新文件，先删后增
- `GET /files/{file_id}/preview` 预览文件

问答：

- `POST /chat/query` 输入污染物数据，返回合规判断表格JSON



## **数据库表设计（MySQL）**

```mysql
CREATE TABLE files (
    id          VARCHAR(36) PRIMARY KEY,
    file_name   VARCHAR(255),
    minio_path  VARCHAR(255),
    upload_time DATETIME,
    status      VARCHAR(20)
);
```

