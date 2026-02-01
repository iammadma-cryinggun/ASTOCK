#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebUI 启动脚本 - Zeabur 专用
"""
import sys
import os
import time

print("=" * 60)
print("Zeabur WebUI 启动中...")
print("=" * 60)

# 强制设置环境变量
os.environ['SCHEDULE_ENABLED'] = 'false'
os.environ['WEBUI_ENABLED'] = 'true'
os.environ['WEBUI_HOST'] = '0.0.0.0'
os.environ['WEBUI_PORT'] = '8080'

print(f"配置: WEBUI_ENABLED={os.getenv('WEBUI_ENABLED')}")
print(f"配置: WEBUI_HOST={os.getenv('WEBUI_HOST')}")
print(f"配置: WEBUI_PORT={os.getenv('WEBUI_PORT')}")
print()

try:
    # 测试导入
    print("[1/3] 导入模块...")
    from web.server import run_server
    print("  OK")

    # 启动服务器
    print("[2/3] 启动 WebUI 服务器...")
    print(f"  地址: http://0.0.0.0:8080")
    print()

    print("[3/3] 运行中...")
    print("可用端点:")
    print("  GET  /              配置页面")
    print("  GET  /health        健康检查")
    print("  GET  /history       历史记录")
    print("  GET  /futures       期货监控")
    print()
    print("=" * 60)

    # 前台运行（阻塞）
    run_server(host='0.0.0.0', port=8080)

except KeyboardInterrupt:
    print("\n退出")
    sys.exit(0)
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
