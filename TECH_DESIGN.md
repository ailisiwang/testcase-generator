# 测试用例自动化生成平台 - 技术设计方案

## 1. 系统架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (React + Ant Design)                  │
│  用户管理 │ 用例生成 │ 用例管理 │ 模型配置 │ 系统设置              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        后端 (Python + FastAPI)                    │
│  API网关 │ 认证 │ 文件处理 │ 用例生成 │ 大模型集成                │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          数据层                                   │
│  PostgreSQL │ 本地文件系统 │ 大模型 API                          │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 技术选型详情

| 层级 | 技术栈 | 版本 |
|------|--------|------|
| 前端框架 | React | 18.x |
| UI 组件库 | Ant Design | 5.x |
| 后端框架 | FastAPI | 0.109.x |
| ORM | SQLAlchemy | 2.x |
| 数据库 | PostgreSQL | 15.x |
| **大模型框架** | **LangChain** | **1.x (最新)** |
| 认证 | JWT (python-jose) | 3.x |
| 文件处理 | python-docx, PyPDF2, Pillow | latest |
| Excel导出 | openpyxl | 3.x |
| 容器化 | Docker + docker-compose | latest |

### LangChain 1.x 新语法 (必须使用)

```python
# 安装
pip install -qU langchain "langchain[anthropic]"

# 1. 创建 Agent (新语法)
from langchain.agents import create_agent

agent = create_agent(
    model="claude-sonnet-4-6",  # 或 "openai/gpt-4", "glm-4"
    tools=[get_weather],  # 自定义工具
    system_prompt="你是测试用例生成助手"
)

# 2. 流式输出
for event in agent.stream({"messages": [("user", "生成登录用例")])}:
    print(event)

# 3. 对话记忆
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
agent_executor = AgentExecutor(agent=agent, memory=memory)

# 4. 模型调用抽象层
from langchain.chat_models import init_chat_model

# 初始化各种模型
model = init_chat_model(model="claude-sonnet-4-6", model_provider="anthropic")
model = init_chat_model(model="glm-4", model_provider="langchain.ChatZhipuAI")
model = init_chat_model(model="gpt-4", model_provider="openai")

# 5. LCEL 流式
chain = prompt | model | output_parser
for chunk in chain.stream({"input": "..."}):
    print(chunk)
```

## 3. 数据库表结构设计

