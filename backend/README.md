# 法宝 - AI法律助手 后端服务

基于 FastAPI + MySQL 的后端 API，为前端提供认证、AI 法律咨询、文书生成、合同审查四类接口。

## 技术栈

| 组件 | 说明 |
|------|------|
| FastAPI | Web 框架 |
| SQLAlchemy 2.0 | ORM（新式声明式写法 `Mapped` / `mapped_column`） |
| Alembic | 数据库迁移 |
| Pydantic V2 + pydantic-settings | 数据校验、序列化与 .env 配置管理 |
| PyMySQL | MySQL 驱动 |
| python-jose + passlib/bcrypt | JWT 认证与密码哈希 |
| python-docx / PyPDF2 | 合同文件文本提取 |
| uvicorn | ASGI 服务器 |

## 环境要求

- Python 3.11+
- MySQL 5.7+ / 8.0（建议 8.0，字符集 utf8mb4）

## 快速开始

### 1. 创建虚拟环境并安装依赖

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 创建数据库

登录 MySQL 后执行（库名与 .env 中 DB_NAME 保持一致）：

```sql
CREATE DATABASE fabao DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 配置环境变量

```bash
# 复制示例文件为 .env，按需修改数据库密码、JWT 密钥等
copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux
```

### 4. 初始化数据库表（二选一）

**方式 A：启动时自动建表（开发环境推荐，默认开启）**

`.env` 中 `AUTO_CREATE_TABLES=true`，直接启动服务即可自动创建 5 张表。

**方式 B：使用 Alembic 迁移（生产环境推荐，支持版本管理与回滚）**

```bash
# 生成迁移脚本（基于模型自动比对，脚本保存在 alembic/versions/）
alembic revision --autogenerate -m "init tables"

# 执行迁移建表
alembic upgrade head

# 其他常用命令
alembic downgrade -1        # 回滚上一个版本
alembic history             # 查看迁移历史
```

> 使用 Alembic 时建议将 `.env` 中 `AUTO_CREATE_TABLES` 设为 `false`，避免两套建表机制混用。

### 5. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

启动成功后：

- 健康检查：<http://127.0.0.1:8000/>
- 交互式接口文档（Swagger UI）：<http://127.0.0.1:8000/docs>

## 接口一览（统一前缀 `/api/v1`，响应格式 `{"code", "message", "data"}`）

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 认证 | POST | `/api/v1/auth/register` | 用户注册（username, email, password） |
| 认证 | POST | `/api/v1/auth/login` | 登录，返回 JWT token |
| 认证 | GET | `/api/v1/auth/me` | 获取当前用户信息（需认证） |
| 咨询 | GET | `/api/v1/chat/conversations` | 对话列表 |
| 咨询 | POST | `/api/v1/chat/conversations` | 新建对话 |
| 咨询 | DELETE | `/api/v1/chat/conversations/{id}` | 删除对话 |
| 咨询 | GET | `/api/v1/chat/conversations/{id}/messages` | 消息列表 |
| 咨询 | POST | `/api/v1/chat/conversations/{id}/messages` | 发送消息，返回 AI 回复 |
| 文书 | POST | `/api/v1/documents/generate` | 生成文书（doc_type + form_data） |
| 文书 | GET | `/api/v1/documents/list` | 文书历史列表 |
| 文书 | GET | `/api/v1/documents/{id}` | 文书记录详情 |
| 合同 | POST | `/api/v1/contracts/upload` | 上传合同（.docx / .pdf）并提取文本 |
| 合同 | POST | `/api/v1/contracts/review/{id}` | 执行审查，返回风险条款 |
| 合同 | GET | `/api/v1/contracts/list` | 审查历史列表 |

> 需认证的接口请在请求头携带：`Authorization: Bearer <token>`

## 目录结构

```text
backend/
├── app/
│   ├── main.py            # 应用入口：路由、中间件、CORS、全局异常处理
│   ├── config.py          # 配置管理（.env）
│   ├── database.py        # 引擎 / 会话工厂 / 模型基类
│   ├── models/            # ORM 模型（users / conversations / messages / documents / contracts）
│   ├── schemas/           # Pydantic 请求/响应模型
│   ├── api/               # 路由层
│   ├── services/          # 业务逻辑（AI 调用 / 文书模板 / 合同审查）
│   ├── core/              # JWT 安全、公共依赖、自定义异常
│   └── utils/             # 文件解析、统一响应
├── alembic/               # 数据库迁移
├── uploads/               # 合同上传目录（自动创建）
├── alembic.ini
├── requirements.txt
└── .env.example
```

## 说明

- AI 回复、文书生成、合同审查当前均为**模拟实现**，接入真实 AI 时只需修改 `app/services/` 下对应文件（已用 `TODO` 标注）。
- 上传的合同文件保存在 `backend/uploads/`，并以 UUID 重命名存储。
