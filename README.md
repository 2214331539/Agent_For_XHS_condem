# Byt 测评系统

半自动化小红书 Byt 测评后台，覆盖产品录入、AI 笔记生成、发布状态、7 天提醒、数据录入和复盘分析。

## 目录

- `frontend/`: React + Vite + TypeScript + Ant Design
- `backend/`: FastAPI + SQLAlchemy 2.0
- `.env.example`: 统一配置模板，包含 API、数据库、OSS、OpenAI、提醒配置
- `docker-compose.yml`: PostgreSQL + 后端 + 前端本地编排

## 本地启动

数据库统一使用 PostgreSQL。推荐先用 Docker Compose 启动数据库，再启动后端和前端。

```bash
cp .env.example .env
docker compose up -d postgres
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

访问：

- 前端：http://localhost:5173
- 后端文档：http://localhost:8000/docs

## 配置约定

所有外部服务配置统一放在 `.env`：

- `DATABASE_URL`: PostgreSQL 数据库连接，默认使用宿主机 `55432` 端口，避免和本机已有 PostgreSQL 的 `5432` 冲突
- `STORAGE_BACKEND`: `local` 或 `aliyun_oss`
- `OSS_*`: 阿里云 OSS 参数
- `OPENAI_*`: OpenAI Responses API 参数
- `AGENT_PROVIDER`: `local` 或后续扩展的真实 OpenAI Agent provider
- `VITE_API_BASE_URL`: 前端 API 根地址
