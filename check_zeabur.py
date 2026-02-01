#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===================================
WebUI 启动测试工具（无 emoji 版本）
===================================
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def main():
    print("\n" + "=" * 60)
    print("WebUI 启动测试工具")
    print("=" * 60)
    print()

    # 测试 1: 模块导入
    print("[测试 1/3] 模块导入...")
    try:
        import web.server
        import web.router
        import web.handlers
        import web.templates
        import web.services
        import src.config
        print("  OK - 所有模块导入成功")
    except Exception as e:
        print(f"  FAILED - {e}")
        return 1

    # 测试 2: 配置加载
    print()
    print("[测试 2/3] 配置加载...")
    try:
        from src.config import get_config
        config = get_config()
        print(f"  OK - webui_enabled={config.webui_enabled}")
        print(f"         webui_host={config.webui_host}")
        print(f"         webui_port={config.webui_port}")
    except Exception as e:
        print(f"  FAILED - {e}")
        return 1

    # 测试 3: WebUI 启动
    print()
    print("[测试 3/3] WebUI 启动...")
    try:
        from web.server import run_server_in_thread
        thread = run_server_in_thread(
            host=config.webui_host,
            port=config.webui_port
        )
        print(f"  OK - WebUI 启动成功")
        print(f"       地址: http://{config.webui_host}:{config.webui_port}")
        print()
        print("可用的端点:")
        print("  GET  /              配置页面")
        print("  GET  /health        健康检查")
        print("  GET  /history       历史记录")
        print("  GET  /futures       期货监控")
        print()

    except Exception as e:
        print(f"  FAILED - {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("=" * 60)
    print("所有测试通过！")
    print("=" * 60)
    print()
    print("提示：如果本地测试通过，问题可能在 Zeabur 配置")
    print()
    print("请检查 Zeabur 控制台：")
    print("  1. 环境变量 -> WEBUI_ENABLED=true")
    print("  2. 端口设置 -> 8080")
    print("  3. 部署状态 -> Running (绿色)")
    print()
    print("按 Ctrl+C 退出...")
    print()

    # 保持运行
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n退出测试")
        return 0


if __name__ == "__main__":
    sys.exit(main())