### 3.1 用户表 (users)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    employee_id VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 测试系统表 (test_systems)
```sql
CREATE TABLE test_systems (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.3 模块分类表 (modules)
```sql
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    system_id INTEGER REFERENCES test_systems(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES modules(id),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.4 用例字段配置表 (case_fields)
```sql
CREATE TABLE case_fields (
    id SERIAL PRIMARY KEY,
    system_id INTEGER REFERENCES test_systems(id) ON DELETE CASCADE,
    field_name VARCHAR(50) NOT NULL,
    field_label VARCHAR(100) NOT NULL,
    field_type VARCHAR(20) DEFAULT 'text',
    is_required BOOLEAN DEFAULT FALSE,
    is_visible BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.5 测试用例表 (test_cases)
```sql
CREATE TABLE test_cases (
    id SERIAL PRIMARY KEY,
    system_id INTEGER REFERENCES test_systems(id) ON DELETE CASCADE,
    module_id INTEGER REFERENCES modules(id),
    case_data JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'draft',
    created_by INTEGER REFERENCES users(id),
    reviewer_id INTEGER REFERENCES users(id),
    review_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.6 用例版本历史表 (case_versions)
```sql
CREATE TABLE case_versions (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES test_cases(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    case_data JSONB NOT NULL,
    change_summary TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.6 模型配置表 (model_configs)
```sql
CREATE TABLE model_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT,
    api_base_url VARCHAR(255),
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2048,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.7 操作日志表 (operation_logs)
```sql
CREATE TABLE operation_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 4. API 接口设计

### 4.1 认证模块
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| POST | /api/auth/refresh | 刷新Token |
| GET | /api/auth/me | 获取当前用户 |

### 4.2 用户管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/users | 用户列表 |
| PUT | /api/users/:id | 更新用户 |

### 4.3 测试系统管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/systems | 获取系统列表 |
| POST | /api/systems | 创建系统 |
| PUT | /api/systems/:id | 更新系统 |
| DELETE | /api/systems/:id | 删除系统 |

### 4.4 模块管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/systems/:id/modules | 获取模块列表 |
| POST | /api/systems/:id/modules | 创建模块 |
| PUT | /api/modules/:id | 更新模块 |
| DELETE | /api/modules/:id | 删除模块 |

### 4.5 用例生成
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/cases/generate | 生成用例(流式) |
| POST | /api/cases/generate/file | 通过文件生成 |
| GET | /api/cases/generate/stream/:task_id | 流式输出 |

### 4.6 用例管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/cases | 用例列表(分页筛选) |
| POST | /api/cases | 创建用例 |
| PUT | /api/cases/:id | 更新用例 |
| DELETE | /api/cases/:id | 删除用例 |
| GET | /api/cases/:id/versions | 版本历史 |
| GET | /api/cases/:id/compare | 版本对比 |
| GET | /api/cases/export | 导出Excel |

### 4.7 字段配置
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/systems/:id/fields | 获取字段配置 |
| PUT | /api/systems/:id/fields | 更新字段配置 |

### 4.8 模型配置
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/models | 模型配置列表 |
| POST | /api/models | 创建配置 |
| PUT | /api/models/:id | 更新配置 |
| DELETE | /api/models/:id | 删除配置 |

### 4.9 日志审计
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/logs | 操作日志列表 |

## 5. 目录结构设计

```
testcase-generator/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI入口
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库连接
│   │   ├── models/              # SQLAlchemy模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── system.py
│   │   │   ├── module.py
│   │   │   ├── test_case.py
│   │   │   └── model_config.py
│   │   ├── schemas/             # Pydantic模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── system.py
│   │   │   └── case.py
│   │   ├── routers/             # API路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── systems.py
│   │   │   ├── modules.py
│   │   │   ├── cases.py
│   │   │   └── models.py
│   │   ├── services/            # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── case_generator.py
│   │   │   └── file_processor.py
│   │   ├── llm/                # 大模型集成 (LangChain 1.x)
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # 模型抽象层
│   │   │   ├── agent.py        # Agent 创建 (create_agent)
│   │   │   ├── memory.py       # 对话记忆
│   │   │   ├── streaming.py    # 流式输出
│   │   │   └── providers/
│   │   │       ├── __init__.py
│   │   │       ├── glm.py      # 智谱GLM
│   │   │       ├── doubao.py   # 字节豆包
│   │   │       ├── qwen.py     # 阿里千问
│   │   │       ├── gpt.py      # OpenAI GPT
│   │   │       └── claude.py   # Anthropic Claude
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── security.py      # 加密/JWT
│   │       └── excel.py        # Excel导出
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/                # API请求
│   │   ├── components/        # 公共组件
│   │   ├── pages/             # 页面
│   │   │   ├── Login/
│   │   │   ├── Register/
│   │   │   ├── Dashboard/
│   │   │   ├── Systems/
│   │   │   ├── Cases/
│   │   │   ├── CaseGenerate/
│   │   │   └── Settings/
│   │   ├── stores/            # 状态管理
│   │   ├── utils/
│   │   └── App.tsx
│   ├── package.json
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── README.md
```

## 6. 部署方案

### 6.1 Docker 部署
```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: testcase
      POSTGRES_USER: testcase
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://testcase:${DB_PASSWORD}@postgres:5432/testcase
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
  uploads:
```

### 6.2 直接部署
```bash
# 后端
cd backend
pip install -r requirements.txt
python -m app.main

# 前端
cd frontend
npm install
npm run build
# 配置 Nginx 静态托管
```

## 7. 安全考虑

1. **API Key 加密存储**: 使用 Fernet 对称加密
2. **JWT 过期时间**: 访问Token 24h, 刷新Token 7天
3. **文件上传限制**: 类型检查、大小限制
4. **CORS 配置**: 仅允许可信域名
5. **SQL注入防护**: 使用参数化查询
6. **XSS防护**: 输入过滤 + CSP头


## 8. LangChain 1.x Provider 示例

### 8.1 GLM 智谱
```python
from langchain.chat_models import init_chat_model

# 初始化 GLM 模型
glm_model = init_chat_model(
    model="glm-4",
    model_provider="langchain.ChatZhipuAI",
    zhipu_api_key="your-api-key"
)

# 流式调用
for chunk in glm_model.stream("你好"):
    print(chunk.content)
```

### 8.2 OpenAI GPT
```python
from langchain.chat_models import init_chat_model

gpt_model = init_chat_model(
    model="gpt-4",
    model_provider="openai",
    openai_api_key="your-api-key"
)
```

### 8.3 Anthropic Claude
```python
from langchain.chat_models import init_chat_model

claude_model = init_chat_model(
    model="claude-sonnet-4-6",
    model_provider="anthropic",
    anthropic_api_key="your-api-key"
)
```

### 8.4 阿里千问
```python
from langchain.chat_models import init_chat_model

qwen_model = init_chat_model(
    model="qwen-turbo",
    model_provider="langchain.Chat Alibaba",
    api_key="your-api-key"
)
```

### 8.5 创建测试用例生成 Agent
```python
from langchain.agents import create_agent
from langchain.tools import tool

@tool
def generate_test_case(requirement: str) -> str:
    """根据需求生成测试用例"""
    # 实现生成逻辑
    pass

agent = create_agent(
    model="glm-4",  # 使用 GLM
    model_provider="langchain.ChatZhipuAI",
    tools=[generate_test_case],
    system_prompt="你是一个专业的测试工程师，擅长根据需求生成测试用例"
)

# 流式输出
for event in agent.stream({"messages": [("user", "为用户登录功能生成测试用例")]}):
    print(event)
```

