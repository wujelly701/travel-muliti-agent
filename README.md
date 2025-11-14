# 旅行规划 Multi-Agent MVP（统一中文说明）

参考: `report-requirements-MVP-detailed-20251114.md` (schema_version 1.0)

## 范围 (Scope)
当前后端 MVP 包含：
- 意图解析 + 多轮澄清（必填: origin, destination, depart_date, days）
- 航班 / 酒店 Mock 检索 + 景点占位数据
- 行程生成（LLM fallback 链 + JSON 修复）
- 预算分配 + 现实性警告
- 结果缓存（意图哈希）
- 会话级限流
- 指标 & Prometheus + 错误追踪 + LLM 调用审计
- Debug 意图端点 `/api/mvp/debug/intent`
- 可选认证：API Key / JWT Token

## Quick Start

### 启动服务
```powershell
# 方式一: 使用启动脚本
.\start_server.ps1

# 方式二: 手动启动
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "src"
uvicorn travel_agent.api:app --host 0.0.0.0 --port 8000 --reload
```

访问:
- Swagger UI: http://127.0.0.1:8000/docs
- 健康检查: http://127.0.0.1:8000/health
- 指标: http://127.0.0.1:8000/metrics

### 演示完整流程
详见 **[DEMO_GUIDE.md](DEMO_GUIDE.md)** - 包含完整的 API 调用示例、缓存测试、限流演示

### 意图解析与澄清规则（2025-11 更新）
现在“出发地 origin”是必填字段；如果初始文本中缺失，将进入澄清模式返回问题列表。必填字段：`origin`, `destination`, `depart_date`, `days`（预算 `budget_total` 可缺失，会被询问）。

示例：
```text
预算3000 去杭州 3天 2025-12-10
```
缺少出发地 → 返回 `questions` 包含 `origin`。

加入出发地：
```text
从上海 预算3000 去杭州 3天 2025-12-10
```
所有关键字段齐全 → 直接执行工作流，返回 itinerary + budget 分配。

调试端点：
`POST /api/mvp/debug/intent` Body: `{ "session_id": "dbg1", "text": "预算3000 去杭州 3天" }` → 返回 `intent` 与 `gaps`。

### 运行测试
```powershell
$env:PYTHONPATH = "src"
pytest -q  # 21 passed, no warnings
```

## 核心端点 (Endpoints)
- `POST /plan` initial planning (may respond with clarification questions)
- `POST /clarify` answer clarification and continue workflow
- `GET /metrics` JSON counters & histogram snapshot
- `GET /metrics_prom` Prometheus exposition format
- `GET /errors_recent` last N errors ring buffer
- `GET /llm_audit_recent` 最近 LLM 调用审计
- `POST /api/mvp/debug/intent` 解析原始文本并返回意图与缺失字段
- `POST /api/mvp/auth/token` 获取 JWT 访问令牌（在启用 JWT 时）
- `POST /api/mvp/plan_v2` 并行航班+酒店（asyncio）
- `POST /api/mvp/plan_v3` LangGraph 图调度（航班/酒店并行 → 景点 → 行程 → 预算）

## 配置 (环境变量)
- `LLM_PRIMARY`, `LLM_FALLBACKS` comma list
- `LLM_MAX_REPAIR` JSON repair attempts
- `CLARIFY_MAX_ROUNDS` clarification loop cap
- `RATE_LIMIT_REQUESTS_PER_MIN` default 30
- `RATE_LIMIT_WINDOW_SECONDS` default 60
-- `API_KEY` 可选；设置后需 `X-API-Key`
- `OPENAI_API_KEY`, `DEEPSEEK_API_KEY` (if real models enabled)
-- `REDIS_URL` 可选；未设置使用内存
-- `JWT_ENABLE` 是否启用 JWT（true/false）
-- `AUTH_JWT_SECRET` JWT 签名密钥
-- `AUTH_JWT_ALG` 签名算法（默认 HS256）
-- `AUTH_JWT_EXPIRE_MIN` 过期时间（分钟）
-- `AUTH_DEMO_USER` / `AUTH_DEMO_PASSWORD` 演示账户

## Docker
### 构建 & 运行（Docker）
```bash
docker build -t travel-agent-mvp .
docker run -p 8000:8000 --env-file .env.example travel-agent-mvp
```

### 使用 docker-compose（含 Redis 可选）
```bash
docker compose up --build -d
```
Access: `http://localhost:8000/docs`

### 镜像说明
- Uses Python 3.11 slim base
- Exposes port 8000 (uvicorn)
- Set `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` when enabling real LLM calls
- Add `REDIS_URL=redis://redis:6379/0` to use Redis cache/session

## 认证
1. API Key：设置 `API_KEY` 后在请求头添加 `X-API-Key`
2. JWT：设置 `JWT_ENABLE=true` 与 `AUTH_JWT_SECRET` 后，通过 `POST /api/mvp/auth/token` 获取令牌；后续请求头 `Authorization: Bearer <token>`。
两者同时设置时任一合法方式即可访问。

## 缓存
- Automatic reuse when identical intent has no information gaps.
- Hash includes destination, dates, days, budget_total, travelers, preferences, language.
- Metrics: `cache_hits`, `cache_misses` counters.

## 限流
- Sliding window per `session_id`; returns error code `RATE_LIMIT_EXCEEDED` when exceeded.

## 预算真实性告警
- `BUDGET_ESTIMATED` when inferred.
- `TRANSPORT_BUDGET_LOW` transportation slice below cheapest flight.
- `DAILY_BUDGET_TOO_LOW` daily average < 150 CNY.
- `DAILY_BUDGET_TOO_HIGH` daily average > 8000 CNY.

## 指标（部分）
- LLM calls, fallbacks, errors, clarification rounds.
- Workflow latency histogram (Prometheus).
- Cache hits/misses.

## 观测缓冲区
- Error tracker ring (recent structured errors).
- Prompt audit ring (LLM prompts/responses + model + duration).

## 后续计划
- 接入真实航班/酒店/景点 API
- 引入 LangGraph 并行多 Agent 调度
- 图执行状态与可视化（plan_v3 进一步扩展）
- 增加 UGC 内容聚合与 RAG 检索
- 完善多币种与预算动态建议
- 安全增强（OAuth2 Scope、输入校验、风控）
- 前端 UI 与实时 WebSocket 推送
