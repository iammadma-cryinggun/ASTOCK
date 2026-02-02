# -*- coding: utf-8 -*-
"""
核心功能对比检查清单
对比 ZhuLinsen/daily_stock_analysis 原始功能与当前实现
"""

import os
import sys

print("=" * 80)
print("核心功能对比检查 - ZhuLinsen/daily_stock_analysis")
print("=" * 80)

# 检查配置文件
print("\n[配置文件检查]")
env_file = ".env"
if os.path.exists(env_file):
    print(f"  [OK] .env 文件存在")
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查关键配置
    checks = {
        "STOCK_LIST": "股票代码列表",
        "OPENAI_API_KEY": "AI 模型 API Key（支持 QWEN/Gemini/DeepSeek）",
        "TAVILY_API_KEYS": "新闻搜索引擎 API（可选）",
        "SERPAPI_API_KEYS": "备用搜索引擎 API（可选）",
    }

    for key, desc in checks.items():
        if key in content:
            value = os.getenv(key)
            status = "[OK]" if value and value != "" else "[WARN]"
            print(f"  {status} {key} - {desc}")
        else:
            print(f"  [INFO] {key} 未配置 - {desc}")
else:
    print(f"  [FAIL] .env 文件不存在")

# 检查核心模块
print("\n[核心模块检查]")
modules = [
    ("src/config.py", "配置管理"),
    ("src/analyzer.py", "AI 分析器"),
    ("src/data_fetcher.py", "数据获取"),
    ("src/notification.py", "通知推送"),
    ("src/core/pipeline.py", "分析管道"),
    ("src/search_service.py", "新闻搜索"),
    ("main.py", "主程序入口"),
]

for module_path, desc in modules:
    if os.path.exists(module_path):
        print(f"  [OK] {module_path} - {desc}")
    else:
        print(f"  [FAIL] {module_path} - {desc} 不存在")

# 检查 AI 模型配置
print("\n[AI 模型配置检查]")
try:
    from src.config import get_config
    config = get_config()

    print(f"  OpenAI API Key: {'[OK] 已配置' if config.openai_api_key else '[WARN] 未配置'}")
    print(f"  OpenAI Base URL: {config.openai_base_url or '未配置（使用默认）'}")
    print(f"  OpenAI Model: {config.openai_model or '未配置'}")
    print(f"  Gemini API Key: {'[OK] 已配置' if config.gemini_api_key else '[INFO] 未配置'}")

    # 检查是否至少配置了一个 AI 模型
    has_ai = config.openai_api_key or config.gemini_api_key
    if has_ai:
        print(f"  [OK] 至少配置了一个 AI 模型")
    else:
        print(f"  [FAIL] 未配置任何 AI 模型（必须配置 OPENAI_API_KEY 或 GEMINI_API_KEY）")

except Exception as e:
    print(f"  [FAIL] 配置加载失败: {e}")

# 检查通知渠道配置
print("\n[通知渠道配置检查]")
try:
    notification_checks = [
        ("EMAIL_SENDER", "邮箱推送"),
        ("WECHAT_WEBHOOK_URL", "企业微信推送"),
        ("FEISHU_WEBHOOK_URL", "飞书推送"),
        ("TELEGRAM_BOT_TOKEN", "Telegram 推送"),
    ]

    with open(env_file, 'r', encoding='utf-8') as f:
        env_content = f.read()

    for key, desc in notification_checks:
        if key in env_content:
            value = os.getenv(key)
            if value and value != "" and value != "xxxx":
                print(f"  [OK] {desc} 已配置")
            else:
                print(f"  [INFO] {desc} 未配置")
        else:
            print(f"  [INFO] {desc} 未配置")

    # 检查是否至少配置了一个通知渠道
    has_notification = any(
        os.getenv(key) and os.getenv(key) != "" and os.getenv(key) != "xxxx"
        for key, _ in notification_checks
    )

    if has_notification:
        print(f"  [OK] 至少配置了一个通知渠道")
    else:
        print(f"  [WARN] 未配置任何通知渠道（分析结果将无法推送）")

except Exception as e:
    print(f"  [WARN] 通知渠道检查失败: {e}")

# 检查 WebUI
print("\n[WebUI 检查]")
webui_files = [
    "web/server.py",
    "web/router.py",
    "web/handlers.py",
    "web/templates.py",
    "web/services.py",
]

all_exist = all(os.path.exists(f) for f in webui_files)
if all_exist:
    print(f"  [OK] WebUI 模块完整")
else:
    for f in webui_files:
        status = "[OK]" if os.path.exists(f) else "[FAIL]"
        print(f"  {status} {f}")

# 检查数据库
print("\n[数据库检查]")
try:
    from src.storage import DatabaseManager
    db = DatabaseManager.get_instance()
    print(f"  [OK] 数据库管理器初始化成功")

    # 检查数据库文件
    db_path = config.database_path
    if os.path.exists(db_path):
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"  [OK] 数据库文件存在: {db_path} ({size_mb:.2f} MB)")
    else:
        print(f"  [INFO] 数据库文件不存在（首次运行时会自动创建）: {db_path}")

except Exception as e:
    print(f"  [FAIL] 数据库检查失败: {e}")

# 检查定时任务
print("\n[定时任务检查]")
try:
    schedule_enabled = os.getenv("SCHEDULE_ENABLED", "false").lower() == "true"
    schedule_time = os.getenv("SCHEDULE_TIME", "18:00")

    if schedule_enabled:
        print(f"  [OK] 定时任务已启用: {schedule_time}")
    else:
        print(f"  [INFO] 定时任务未启用（SCHEDULE_ENABLED=false）")

except Exception as e:
    print(f"  [WARN] 定时任务检查失败: {e}")

print("\n" + "=" * 80)
print("功能对比总结")
print("=" * 80)

print("""
原始项目核心功能（ZhuLinsen/daily_stock_analysis）：

1. AI 决策仪表盘
   - 一句话核心结论 ✓
   - 精确买卖点位 ✓
   - 操作检查清单 ✓

2. 多维度分析
   - 技术面分析 ✓
   - 筹码分布 ✓
   - 舆情情报（新闻搜索）✓
   - 实时行情 ✓

3. 全球市场支持
   - A股（6位数字）✓
   - 港股（HK+5位数字）✓
   - 美股（字母代码）✓

4. 多渠道推送
   - 企业微信 ✓
   - 邮箱 ✓
   - 飞书 ✓
   - Telegram ✓
   - 钉钉 ✓

5. 自动化运行
   - 定时任务 ✓
   - GitHub Actions ✓

6. WebUI 快速分析
   - 查询分析页面 ✓
   - 历史记录页面 ✓
   - 实时任务状态 ✓

7. 部署方式
   - 本地运行 ✓
   - Docker 容器化 ✓
   - Zeabur 云部署 ✓

本项目的增强功能：
   - FinBERT 语义分析（可选，已禁用）
   - 更多数据源支持
   - 完整的 WebUI 界面
   - 数据库历史记录
""")

print("\n下一步建议：")
print("1. 确保 .env 中配置了 AI 模型（OPENAI_API_KEY 支持 QWEN）")
print("2. 确保 STOCK_LIST 中有股票代码")
print("3. 运行测试: python main.py --dry-run")
print("4. 如果正常，运行完整分析: python main.py")
print()
