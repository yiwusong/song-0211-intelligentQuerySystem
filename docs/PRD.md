# 智能查询系统 (Intelligent Query System) — 产品需求文档

> **版本**: v1.0  
> **创建日期**: 2026-02-11  
> **状态**: 初稿  
> **项目代号**: project-0211-IntelligentQuerySystem

---

## 1. 项目概述

### 1.1 背景

业务人员在日常数据分析中，常因不熟悉 SQL 语法或数据库表结构而依赖开发人员手动查询，效率低下、响应周期长。需要一套**自然语言驱动的智能查询与可视化系统**，让用户用日常语言提问，系统自动生成 SQL、执行查询并以可视化图表呈现结果。

### 1.2 产品目标

- 用户通过自然语言描述数据需求，系统自动完成 **意图理解 → SQL 生成 → 查询执行 → 图表渲染** 全流程
- 提供**流式交互体验**，实时展示思考过程、SQL 预览和可视化结果
- 确保数据安全，严格限制为**只读查询**，杜绝任何写操作风险

### 1.3 目标用户

| 角色 | 描述 |
|------|------|
| 业务分析师 | 需要频繁查看数据报表，不熟悉 SQL |
| 产品经理 | 临时性数据查询需求，希望快速获取数据洞察 |
| 管理层 | 需要直观的数据可视化来辅助决策 |

---

## 2. 系统架构

### 2.1 整体分层架构

```
┌─────────────────────────────────────────────────┐
│               前端可视化层 (Frontend)              │
│          React (Vite) + Apache ECharts            │
├─────────────────────────────────────────────────┤
│               后端服务层 (Backend)                 │
│            FastAPI + SSE 流式推送                  │
├─────────────────────────────────────────────────┤
│             AI 核心逻辑层 (AI Engine)              │
│       Single-Model Chain-of-Thought (Claude)      │
├─────────────────────────────────────────────────┤
│            数据与 RAG 层 (Data & RAG)              │
│         Vector Store + Schema 语义检索             │
├─────────────────────────────────────────────────┤
│            安全与治理层 (Security)                  │
│         SQL 防火墙 + 只读权限隔离                   │
└─────────────────────────────────────────────────┘
```

### 2.2 数据流

```
用户提问 → SSE 连接建立
       → Schema 语义检索 (RAG)
       → LLM 生成 (Thinking + SQL + Viz Config)
       → SQL 安全校验 (AST 解析)
       → 数据库只读查询
       → 流式推送结果 → 前端渲染图表
```

---

## 3. 功能需求

### 3.1 后端服务层 (Backend Service)

- **核心框架**: FastAPI (Python)
- **优先级**: P0

| 功能点 | 描述 | 验收标准 |
|--------|------|---------|
| SSE 流式接口 | 基于 Server-Sent Events 协议，后端单向推送事件流 | 支持 `event: thought`、`event: sql`、`event: viz_config`、`event: error` 四种事件类型 |
| 异步处理 | 全链路异步，不阻塞请求线程 | 使用 `async/await`，支持并发请求 |
| 状态流转管理 | 管理 Prompt → SQL 生成 → 校验 → 自动修正 → 再次生成 的状态机 | 使用 LangGraph 或简单 State Machine 实现；SQL 校验失败时自动重试，最多 3 次 |
| 健康检查 | 提供服务健康状态接口 | `GET /health` 返回 200 |

**SSE 事件协议定义**:

```
event: thought
data: {"content": "用户想查询近 30 天的销售趋势..."}

event: sql
data: {"content": "SELECT date, SUM(amount) FROM orders WHERE ..."}

event: viz_config
data: {"echarts_option": { ... ECharts JSON 配置 ... }}

event: error
data: {"code": "SQL_VALIDATION_FAILED", "message": "..."}
```

### 3.2 数据与 RAG 层 (Data & Schema RAG)

- **优先级**: P0

| 功能点 | 描述 | 验收标准 |
|--------|------|---------|
| Schema 预处理 | 提取所有表的 `CREATE TABLE` 语句 + 字段注释 | 自动解析数据库元数据，生成结构化描述文本 |
| Schema Embedding | 将表结构描述向量化，存入向量数据库 | 使用 ChromaDB 或 Qdrant 作为 Vector Store |
| 语义检索 | 用户提问时，语义召回 Top-5~10 相关表的 Schema | 检索延迟 < 200ms；召回结果包含表名、字段、注释 |
| Schema 增量更新 | 数据库表结构变更时同步更新向量索引 | 支持手动触发 / 定时扫描更新 |

**技术路径**:

1. **预处理**: 连接业务数据库 → 提取 DDL + 字段注释 → 生成自然语言描述
2. **Embedding**: 调用 Embedding 模型 → 存入 Vector Store
3. **检索 (Retrieval)**: 用户提问 → 语义相似度匹配 → 返回 Top-K Schema → 注入 Prompt 上下文

### 3.3 AI 核心逻辑层 (Single-Model Engine)

- **优先级**: P0

| 功能点 | 描述 | 验收标准 |
|--------|------|---------|
| 模型策略 | 单一强模型 Chain-of-Thought | 使用 Claude-3.5-Sonnet (或同级别模型) |
| 三段式输出 | 一次请求输出 Thinking → SQL → Viz Config | 模型在单次回复中按顺序输出三个部分 |
| 结构化输出 | 强制 JSON 格式输出 | 使用 Pydantic 模型约束，包含 `thinking`、`sql`、`echarts_option` 字段 |
| 上下文注入 | 将 RAG 检索的 Schema 注入 System Prompt | Prompt 模板包含：系统角色 + Schema 上下文 + 用户问题 |

**输出 Schema 定义 (Pydantic)**:

