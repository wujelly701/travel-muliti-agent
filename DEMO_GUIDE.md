# 旅行规划 Multi-Agent MVP - 启动与演示指南

## 🚀 快速启动

### 方式一：使用启动脚本（推荐）
```powershell
.\start_server.ps1
```

### 方式二：手动启动
```powershell
# 1. 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 2. 设置 PYTHONPATH
$env:PYTHONPATH = "src"

# 3. 启动服务
uvicorn travel_agent.api:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问：
- **API 文档**: http://127.0.0.1:8000/docs
- **健康检查**: http://127.0.0.1:8000/health
- **Metrics**: http://127.0.0.1:8000/metrics
- **Prometheus**: http://127.0.0.1:8000/metrics_prom

---

## 🎯 演示完整流程

### 1️⃣ 健康检查
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
```

**预期响应**:
```json
{
  "status": "healthy",
  "service": "Travel Agent MVP"
}
```

---

### 2️⃣ 发起规划请求（信息不完整 - 触发澄清）
```powershell
$planRequest = @{
    session_id = "demo_001"
    text = "预算5000 3天旅行"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/mvp/plan" `
    -Method Post `
    -Body $planRequest `
    -ContentType "application/json"
```

**预期响应** (澄清模式):
```json
{
  "success": false,
  "mode": "clarify",
  "questions": [
    {
      "field": "destination",
      "question_text": "请问您想去哪个城市旅行？",
      "suggestions": ["北京", "上海", "杭州", "成都"]
    },
    {
      "field": "depart_date",
      "question_text": "请问您的出发日期是？",
      "format": "YYYY-MM-DD"
    }
  ],
  "round": 1,
  "max_rounds": 3
}
```

---

### 3️⃣ 回答澄清问题
```powershell
$clarifyRequest = @{
    session_id = "demo_001"
    answers = @{
        destination = "杭州"
        depart_date = "2025-12-20"
    }
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/mvp/clarify" `
    -Method Post `
    -Body $clarifyRequest `
    -ContentType "application/json"

# 美化输出
$result | ConvertTo-Json -Depth 10
```

**预期响应** (完整规划结果):
```json
{
  "success": true,
  "data": {
    "session_id": "demo_001",
    "schema_version": "1.0",
    "intent": {
      "destination": "杭州",
      "depart_date": "2025-12-20",
      "return_date": "2025-12-22",
      "days": 3,
      "nights": 2,
      "budget_total": 5000.0,
      "currency": "CNY",
      "travelers": 1
    },
    "flights": [...],  // 5个航班选项
    "hotels": [...],   // 5个酒店选项
    "itinerary": {
      "days": [
        {
          "day_index": 1,
          "date": "2025-12-20",
          "main_spots": ["西湖", "断桥"],
          "meals": ["午餐: 楼外楼", "晚餐: 知味观"]
        },
        // ... 其他天数
      ],
      "summary": "3天杭州经典游"
    },
    "budget": {
      "total": 5000.0,
      "currency": "CNY",
      "transportation": 1500.0,
      "accommodation": 1250.0,
      "food": 1000.0,
      "attractions": 750.0,
      "other": 500.0,
      "warnings": []  // 可能包含 DAILY_BUDGET_TOO_LOW 等警告
    }
  }
}
```

---

### 4️⃣ 查看系统指标
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/metrics" -Method Get
```

**关键指标**:
```json
{
  "llm_calls": 1,
  "llm_errors": 0,
  "llm_fallbacks": 0,
  "clarify_sessions": 1,
  "clarify_rounds_total": 2,
  "cache_hits": 0,
  "cache_misses": 1,
  "workflow_count": 1
}
```

---

### 5️⃣ 查看 Prometheus 格式指标
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/metrics_prom" -Method Get
```

**输出示例**:
```
# TYPE workflow_latency_seconds histogram
workflow_latency_seconds_sum 2.543
workflow_latency_seconds_count 1
...
llm_calls_total 1
cache_hits_total 0
cache_misses_total 1
```

---

### 6️⃣ 查看错误日志
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/errors_recent?limit=10" -Method Get
```

---

### 7️⃣ 查看 LLM 调用审计
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/llm_audit_recent?limit=5" -Method Get
```

**输出示例**:
```json
{
  "records": [
    {
      "timestamp": "2025-11-14T10:30:45",
      "model_name": "gpt-4o-mini",
      "prompt_preview": "生成3天杭州行程...",
      "response_preview": "{\"days\": [{\"day_index\": 1...}",
      "duration_ms": 1234.5,
      "success": true
    }
  ]
}
```

---

## 🧪 测试缓存功能

**第一次请求**（缓存未命中）:
```powershell
$req = @{ session_id = "cache_test"; text = "去北京 2025-12-01 5天 预算8000" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/mvp/plan" -Method Post -Body $req -ContentType "application/json"
```

**第二次相同请求**（缓存命中，速度快）:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/mvp/plan" -Method Post -Body $req -ContentType "application/json"
```

查看 Metrics，应该看到 `cache_hits: 1`

---

## 🚦 测试限流功能

```powershell
# 快速发送多个请求（超过限制）
1..35 | ForEach-Object {
    $req = @{ session_id = "rate_test"; text = "测试 $_" } | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/mvp/plan" -Method Post -Body $req -ContentType "application/json" -ErrorAction Stop
    } catch {
        Write-Host "请求 $_ 被限流" -ForegroundColor Yellow
    }
}
```

预期：前 30 个请求成功，之后返回 `RATE_LIMIT_EXCEEDED` 错误。

---

## 🎨 核心特性展示

### ✅ 已实现功能
- ✅ 意图解析（正则提取 + 差距检测）
- ✅ 多轮澄清（最多 3 轮）
- ✅ LLM 行程生成（fallback 链 + JSON 修复）
- ✅ 预算分配 + 真实性警告
- ✅ 结果缓存（intent 哈希）
- ✅ 限流控制（滑动窗口）
- ✅ 指标收集（内部计数器 + Prometheus）
- ✅ 错误追踪（环形缓冲区）
- ✅ LLM 审计（提示/响应日志）

### 📊 预算警告类型
- `BUDGET_ESTIMATED` - 预算被自动估算
- `TRANSPORT_BUDGET_LOW` - 交通预算不足
- `DAILY_BUDGET_TOO_LOW` - 每日预算 < 150 CNY（不现实）
- `DAILY_BUDGET_TOO_HIGH` - 每日预算 > 8000 CNY（奢华级别）

---

## 🔧 环境变量配置

```powershell
# LLM 配置
$env:LLM_PRIMARY = "gpt-4o-mini"
$env:LLM_FALLBACKS = "gpt-3.5-turbo,deepseek-chat"
$env:OPENAI_API_KEY = "sk-..."
$env:DEEPSEEK_API_KEY = "sk-..."

# 限流配置
$env:RATE_LIMIT_REQUESTS_PER_MIN = "30"
$env:RATE_LIMIT_WINDOW_SECONDS = "60"

# Redis（可选，默认使用内存）
$env:REDIS_URL = "redis://localhost:6379/0"

# 其他
$env:CLARIFY_MAX_ROUNDS = "3"
$env:LLM_MAX_REPAIR = "3"
```

---

## 🧹 清理与维护

### 清除缓存
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/cache/clear" -Method Post
```

### 运行测试套件
```powershell
$env:PYTHONPATH = "src"
pytest -q  # 21 个测试全部通过
```

### 查看日志
结构化 JSON 日志输出到控制台，包含：
- 请求 ID、会话 ID
- LLM 调用详情
- 错误堆栈
- 延迟指标

---

## 📦 下一步增强建议

1. **Docker 容器化**
   ```dockerfile
   FROM python:3.11-slim
   COPY . /app
   RUN pip install -r requirements.txt
   CMD ["uvicorn", "travel_agent.api:app", "--host", "0.0.0.0"]
   ```

2. **API 认证**
   - JWT token 或 API key 中间件
   - 速率限制按用户而非会话

3. **生产就绪**
   - 持久化 Redis（缓存 + 会话）
   - 配置 Prometheus 抓取
   - 添加 Sentry 错误监控
   - HTTPS 反向代理（Nginx/Traefik）

4. **真实数据源**
   - 接入携程/飞猪 API
   - 实时航班/酒店查询
   - UGC 内容集成

---

## 💡 提示

- 首次请求可能较慢（LLM 调用），后续相同请求会命中缓存
- 查看 Swagger UI (`/docs`) 可交互式测试所有端点
- 修改代码后服务自动重载（`--reload` 模式）
- 所有测试无警告通过（httpx 警告已过滤）

**祝使用愉快！** 🎉
