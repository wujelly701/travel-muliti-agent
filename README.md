# Travel Agent MVP

Ref: `report-requirements-MVP-detailed-20251114.md` (schema_version 1.0)

## Scope
Implements backend MVP with:
- Intent parsing + multi-round clarification (auto-filled mock answers for now)
- Flight & Hotel mock search, spot fetch
- Itinerary generation (LLM manager: fallback chain + JSON repair loop)
- Budget allocation + realism warnings (daily too low/high, transport underfunded)
- Result caching (intent hash) to reduce repeat cost
- Rate limiting (sliding window per session)
- Observability: metrics counters + Prometheus, error tracker, LLM prompt audit
- REST API endpoints

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

### 意图解析与澄清（Clarify）规则更新（2025-11）
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
`POST /api/mvp/debug/intent` Body: `{ "session_id": "dbg1", "text": "预算3000 去杭州 3天" }` → 返回 `intent` 对象与 `gaps` 数组，方便验证解析结果。

### 运行测试
```powershell
$env:PYTHONPATH = "src"
pytest -q  # 21 passed, no warnings
```

## Endpoints (core)
- `POST /plan` initial planning (may respond with clarification questions)
- `POST /clarify` answer clarification and continue workflow
- `GET /metrics` JSON counters & histogram snapshot
- `GET /metrics_prom` Prometheus exposition format
- `GET /errors_recent` last N errors ring buffer
- `GET /llm_audit_recent` recent LLM prompt/response entries
- `POST /debug/intent` 解析原始文本并返回意图与缺失字段（开发调试）

## Configuration (env vars)
- `LLM_PRIMARY`, `LLM_FALLBACKS` comma list
- `LLM_MAX_REPAIR` JSON repair attempts
- `CLARIFY_MAX_ROUNDS` clarification loop cap
- `RATE_LIMIT_REQUESTS_PER_MIN` default 30
- `RATE_LIMIT_WINDOW_SECONDS` default 60
- `API_KEY` optional; when set, require header `X-API-Key`
- `OPENAI_API_KEY`, `DEEPSEEK_API_KEY` (if real models enabled)
- `REDIS_URL` (optional; in-memory fallback used for cache/session)

## Docker
### Build & Run (Docker only)
```bash
docker build -t travel-agent-mvp .
docker run -p 8000:8000 --env-file .env.example travel-agent-mvp
```

### Using docker-compose (with Redis)
```bash
docker compose up --build -d
```
Access: `http://localhost:8000/docs`

### Image Notes
- Uses Python 3.11 slim base
- Exposes port 8000 (uvicorn)
- Set `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` when enabling real LLM calls
- Add `REDIS_URL=redis://redis:6379/0` to use Redis cache/session

## Authentication (Optional API Key)
Set `API_KEY` in environment to enable simple key auth. Requests to planning endpoints must include:
```
X-API-Key: <your_key_value>
```
Omit `API_KEY` to run in open mode (no auth).

## Caching
- Automatic reuse when identical intent has no information gaps.
- Hash includes destination, dates, days, budget_total, travelers, preferences, language.
- Metrics: `cache_hits`, `cache_misses` counters.

## Rate Limiting
- Sliding window per `session_id`; returns error code `RATE_LIMIT_EXCEEDED` when exceeded.

## Budget Realism Warnings
- `BUDGET_ESTIMATED` when inferred.
- `TRANSPORT_BUDGET_LOW` transportation slice below cheapest flight.
- `DAILY_BUDGET_TOO_LOW` daily average < 150 CNY.
- `DAILY_BUDGET_TOO_HIGH` daily average > 8000 CNY.

## Metrics (selected counters)
- LLM calls, fallbacks, errors, clarification rounds.
- Workflow latency histogram (Prometheus).
- Cache hits/misses.

## Observability Buffers
- Error tracker ring (recent structured errors).
- Prompt audit ring (LLM prompts/responses + model + duration).

## Notes / Future
- Replace mock flight/hotel/spot with real providers.
- Persist sessions & cache (Redis/in-memory now).
- Add UGC, payments, WebSocket streaming.
- Harden security (auth, input validation) before production.