```python
class QueryResponse(BaseModel):
    thinking: str           # 思考分析过程
    sql: str                # 生成的 SQL 语句
    echarts_option: dict    # ECharts 标准 JSON 配置对象
```

### 3.4 前端可视化层 (Frontend & Visualization)

- **优先级**: P1

| 功能点 | 描述 | 验收标准 |
|--------|------|---------|
| 查询输入框 | 自然语言输入区域 | 支持回车发送；支持输入历史 |
| 流式展示 | 实时展示 SSE 事件流内容 | 依次渲染"思考中..." → SQL 代码预览 → 图表 |
| 通用图表组件 | `<EChartsRenderer option={data} />` 声明式渲染 | 前端不写绘图逻辑，透传后端 JSON 配置 |
| 三种核心图表 | 支持**柱形图 (bar)**、**饼状图 (pie)**、**曲线图 (line)** 三种可视化类型 | LLM 根据数据语义自动推荐默认图表类型；用户可通过图表上方的切换按钮自由选择任意一种图表类型，切换后实时重新渲染 |
| SQL 预览 | 展示生成的 SQL（带语法高亮） | 用户可查看但不可编辑（MVP 阶段） |
| 错误提示 | 友好展示错误信息 | 接收 `event: error` 后展示可读的错误说明 |

**技术选型**:
- 框架: React (Vite)
- 图表引擎: Apache ECharts
- SSE 接收: `fetch` (ReadableStream) 或 `EventSource`

### 3.5 安全与治理层 (Security & Governance)

- **优先级**: P0

| 功能点 | 描述 | 验收标准 |
|--------|------|---------|
| SQL 防火墙 | 使用 `sqlglot` 解析 SQL AST | 根节点必须为 `SELECT`；拦截 `DROP`/`DELETE`/`UPDATE`/`TRUNCATE`/`GRANT` 等写操作 |
| 物理隔离 | 数据库连接使用 Read-Only 用户 | 数据库层面创建只读账户，连接池绑定该账户 |
| 查询限制 | 防止全表扫描和超大结果集 | 自动添加 `LIMIT`（默认 1000 行）；查询超时限制 30s |
| 日志审计 | 记录所有查询请求和结果 | 日志包含：用户问题、生成 SQL、执行耗时、结果行数 |

---

## 4. 非功能需求

| 维度 | 要求 |
|------|------|
| **性能** | Schema 检索 < 200ms；SQL 生成 (LLM) < 10s；查询执行 < 30s |
| **并发** | MVP 阶段支持 10 个并发用户 |
| **可用性** | 服务可用性 > 99%（MVP 阶段） |
| **安全** | 严格只读访问；SQL 注入防护；敏感字段脱敏（后续迭代） |
| **可扩展性** | 模块化设计，支持后续替换 LLM 模型、新增数据源 |

---

## 5. 技术栈总览

| 层级 | 技术选型 |
|------|---------|
| 前端 | React (Vite) + TypeScript + Apache ECharts |
| 后端 | Python 3.11+ + FastAPI + Uvicorn |
| AI 模型 | Claude-3.5-Sonnet (Anthropic API) |
| 向量数据库 | ChromaDB（MVP）/ Qdrant（生产） |
| 业务数据库 | PostgreSQL（推荐）/ MySQL |
| ORM/驱动 | SQLAlchemy / asyncpg |
| SQL 安全 | sqlglot (AST 解析) |
| 状态管理 | LangGraph / 自定义 State Machine |

---

## 6. MVP 开发路径

### Phase 1: 基础骨架（第 1-2 周）

- [ ] 搭建 FastAPI 项目框架 + SSE 流式接口原型
- [ ] 搭建 React (Vite) 前端项目 + SSE 监听原型
- [ ] 实现 Schema 预处理脚本（提取 DDL + 注释）
- [ ] 搭建 ChromaDB 向量数据库 + Schema Embedding 入库
- [ ] 实现 Schema 语义检索接口

### Phase 2: AI 核心链路（第 3-4 周）

- [ ] 设计 System Prompt 模板（三段式输出约束）
- [ ] 实现 LLM 调用 + Pydantic 结构化输出解析
- [ ] 实现 SQL 防火墙（sqlglot AST 校验）
- [ ] 实现状态机（生成 → 校验 → 修正 → 重试）
- [ ] 打通全链路：提问 → RAG → LLM → SQL 执行 → 返回结果

### Phase 3: 前端可视化（第 5-6 周）

- [ ] 实现 `<EChartsRenderer />` 通用图表组件
- [ ] 实现流式 UI：思考过程 → SQL 预览 → 图表渲染
- [ ] 实现查询历史列表
- [ ] UI 美化 + 错误处理 + Loading 状态
- [ ] 端到端联调测试

### Phase 4: 安全加固 & 上线（第 7-8 周）

- [ ] 数据库只读用户配置 + 连接池隔离
- [ ] 查询限制（LIMIT / 超时 / 结果集大小）
- [ ] 日志审计系统
- [ ] 部署方案（Docker Compose）
- [ ] 性能测试 + Bug 修复

---

## 7. 约束与依赖

| 项目 | 说明 |
|------|------|
| 外部 API | 依赖 Anthropic Claude API（需申请 API Key） |
| 数据库访问 | 需要业务数据库的只读账户和网络连通性 |
| 表注释质量 | Schema RAG 效果强依赖于数据库字段注释的完整度 |
| 模型成本 | Claude-3.5-Sonnet 按 Token 计费，需监控用量 |

---

## 8. 变更记录

| 日期 | 版本 | 修改内容 | 修改人 |
|------|------|---------|--------|
| 2026-02-11 | v1.0 | 初稿，包含 5 层架构设计和 MVP 开发路径 | — |
