# Travel Agent MVP - 启动脚本
# PowerShell script for Windows

Write-Host "==> 旅行规划 Multi-Agent MVP 启动中..." -ForegroundColor Cyan

# 1. 检查虚拟环境
if (!(Test-Path ".venv\Scripts\activate.ps1")) {
    Write-Host "错误: 未找到虚拟环境，请先运行: python -m venv .venv" -ForegroundColor Red
    exit 1
}

# 2. 激活虚拟环境
Write-Host "`n[1/3] 激活虚拟环境..." -ForegroundColor Yellow
. .venv\Scripts\Activate.ps1

# 3. 设置环境变量
Write-Host "[2/3] 配置 PYTHONPATH..." -ForegroundColor Yellow
$env:PYTHONPATH = "src"

# 4. 启动 FastAPI 服务
Write-Host "[3/3] 启动 FastAPI 服务 (http://127.0.0.1:8000)..." -ForegroundColor Yellow
Write-Host "`n  API 文档: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "  健康检查: http://127.0.0.1:8000/health" -ForegroundColor Green
Write-Host "  Metrics: http://127.0.0.1:8000/metrics" -ForegroundColor Green
Write-Host "  Prometheus: http://127.0.0.1:8000/metrics_prom`n" -ForegroundColor Green

uvicorn travel_agent.api:app --host 0.0.0.0 --port 8000 --reload
