# 测试用例自动化生成平台 - Code Wiki

## 1. 项目概述
本项目是一个基于大语言模型（LLM）的测试用例自动化生成平台。它允许测试工程师根据需求自动生成、管理、导出测试用例，并支持多系统的模块划分以及不同的主流大模型（如智谱GLM、OpenAI GPT、Anthropic Claude、阿里千问等）。

---

## 2. 整体架构
项目采用前后端分离的架构模式：
- **前端 (Frontend)**: 基于 React 18 + Vite 构建，UI 层采用 Ant Design 5.x 组件库，通过 Zustand 进行状态管理，提供响应式的用户界面。
- **后端 (Backend)**: 基于 Python FastAPI 框架构建，提供 RESTful API 接口，使用 SQLAlchemy 2.x 作为 ORM 操作 PostgreSQL 数据库。
- **大模型集成层**: 后端集成了 LangChain 1.x 框架，通过 `create_agent` 和 `init_chat_model` 实现多种 LLM 的流式调用和生成逻辑。
- **数据层**: 使用 PostgreSQL 15 存储用户数据、系统模块、测试用例版本历史及模型配置等数据。

---

## 3. 技术栈与依赖关系

### 3.1 前端依赖
- **核心框架**: React (`^18.3.1`), React DOM, React Router (`^6.22.0`)
- **构建工具**: Vite (`^5.4.1`), TypeScript (`^5.5.3`)
- **UI & 样式**: Ant Design (`^5.15.0`), @ant-design/icons
- **状态管理**: Zustand (`^4.5.0`)
- **网络请求**: Axios (`^1.6.7`)
- **Markdown渲染**: react-markdown, @uiw/react-md-editor
- **其他**: dayjs (时间处理), js-cookie (Cookie管理)

### 3.2 后端依赖
- **核心框架**: FastAPI (`0.109.0`), Uvicorn
- **数据库 & ORM**: SQLAlchemy (`2.0.25`), Alembic, psycopg2-binary
- **LLM 集成**: LangChain (`0.3.7`), langchain-core, langchain-community, openai
- **认证与安全**: python-jose, passlib, cryptography
- **数据校验**: Pydantic (`2.10.4`), pydantic-settings
- **文件处理**: python-docx, PyPDF2, openpyxl

---

## 4. 主要模块职责

### 4.1 后端模块 (`backend/app/`)
- **`routers/`**: 包含 FastAPI 的各个路由控制器，负责处理 HTTP 请求。
  - `auth.py`: 用户注册、登录、刷新 Token。
  - `cases.py`: 测试用例生成（包含流式接口）、用例管理、导出 Excel。
  - `models.py`: 大模型配置管理（如配置 API Key 和选用哪个提供商）。
  - `systems.py` / `modules.py`: 测试系统和模块分类的增删改查。
- **`services/`**: 存放核心业务逻辑。
  - `case_generator.py`: 处理从文本或文件生成测试用例的业务流程。
  - `file_processor.py`: 解析用户上传的文档（Word, PDF 等）。
- **`llm/`**: 大模型交互核心层，封装 LangChain 相关逻辑。
  - `agent.py`: 封装了 Agent 创建和流式输出的逻辑，包含 `TestCaseAgent`。
  - `providers/`: 各大模型（Claude, Doubao, GLM, GPT, Qwen）的具体接入实现。
- **`models/` & `schemas/`**: 
  - `models/`: SQLAlchemy 数据库表映射类。
  - `schemas/`: Pydantic 数据验证模型，用于请求与响应数据的序列化。

### 4.2 前端模块 (`frontend/src/`)
- **`pages/`**: 业务页面组件，包括登录注册、Dashboard、系统管理 (`Systems`)、模块管理 (`Modules`)、用例管理 (`Cases`)、用例生成 (`CaseGenerate`)、模型配置 (`ModelConfig`)。
- **`api/`**: 封装 Axios 请求拦截器与 API 接口调用 (`index.ts`, `services.ts`)，处理 Token 自动刷新和统一错误提示。
- **`stores/`**: Zustand 状态仓库，如 `authStore.ts` 负责全局用户鉴权状态。
- **`components/`**: 可复用组件，例如全局布局 `MainLayout` 和错误边界 `ErrorBoundary`。

---

## 5. 关键类与函数说明

