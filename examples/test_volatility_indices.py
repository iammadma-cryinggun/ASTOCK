#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===================================
波动率指数测试脚本
===================================

测试真实的 VIX、GVZ、OVX 等波动率指数获取功能

使用方法：
    python examples/test_volatility_indices.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.volatility_index import get_volatility_fetcher


def main():
    """测试函数"""
    print("=" * 60)
    print("🧪 测试波动率指数获取功能")
    print("=" * 60)
    print()

    fetcher = get_volatility_fetcher()

    # 测试的指数和ETF
    test_symbols = [
        ('^VIX', 'VIX - 标普500波动率指数（恐慌指数）'),
        ('^GVZ', 'GVZ - CBOE黄金波动率指数'),
        ('^OVX', 'OVX - CBOE原油波动率指数'),
        ('GLD', 'GLD - 黄金SPDR（使用GVZ指数）'),
        ('SLV', 'SLV - 白银iShares（使用GVZ指数）'),
        ('USO', 'USO - 原油（使用OVX指数）'),
    ]

    print("📊 获取当前波动率指数")
    print("-" * 60)
    print()

    for symbol, description in test_symbols:
        print(f"🔍 获取 {description} ({symbol})...")

        try:
            value = fetcher.get_volatility_index(symbol)

            if value is not None:
                # 获取分位数
                percentile = fetcher.calculate_iv_percentile(symbol)

                print(f"   ✅ 当前值: {value:.2f}%")

                if percentile is not None:
                    # 判断风险等级
                    if percentile >= 95:
                        level = "🔴 极端"
                    elif percentile >= 90:
                        level = "🟠 高危"
                    elif percentile >= 80:
                        level = "🟡 警告"
                    else:
                        level = "🟢 正常"

                    print(f"   📊 历史分位: {percentile:.1f}%")
                    print(f"   {level} 风险等级")
            else:
                print(f"   ❌ 获取失败")

        except Exception as e:
            print(f"   ❌ 错误: {e}")

        print()

    print("=" * 60)
    print("📊 获取历史波动率指数数据")
    print("-" * 60)
    print()

    # 测试获取历史数据
    symbol = '^VIX'
    print(f"🔍 获取 {symbol} 的历史数据（最近30天）...")

    try:
        historical = fetcher.get_historical_volatility_index(symbol, days=30)

        if historical:
            print(f"   ✅ 获取到 {len(historical)} 条数据")
            print()
            print("   最近5天数据:")
            for data in historical[-5:]:
                print(f"      {data['date'].strftime('%Y-%m-%d')}: {data['value']:.2f}%")
        else:
            print(f"   ❌ 未获取到历史数据")

    except Exception as e:
        print(f"   ❌ 错误: {e}")

    print()
    print("=" * 60)
    print("✅ 测试完成！")
    print()
    print("💡 说明：")
    print("   - VIX、GVZ、OVX 是真实的波动率指数")
    print("   - 这些指数本身就是市场预期的波动率")
    print("   - 可以直接作为 IV 使用，不需要估算")
    print("   - 比'简化估算'更准确、更可靠")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
