#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
国内期货监控演示页面生成器
使用真实数据（通过 akshare 获取）
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from src.china_futures_fetcher import get_china_futures_fetcher
from web.templates import render_futures_page

print("=" * 60)
print("生成国内期货监控页面（真实数据）")
print("=" * 60)

fetcher = get_china_futures_fetcher()

# 国内期货主力品种
china_futures = [
    'SC',   # 原油
    'AU',   # 黄金
    'AG',   # 白银
    'CU',   # 铜
    'I',    # 铁矿石
    'M',    # 豆粕
    'RB',   # 螺纹钢
    'MA',   # 甲醇
]

results = []
extreme_results = []

for code in china_futures:
    info = fetcher.get_futures_info(code)
    if not info:
        continue

    try:
        # 获取当前价格
        price = fetcher.get_current_price(code)

        # 计算波动率
        hv = fetcher.calculate_historical_volatility(code, window=20)
        iv = fetcher.estimate_implied_volatility(code)

        if hv is None or iv is None:
            continue

        # 计算 IV-HV 背离度
        iv_hv_divergence = iv - hv

        # 判断风险等级
        if iv >= 80 or iv_hv_divergence >= 20:
            risk_level = 'extreme'
        elif iv >= 60 or iv_hv_divergence >= 15:
            risk_level = 'high'
        elif iv >= 40 or iv_hv_divergence >= 10:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        # 计算 IV 分位数（简化：基于 IV 绝对值）
        if iv >= 70:
            iv_percentile = 90
        elif iv >= 50:
            iv_percentile = 75
        elif iv >= 30:
            iv_percentile = 50
        else:
            iv_percentile = 25

        result = {
            'symbol': f"{code}(CN)",  # 标记为国内期货
            'name': f"{info['name']}({info['exchange']})",
            'current_price': price if price else 0,
            'iv_current': iv,
            'iv_percentile': iv_percentile,
            'hv_20d': hv,
            'iv_hv_divergence': iv_hv_divergence,
            'risk_level': risk_level,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

        results.append(result)

        if risk_level in ['high', 'extreme']:
            extreme_results.append(result)

        print(f"  {code} - {info['name']}: IV={iv:.2f}%, HV={hv:.2f}%, 风险={risk_level}")

    except Exception as e:
        print(f"  {code} - 处理失败: {e}")
        continue

# 生成页面
print(f"\n生成页面: {len(results)} 个品种")
html = render_futures_page(results, extreme_results, data_unavailable=False)

# 保存文件
output_file = "china_futures_monitor.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html.decode('utf-8'))

print(f"\n[完成] 页面已保存: {output_file}")
print(f"[提示] 双击文件在浏览器中打开")
print("\n" + "=" * 60)
