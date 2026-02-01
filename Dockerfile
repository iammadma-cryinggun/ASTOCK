# Zeabur 专用 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装依赖
RUN apt-get update && apt-get install -y --no-install-recommends gcc curl && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY *.py ./
COPY data_provider/ ./data_provider/
COPY web/ ./web/
COPY bot/ ./bot/
COPY src/ ./src/

# 创建目录
RUN mkdir -p /app/data /app/logs /app/reports

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV WEBUI_ENABLED=true
ENV WEBUI_HOST=0.0.0.0
ENV WEBUI_PORT=8080
ENV SCHEDULE_ENABLED=false

# 暴露端口（容器内部端口 = Zeabur 外部端口）
EXPOSE 8080

# 健康检查使用容器内部端口
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 0

# 启动命令（强制使用 start_webui.py）
CMD ["python", "start_webui.py"]
