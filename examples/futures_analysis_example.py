#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===================================
期货波动率监控示例脚本
===================================

使用方法：
    python examples/futures_analysis_example.py

监控标的：
- 贵金属：GLD（黄金）、SLV（白银）
- 商品：USO（原油）、UNG（天然气）
- 大宗商品：DBC、DBA
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from src.config import get_config
from src.futures_monitor import get_volatility_monitor
from src.notification import NotificationService


def main():
    """主函数"""
    print("=" * 60)
    print("📊 期货/贵金属期权波动率监控")
    print("=" * 60)
    print()

    # 获取配置
    config = get_config()

    # 创建监控器（需要数据提供者）
    # TODO: 需要实现数据提供者接口
    monitor = get_volatility_monitor()

    # 监控的标的列表
    symbols = ['GLD', 'SLV', 'IAU', 'USO', 'UNG', 'DBC']

    print(f"正在分析 {len(symbols)} 个标的...")
    print()

    try:
        # 生成风险报告
        report = monitor.generate_risk_report(symbols)

        # 打印报告
        print(report)

        # 获取极端风险标的
        extreme_symbols = monitor.get_extreme_risk_symbols(symbols)

        if extreme_symbols:
            print()
            print("⚠️  检测到极端风险标的，建议谨慎操作！")
            print()

        # 如果配置了通知，发送报告
        if config.wechat_webhook_url or config.feishu_webhook_url:
            notifier = NotificationService()

            # 构造通知消息
            if extreme_symbols:
                title = "🚨 期货波动率极端风险预警"
                content = f"检测到 {len(extreme_symbols)} 个极端风险标的：\n\n"
                for metrics in extreme_symbols:
                    content += f"🔴 {metrics.name} ({metrics.symbol})\n"
                    content += f"IV: {metrics.iv_current:.2f}% | HV: {metrics.hv_20d:.2f}%\n"
                    content += f"背离度: {metrics.iv_hv_divergence:.2f}%\n\n"
            else:
                title = "📊 期货波动率监控报告"
                content = f"已分析 {len(symbols)} 个标的，未检测到极端风险。"

            # 发送通知
            notifier.send(content)

            print("✅ 报告已发送到通知渠道")

    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
