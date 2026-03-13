# Claude Code Agent Teams 使用规范

> 基于 2026-03-13 实践整理

---

## 一、环境准备

### 1.1 Node.js 版本要求

| 状态 | 版本 | 说明 |
|------|------|------|
| ❌ 不推荐 | Node.js v25+ | Claude Code 有兼容性问题 |
| ✅ 推荐 | Node.js v22.x | 稳定运行 Claude Code 2.1+ |

```bash
# 降级 Node.js
source ~/.nvm/nvm.sh
nvm use 22
nvm alias default 22

# 验证版本
node --version  # 应显示 v22.x.x
claude --version  # 应显示 2.1.x
```

### 1.2 启用 Agent Teams 实验性功能

在 `~/.claude/settings.json` 中添加：

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

或临时通过环境变量：
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

---

## 二、启动 Agent Teams

### 2.1 基础命令模板

```bash
cd ~/项目目录
source ~/.nvm/nvm.sh
nvm use 22

claude --permission-mode bypassPermissions --print --teammate-mode in-process '你的任务描述'
```

### 2.2 关键参数说明

| 参数 | 作用 | 必需 |
|------|------|------|
| `--permission-mode bypassPermissions` | 跳过权限确认 | ✅ |
| `--print` | 打印模式，保持工具访问 | ✅ |
| `--teammate-mode in-process` | 使用内联模式（终端内切换） | 推荐 |
| `--teammate-mode tmux` | 分屏模式（需要 tmux） | 可选 |

### 2.3 任务描述模板

```
你是团队 Lead。请创建一个 agent team，成员如下：

1. **技术架构师** - [职责描述]
2. **前端工程师** - [职责描述]
3. **后端工程师** - [职责描述]
4. **测试工程师** - [职责描述]

项目：[项目名称]
技术栈：[技术栈]
GitHub：[仓库地址]

工作流程：
1. [步骤1]
2. [步骤2]
3. [步骤3]

请开始创建团队并执行任务。
```

---

## 三、任务完成自动通知（重点！）

### 3.1 为什么需要

Claude Code Agent Teams 默认**不会自动通知**任务完成，需要在 prompt 中配置 wake trigger。

### 3.2 集成命令

在任务描述末尾添加：

```
请在任务完成后执行以下命令通知我：
openclaw system event --text "Done: [任务摘要]" --mode now
```

### 3.3 完整示例

```bash
cd ~/testcase-generator
source ~/.nvm/nvm.sh
nvm use 22

claude --permission-mode bypassPermissions --print --teammate-mode in-process '你是团队 Lead。请创建一个 agent team，成员如下：

1. **技术架构师** - 系统架构设计
2. **前端工程师** - React + Ant Design 开发
3. **后端工程师** - Python + LangChain 开发
4. **测试工程师** - 功能验证

项目：测试用例自动化生成平台
仓库：https://github.com/ailisiwang/testcase-generator

请开始创建团队并执行任务。

请在任务完成后执行以下命令通知我：
openclaw system event --text "Done: Agent Teams 完成测试用例平台开发，修改了31个文件" --mode now'
```

---

## 四、交互操作

### 4.1 团队控制

| 操作 | 说明 |
|------|------|
| `Shift+Down` | 切换到下一个 teammate |
| `Escape` | 打断当前 agent |
| `Ctrl+T` | 显示/隐藏任务列表 |

### 4.2 通过 Exec 工具监控

```bash
# 查看运行中的会话
process action:list

# 查看输出
process action:log sessionId:XXX

# 检查是否完成
process action:poll sessionId:XXX

# 发送输入（如确认）
process action:submit sessionId:XXX data:"1"

# 终止会话
process action:kill sessionId:XXX
```

---

## 五、团队成员配置最佳实践

### 5.1 角色定义示例

```
1. **技术架构师 (@architect)** - 系统架构设计、技术选型、代码规范
2. **前端工程师 (@frontend-dev)** - 界面开发、组件编写、样式优化
3. **后端工程师 (@backend-dev)** - API 开发、数据库设计、业务逻辑
4. **测试工程师 (@qa-engineer)** - 测试计划、用例编写、质量保障
```

### 5.2 任务分配策略

- **独立性**：每个成员的任务应该相对独立，减少等待
- **并行性**：前端/后端可以同时开发
- **依赖管理**：架构师先完成，后续成员再开始

---

## 六、常见问题

### Q1: Claude Code 启动后卡住不动

**原因**：等待安全确认
**解决**：发送 `1` 确认信任该目录

### Q2: Node.js 版本不兼容

**症状**：`TypeError: Cannot read properties of undefined (reading 'prototype')`
**解决**：降级到 Node.js v22.x

### Q3: 团队成员不执行任务

**检查**：确认已启用 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

### Q4: 任务完成后没有通知

**原因**：没有在 prompt 中添加 wake trigger
**解决**：按 3.2 节添加通知命令

---

## 七、完整工作流总结

```
1. 准备环境
   ├── nvm use 22
   ├── 确认 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
   └── cd 项目目录

2. 启动团队
   ├── claude --permission-mode bypassPermissions --print --teammate-mode in-process
   ├── 输入任务描述 + 通知命令
   └── 发送 "1" 确认安全

3. 监控进度
   ├── process poll 查看状态
   └── process log 查看输出

4. 接收通知
   ├── Agent 完成 → 自动触发 system event
   ├── OpenClaw 收到通知
   └── 向用户汇报结果

5. 后续操作
   ├── git diff 查看变更
   ├── git commit && git push
   └── 继续开发或修复
```

---

## 八、相关配置

### Claude Code 配置位置

- 全局设置：`~/.claude/settings.json`
- 团队配置：`~/.claude/teams/{team-name}/config.json`
- 任务列表：`~/.claude/tasks/{team-name}/`

### OpenClaw 配置

- 记忆文件：`~/testcase-generator/AGENT_TEAMS_GUIDE.md`（本文档）
- GitHub Token：环境变量 `GH_TOKEN` 或 `gh auth`