### 5.1 后端关键类：`TestCaseAgent` (`backend/app/llm/agent.py`)
该类负责封装大语言模型的调用逻辑，利用 LangChain 1.x 的语法创建工具代理：
- **`__init__`**: 初始化模型配置，通过 `init_chat_model` 根据 `provider` (如 glm, openai, anthropic) 实例化对应的 ChatModel。
- **`_create_tools`**: 定义大模型可用的工具集，包含 `generate_test_cases` (用例生成) 和 `validate_case_structure` (验证用例 JSON 结构)。
- **`create_agent`**: 使用 `langchain.agents.create_agent` 将 LLM、工具和 System Prompt 组合成一个可执行的 Agent 实例。
- **`run` & `run_stream_events`**: 提供异步的流式输出（Generator），通过 `astream` 实时将大模型的生成结果返回给前端，提供打字机体验。

### 5.2 后端关键方法：`generate_cases_with_agent` (`backend/app/llm/agent.py`)
- 帮助函数，用于快速初始化 `TestCaseAgent` 并执行用例生成流程。接收需求描述、提供商、API Key 等参数，通过异步生成器 `Yield` 返回大模型生成的测试用例数据。

### 5.3 前端关键配置：Axios 拦截器 (`frontend/src/api/index.ts`)
- **请求拦截器**: 自动从 Cookie 中读取 `access_token` 附加到 Authorization 请求头。
- **响应拦截器**: 捕获 401 Unauthorized 错误，利用 `refresh_token` 自动调用刷新 Token 接口。刷新期间如果有新的请求，会将其放入队列挂起，待刷新完成后重试，保证用户体验的连贯性。

---

## 6. 目录结构

```text
/workspace
├── backend/                  # 后端项目目录
│   ├── app/                  # 后端应用代码
│   │   ├── llm/              # LangChain 大模型集成层
│   │   ├── models/           # 数据库模型
│   │   ├── routers/          # API 路由
│   │   ├── schemas/          # Pydantic 校验模型
│   │   ├── services/         # 业务逻辑层
│   │   ├── utils/            # 工具类(安全加密、Excel导出等)
│   │   ├── main.py           # FastAPI 入口
│   │   └── database.py       # 数据库配置
│   ├── tests/                # pytest 测试代码
│   ├── requirements.txt      # 后端依赖
│   └── Dockerfile            # 后端容器构建文件
├── frontend/                 # 前端项目目录
│   ├── src/                  # 前端源码
│   │   ├── api/              # Axios 及 API 接口封装
│   │   ├── components/       # 公共组件
│   │   ├── pages/            # 路由页面
│   │   ├── stores/           # Zustand 状态管理
│   │   └── App.tsx           # React 根组件与路由配置
│   ├── package.json          # 前端依赖
│   ├── vite.config.ts        # Vite 配置
│   └── Dockerfile            # 前端容器构建文件
├── docker-compose.yml        # (如适用) 全局或各端 Docker 编排文件
├── TECH_DESIGN.md            # 系统技术设计方案
└── AGENT_TEAMS_GUIDE.md      # Claude Code Agent Teams 使用规范
```

---

## 7. 项目运行方式

项目支持 Docker 容器化一键部署以及本地直接部署两种方式。

### 7.1 本地开发运行

**环境要求**:
- Node.js (推荐 v22.x)
- Python 3.9+
- PostgreSQL 15+

**后端运行**:
```bash
cd backend
# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量 (根据 .env.example 创建 .env 并配置数据库连接)
cp .env.example .env

# 启动 FastAPI 服务
python -m app.main
# 服务将在 http://localhost:8000 运行
```

**前端运行**:
```bash
cd frontend
# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 服务将在 http://localhost:5173 (或由 Vite 指定的端口) 运行
```

### 7.2 Docker Compose 运行
如果项目根目录或各端目录包含完整的 docker-compose 配置，可以使用以下命令一键启动（包含 PostgreSQL, Backend, Frontend）：
```bash
# 在包含 docker-compose.yml 的目录执行
docker-compose up -d --build
```
启动后：
- 前端地址：`http://localhost:3000`
- 后端 API 地址：`http://localhost:8000`

---

## 8. 高级特性：Agent Teams 工作流
本项目提供了对 `Claude Code Agent Teams` 实验性功能的支持。用户可通过终端直接召唤虚拟开发团队（架构师、前端、后端、QA）协同工作。
- **环境配置**: 需要在 `~/.claude/settings.json` 中配置 `"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"`。
- **启动方式**:
  ```bash
  claude --permission-mode bypassPermissions --print --teammate-mode in-process '你的任务描述'
  ```
- **详细规范**: 请参考代码库中的 `AGENT_TEAMS_GUIDE.md` 获取完整的交互操作与团队分配策略。
