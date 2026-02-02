@echo off
echo ============================================================
echo A股智能分析系统 - WebUI 启动脚本
echo ============================================================
echo.

echo [1/3] 检查环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)

echo.
echo [2/3] 安装依赖...
python -m pip install -q scipy yfinance requests pandas numpy

echo.
echo [3/3] 启动 WebUI 服务器...
echo.
echo ============================================================
echo WebUI 运行中:
echo   本地访问: http://localhost:8080
echo   期货监控: http://localhost:8080/futures
echo   历史记录: http://localhost:8080/history
echo.
echo 按 Ctrl+C 停止服务器
echo ============================================================
echo.

python start_webui.py

pause
