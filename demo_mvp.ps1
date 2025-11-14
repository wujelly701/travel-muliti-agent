# Travel Agent MVP - 测试演示脚本
# 展示完整的旅行规划流程

Write-Host "==> 旅行规划 MVP 演示" -ForegroundColor Cyan
Write-Host "确保服务已启动: .\start_server.ps1`n" -ForegroundColor Yellow

$baseUrl = "http://127.0.0.1:8000"
$sessionId = "demo_" + (Get-Date -Format "yyyyMMdd_HHmmss")

# 函数：美化 JSON 输出
function Show-Response {
    param($response, $title)
    Write-Host "`n===== $title =====" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10 | Write-Host
}

# 1. 健康检查
Write-Host "[1/6] 健康检查..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Show-Response $health "Health Check"
} catch {
    Write-Host "错误: 服务未启动或无法访问" -ForegroundColor Red
    exit 1
}

# 2. 发起规划请求 (信息不完整 - 触发澄清)
Write-Host "`n[2/6] 发起规划请求 (缺少目的地)..." -ForegroundColor Cyan
$planRequest = @{
    session_id = $sessionId
    text = "预算5000 3天旅行"
} | ConvertTo-Json
$planResult = Invoke-RestMethod -Uri "$baseUrl/api/mvp/plan" -Method Post -Body $planRequest -ContentType "application/json"
Show-Response $planResult "Plan Response (Clarification)"

# 3. 回答澄清问题
if ($planResult.mode -eq "clarify") {
    Write-Host "`n[3/6] 回答澄清问题..." -ForegroundColor Cyan
    $clarifyRequest = @{
        session_id = $sessionId
        answers = @{
            destination = "杭州"
            depart_date = "2025-12-20"
        }
    } | ConvertTo-Json
    $finalResult = Invoke-RestMethod -Uri "$baseUrl/api/mvp/clarify" -Method Post -Body $clarifyRequest -ContentType "application/json"
    Show-Response $finalResult "Final Planning Result"
    
    # 显示核心信息摘要
    Write-Host "`n===== 规划摘要 =====" -ForegroundColor Magenta
    Write-Host "目的地: $($finalResult.data.intent.destination)"
    Write-Host "出发日期: $($finalResult.data.intent.depart_date)"
    Write-Host "返程日期: $($finalResult.data.intent.return_date)"
    Write-Host "预算总额: $($finalResult.data.budget.total) $($finalResult.data.budget.currency)"
    Write-Host "航班数: $($finalResult.data.flights.Count)"
    Write-Host "酒店数: $($finalResult.data.hotels.Count)"
    Write-Host "行程天数: $($finalResult.data.itinerary.days.Count)"
    if ($finalResult.data.budget.warnings.Count -gt 0) {
        Write-Host "预算警告: $($finalResult.data.budget.warnings -join ', ')" -ForegroundColor Yellow
    }
}

# 4. 查看 Metrics
Write-Host "`n[4/6] 查看系统指标..." -ForegroundColor Cyan
$metrics = Invoke-RestMethod -Uri "$baseUrl/metrics" -Method Get
Show-Response $metrics "System Metrics"

# 5. 查看错误追踪
Write-Host "`n[5/6] 查看错误日志..." -ForegroundColor Cyan
$errors = Invoke-RestMethod -Uri "$baseUrl/errors_recent" -Method Get
if ($errors.errors.Count -eq 0) {
    Write-Host "无错误记录" -ForegroundColor Green
} else {
    Show-Response $errors "Recent Errors"
}

# 6. 查看 LLM 审计日志
Write-Host "`n[6/6] 查看 LLM 调用记录..." -ForegroundColor Cyan
$audit = Invoke-RestMethod -Uri "$baseUrl/llm_audit_recent" -Method Get
if ($audit.records.Count -gt 0) {
    Write-Host "LLM 调用次数: $($audit.records.Count)"
    $audit.records | ForEach-Object {
        Write-Host "  - 模型: $($_.model_name), 耗时: $($_.duration_ms)ms" -ForegroundColor Gray
    }
} else {
    Write-Host "无 LLM 调用记录" -ForegroundColor Gray
}

Write-Host "`n==> 演示完成！" -ForegroundColor Green
Write-Host "访问 Swagger UI: $baseUrl/docs" -ForegroundColor Cyan
