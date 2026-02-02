@echo off
echo ============================================================
echo A股智能分析系统 - WebUI 启动脚本（代理模式）
echo ============================================================
echo.

REM 设置代理（修改为您的代理地址和端口）
REM 如果使用 VPN，通常不需要设置，VPN 会自动代理
REM 如果使用 HTTP 代理，取消下面的注释并修改地址

REM SET HTTP_PROXY=http://127.0.0.1:10809
REM SET HTTPS_PROXY=http://127.0.0.1:10809

REM 如果使用 SOCKS5 代理（需要安装 pysocks）
REM SET ALL_SOCKS_PROXY=socks5://127.0.0.1:1080

echo [启动] WebUI 服务器...
echo.
echo ============================================================
echo WebUI 运行中:
echo   本地访问: http://localhost:8080
echo   期货监控: http://localhost:8080/futures
echo.
echo 按 Ctrl+C 停止服务器
echo ============================================================
echo.

python start_webui.py

pause
