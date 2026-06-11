# 安全审计与修复报告（测试用例自动化生成平台）

## 执行摘要
- 已定位并修复 3 个高危/严重问题：CORS 误配置、跨用户滥用模型配置（潜在 API Key 盗用）、文件上传路径遍历。
- 已加固若干中危问题：刷新令牌接口异常逻辑、用户枚举风险、Markdown 外链协议过滤、Cookie 安全属性补齐。
- 受限于当前沙箱 Python 版本为 3.14（与本项目依赖的 pydantic-core 构建链不兼容），无法在本环境中完成后端依赖安装与 pytest 运行；已使用 `python -m compileall` 对后端源码做了语法级验证，前端 `npm run build` 已通过。

## 1. 严重（Critical）

### [C-1] CORS 允许任意来源与凭证组合导致跨站滥用风险
- 影响：任意站点可能在浏览器侧读取/触发带凭证的 API 调用，造成会话滥用与数据泄露。
- 原位置：
  - [config.py:L8-L44](file:///workspace/backend/app/config.py#L8-L44)
  - [main.py:L17-L28](file:///workspace/backend/app/main.py#L17-L28)
- 修复：
  - 将默认 `CORS_ORIGINS` 从 `["*"]` 调整为本地开发白名单，并支持从环境变量逗号分隔解析：见 [config.py:L30-L41](file:///workspace/backend/app/config.py#L30-L41)
  - 当 `CORS_ORIGINS` 包含 `*` 时强制 `allow_credentials=False`，并收敛 `allow_methods/allow_headers`：见 [main.py:L17-L28](file:///workspace/backend/app/main.py#L17-L28)

### [C-2] 用例生成可跨用户引用 `model_config_id`（潜在 API Key 盗用）
- 影响：攻击者可通过传入他人的 `model_config_id` 触发后端解密并使用他人 LLM Key 发起调用，造成费用损失与敏感信息风险。
- 原位置：
  - [case_generator.py:L81-L95](file:///workspace/backend/app/services/case_generator.py#L81-L95)（修复后）
- 修复：
  - 当 `model_config_id` 指定时，强制校验 `ModelConfig.user_id == user_id` 且 `is_active==True`；并对 `user_id is None` 显式拒绝：见 [case_generator.py:L81-L95](file:///workspace/backend/app/services/case_generator.py#L81-L95)

### [C-3] 文件上传保存存在路径遍历（filename 未做 basename 处理）
- 影响：构造包含路径分隔符的文件名可能导致写出到上传目录之外（覆盖任意文件取决于部署权限）。
- 原位置：
  - [file_processor.py:L23-L41](file:///workspace/backend/app/services/file_processor.py#L23-L41)（修复后）
- 修复：
  - 仅使用 `Path(filename).name` 作为落盘文件名，并将 hash 从 md5 改为 sha256 截断；同时校验扩展名用安全文件名：见
    - [file_processor.py:L23-L41](file:///workspace/backend/app/services/file_processor.py#L23-L41)
    - [file_processor.py:L93-L104](file:///workspace/backend/app/services/file_processor.py#L93-L104)

## 2. 高（High）

### [H-1] Token 存储在可被 JS 读取的 Cookie（XSS 下易被窃取）
- 影响：任意 XSS 一旦出现，攻击者可直接读取并窃取 `access_token/refresh_token`。
- 位置：
  - [Login/index.tsx:L14-L29](file:///workspace/frontend/src/pages/Login/index.tsx#L14-L29)
  - [api/index.ts:L5-L10](file:///workspace/frontend/src/api/index.ts#L5-L10)
- 修复（兼容现有架构的“增量加固”）：
  - 设置 Cookie `SameSite=Strict`、`Secure(仅 https)`、`path=/`，并补齐删除时的 `path=/`：见
    - [Login/index.tsx:L14-L29](file:///workspace/frontend/src/pages/Login/index.tsx#L14-L29)
    - [api/index.ts:L5-L10](file:///workspace/frontend/src/api/index.ts#L5-L10)
- 仍建议（后续改造项）：
  - 将 refresh token 改为后端设置 `HttpOnly + Secure + SameSite` Cookie，并将 access token 改为短期内存存储，减少 XSS 面导致的直接泄露。

### [H-2] API Key 解密失败从“静默返回原文”改为“仅对疑似明文兼容，疑似密文失败则拒绝”
- 影响：密文损坏/伪造时，避免静默降级为“原文可用”导致不可控的明文链路。
- 位置：
  - [security.py:L57-L90](file:///workspace/backend/app/utils/security.py#L57-L90)
  - [models.py:L195-L200](file:///workspace/backend/app/routers/models.py#L195-L200)
  - [case_generator.py:L100-L105](file:///workspace/backend/app/services/case_generator.py#L100-L105)
- 修复：
  - `decrypt_api_key`：当字符串不符合 Fernet token 形态（不以 `gAAAA` 开头）时按历史行为返回原值；当符合形态但解密失败时抛出 `ValueError`，调用方据此拒绝使用：见 [security.py:L80-L90](file:///workspace/backend/app/utils/security.py#L80-L90)
  - 生成/测试模型配置时捕获解密失败并拒绝继续：见
    - [case_generator.py:L100-L105](file:///workspace/backend/app/services/case_generator.py#L100-L105)
    - [models.py:L195-L200](file:///workspace/backend/app/routers/models.py#L195-L200)

## 3. 中（Medium）

### [M-1] 刷新令牌接口错误调用导致异常与信息泄露面扩大
- 影响：错误调用可能触发 500；若生产误开 debug 或日志暴露，将放大信息泄露面与 DoS 风险。
- 修复：
  - 直接使用 `decode_token` 校验 refresh token 并生成新 token：见 [auth.py:L41-L62](file:///workspace/backend/app/routers/auth.py#L41-L62)

### [M-2] 用户枚举风险：用户列表/任意用户详情缺少权限边界
- 影响：任意登录用户可枚举用户信息，为社工与撞库提供素材。
- 修复（最小化破坏的收敛策略）：
  - `GET /api/users` 仅返回当前用户
  - `GET /api/users/{id}` 仅允许访问自身
  - 见 [users.py:L33-L58](file:///workspace/backend/app/routers/users.py#L33-L58)

### [M-3] Markdown 输出内容来自 LLM（不可信输入），需要显式 URL 协议限制
- 影响：当前 `react-markdown` 默认会转义 HTML，但外链协议未来变更/插件引入（例如 raw HTML）会迅速变成高危存量漏洞。
- 修复：
  - 增加 `urlTransform`，仅允许 `http/https/mailto`，并为 `a/img` 补齐 `target`/`rel`/`referrerPolicy`：见 [CaseGenerate/index.tsx:L35-L57](file:///workspace/frontend/src/pages/CaseGenerate/index.tsx#L35-L57)

## 4. 仍建议的后续整改（不影响本次已完成修复）
- **生产密钥治理**：在 `DEBUG=False` 时强制要求从环境变量/密钥管理注入 `SECRET_KEY` 与 `ENCRYPTION_KEY`，并避免使用占位默认值（当前仅调整默认更安全，但未做强制校验）：见 [config.py:L8-L33](file:///workspace/backend/app/config.py#L8-L33)
- **刷新令牌轮换/撤销**：服务端持久化 refresh token（或 token version），支持登出/失效与轮换，降低 token 泄露后的持续风险。
- **上传解析隔离**：对 PDF/DOCX 解析增加资源限制（大小/页数/超时），并确保 uploads 目录不可被 Web 直接访问与不可执行。

