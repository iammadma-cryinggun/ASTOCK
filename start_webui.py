#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===================================
Zeabur WebUI 专用启动脚本
===================================
确保 Zeabur 部署时只运行 WebUI，不执行定时任务
"""

import sys
import os
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# 禁用定时任务（确保不会自动执行分析）
os.environ['SCHEDULE_ENABLED'] = 'false'

# 确保 WebUI 启用
if os.getenv('WEBUI_ENABLED', 'false').lower() != 'true':
    os.environ['WEBUI_ENABLED'] = 'true'

# 设置默认端口
if not os.getenv('WEBUI_PORT'):
    os.environ['WEBUI_PORT'] = '8000'

if not os.getenv('WEBUI_HOST'):
    os.environ['WEBUI_HOST'] = '0.0.0.0'


def main():
    """启动 WebUI 服务"""
    logger.info("=" * 60)
    logger.info("Zeabur WebUI 服务启动")
    logger.info("=" * 60)
    logger.info(f"运行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info()

    # 检查环境变量
    webui_enabled = os.getenv('WEBUI_ENABLED', 'false')
    webui_host = os.getenv('WEBUI_HOST', '127.0.0.1')
    webui_port = os.getenv('WEBUI_PORT', '8000')

    logger.info(f"配置信息:")
    logger.info(f"  WEBUI_ENABLED: {webui_enabled}")
    logger.info(f"  WEBUI_HOST: {webui_host}")
    logger.info(f"  WEBUI_PORT: {webui_port}")
    logger.info(f"  SCHEDULE_ENABLED: {os.getenv('SCHEDULE_ENABLED', 'false')}")
    logger.info()

    try:
        # 导入并启动 WebUI
        from web.server import run_server

        logger.info(f"WebUI 服务启动: http://{webui_host}:{webui_port}")
        logger.info("可用端点:")
        logger.info("  GET  /              配置页面")
        logger.info("  GET  /health        健康检查")
        logger.info("  GET  /history       历史记录")
        logger.info("  GET  /futures       期货监控")
        logger.info("  GET  /analysis?code=xxx  触发分析")
        logger.info()
        logger.info("按 Ctrl+C 退出...")
        logger.info()

        # 前台运行（阻塞）
        run_server(host=webui_host, port=webui_port)

    except KeyboardInterrupt:
        logger.info("\n用户中断，程序退出")
        return 0
    except Exception as e:
        logger.error(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
