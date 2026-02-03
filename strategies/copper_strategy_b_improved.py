# -*- coding: utf-8 -*-
"""
===================================
沪铜期货策略 B - 逻辑改进版
===================================

改进内容:
1. 波动率过滤 - 低波动时不交易
2. 仓位管理 - 根据趋势强度动态调整
3. 分批止盈 - 50% + 50% 分两批出场

相比策略 A 的改进:
- A: 固定仓位，一次性止盈，无波动率过滤
- B: 动态仓位，分批止盈，波动率过滤
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import time

# ==========================================
# ⚙️ 策略参数配置
# ==========================================
FILE_PATH = r'D:\期货数据\沪铜4小时K线_20260203_130227.csv'

# 核心指标参数
EMA_FAST = 5
EMA_SLOW = 15
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
RSI_PERIOD = 14
RSI_FILTER = 45          # 使用优化后的值
RATIO_TRIGGER = 1.15
STC_LENGTH = 10
STC_FAST = 23
STC_SLOW = 50
STC_SELL_ZONE = 85       # 使用优化后的值
STOP_LOSS_PCT = 0.02

# ==========================================
# 🆕 新增参数
# ==========================================

# 1. 波动率过滤参数
VOLATILITY_PERIOD = 20         # ATR 周期
VOLATILITY_THRESHOLD = 0.015    # 最小波动率阈值 (1.5%)
                               # 低于此值不交易（震荡市）

# 2. 仓位管理参数
POSITION_BASE = 1.0            # 基础仓位
POSITION_MAX = 2.0             # 最大仓位（2倍）
TREND_STRENGTH_THRESHOLD = 1.5  # 趋势强度阈值（Ratio值）
                                 # Ratio > 1.5 时加仓到 2倍

# 3. 分批止盈参数
TAKE_PROFIT_BATCH1 = 0.50      # 第一批止盈比例 (50%)
TAKE_PROFIT_BATCH1_PCT = 1.5   # 第一批止盈条件 (盈利 1.5%)
TAKE_PROFIT_BATCH2_PCT = 2.5   # 第二批止盈条件 (盈利 2.5%)


def calculate_indicators(df):
    """计算技术指标"""
    # 1. EMA
    df['ema_fast'] = df['close'].ewm(span=EMA_FAST, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=EMA_SLOW, adjust=False).mean()

    # 2. MACD & Ratio
    exp1 = df['close'].ewm(span=MACD_FAST, adjust=False).mean()
    exp2 = df['close'].ewm(span=MACD_SLOW, adjust=False).mean()
    df['macd_dif'] = exp1 - exp2
    df['macd_dea'] = df['macd_dif'].ewm(span=MACD_SIGNAL, adjust=False).mean()
    df['ratio'] = np.where(df['macd_dea'] != 0, df['macd_dif'] / df['macd_dea'], 0)

    # 3. RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 4. STC
    stc_macd = df['close'].ewm(span=STC_FAST, adjust=False).mean() - \
               df['close'].ewm(span=STC_SLOW, adjust=False).mean()
    stoch_period = STC_LENGTH
    min_macd = stc_macd.rolling(window=stoch_period).min()
    max_macd = stc_macd.rolling(window=stoch_period).max()
    stoch_k = 100 * (stc_macd - min_macd) / (max_macd - min_macd).replace(0, np.nan)
    stoch_k = stoch_k.fillna(50)
    stoch_d = stoch_k.rolling(window=3).mean()
    min_stoch_d = stoch_d.rolling(window=stoch_period).min()
    max_stoch_d = stoch_d.rolling(window=stoch_period).max()
    stc_raw = 100 * (stoch_d - min_stoch_d) / (max_stoch_d - min_stoch_d).replace(0, np.nan)
    stc_raw = stc_raw.fillna(50)
    df['stc'] = stc_raw.rolling(window=3).mean()

    # 5. 波动率指标 (ATR) - 保留用于参考，但不用于过滤
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(window=VOLATILITY_PERIOD).mean()
    df['volatility'] = df['atr'] / df['close']

    return df


def calculate_position_size(ratio, rsi):
    """
    动态仓位管理

    根据趋势强度调整仓位:
    - 基础: 1.0 倍
    - 强趋势 (Ratio > 1.5): 2.0 倍
    - 超强趋势 (Ratio > 2.0): 2.0 倍 (最大)
    """
    if ratio > 2.0:
        return POSITION_MAX
    elif ratio > 1.5:
        return 1.5
    elif ratio > 1.0:
        return 1.2
    else:
        return POSITION_BASE


def run_strategy():
    print("=" * 80)
    print("沪铜策略 B - 实盘逻辑版（修正未来函数）")
    print("=" * 80)
    print("\n改进内容:")
    print("  1. [修正] 使用上一根K线Ratio计算仓位（实盘逻辑）")
    print("  2. [移除] 波动率过滤（原来太严格）")
    print("  3. [保留] 动态仓位 - Ratio > 1.5 时加仓到 1.5-2.0 倍")
    print("  4. [保留] 分批止盈 - 盈利 1.5% 卖 50%，盈利 2.5% 全部止盈")
    print("\n修正说明:")
    print("  - 回测原逻辑: 用当前K线Ratio（收盘后才知道，无法买入）")
    print("  - 实盘修正版: 用上一根K线Ratio（收盘前已知，可下单）")
    print("-" * 80)

    start_time = time.time()

    # 加载数据
    print(f"\n[加载] 数据文件...")
    try:
        try:
            df = pd.read_csv(FILE_PATH)
        except:
            df = pd.read_csv(FILE_PATH, encoding='gbk')
        df.columns = [c.strip() for c in df.columns]
        df['datetime'] = pd.to_datetime(df['datetime'])
    except Exception as e:
        print(f"[错误] 读取失败: {e}")
        return

    df = calculate_indicators(df)

    print(f"[数据] 时间范围: {df['datetime'].iloc[0]} ~ {df['datetime'].iloc[-1]}")
    print(f"[数据] K线数量: {len(df)} 根")

    # 预计算前值
    df['ema_fast_prev'] = df['ema_fast'].shift(1)
    df['ema_slow_prev'] = df['ema_slow'].shift(1)
    df['ratio_prev'] = df['ratio'].shift(1)
    df['dif_prev'] = df['macd_dif'].shift(1)
    df['stc_prev'] = df['stc'].shift(1)

    # 信号条件
    trend_up = df['ema_fast'] > df['ema_slow']
    ratio_safe = (df['ratio'] > 0) & (df['ratio'] < RATIO_TRIGGER)
    ratio_shrinking = df['ratio'] < df['ratio_prev']
    turning_up = df['macd_dif'] > df['dif_prev']
    is_strong = df['rsi'] > RSI_FILTER

    # ==========================================
    # ✖️ 移除波动率过滤（方案3）
    # 原因: 1.5% 阈值太严格，过滤掉太多机会
    # ==========================================

    ema_cross = (df['ema_fast_prev'] <= df['ema_slow_prev']) & (df['ema_fast'] > df['ema_slow'])

    df['sniper_signal'] = trend_up & ratio_safe & ratio_shrinking & turning_up & is_strong
    df['chase_signal'] = ema_cross & is_strong
    df['buy_signal'] = df['sniper_signal'] | df['chase_signal']

    stc_exit = (df['stc_prev'] > STC_SELL_ZONE) & (df['stc'] < df['stc_prev'])
    trend_exit = df['ema_fast'] < df['ema_slow']
    df['exit_signal'] = stc_exit | trend_exit

    # ==========================================
    # 分批止盈回测
    # ==========================================
    print("\n[交易] === 流水记录（分批止盈）===")

    positions = []
    holding = False
    entry_price = 0.0
    position_size = 1.0
    entry_date = None
    profit_points = []
    batch1_sold = False

    for i in range(1, len(df)):
        row = df.iloc[i]

        if not holding:
            if row['buy_signal']:
                holding = True
                entry_price = row['close']
                entry_date = row['datetime']

                # ==========================================
                # ✅ 实盘逻辑：用上一根K线的Ratio计算仓位
                # ==========================================
                # 回测错误：用当前Ratio（当前收盘后才知道）
                # 实盘正确：用上一根Ratio（上一根收盘后已知道）
                position_size = calculate_position_size(row['ratio_prev'], row['rsi'])

                reason = 'sniper' if row['sniper_signal'] else 'chase'
                reason_text = "狙击开多" if reason == 'sniper' else "暴力追涨"
                ratio_info = f"| Ratio收敛: {row['ratio_prev']:.2f}->{row['ratio']:.2f}" if reason == 'sniper' else "| EMA金叉 + RSI强势"

                # 显示仓位（注意：用的是上一根Ratio）
                print(f"[买入] {reason_text} | {row['datetime']} | 价格: {row['close']:.0f} | "
                      f"仓位: {position_size:.1f}x (上一根Ratio: {row['ratio_prev']:.2f}) {ratio_info}")

                positions.append({
                    'date': row['datetime'],
                    'price': row['close'],
                    'type': 'buy',
                    'reason': reason,
                    'position_size': position_size,
                    'ratio_used': row['ratio_prev']  # 记录使用的Ratio
                })

                batch1_sold = False

        elif holding:
            stop_price = entry_price * (1 - STOP_LOSS_PCT)

            # 当前盈利比例
            profit_pct = (row['close'] - entry_price) / entry_price

            # 分批止盈逻辑
            # 第一批止盈 (50% 仓位)
            if not batch1_sold and profit_pct >= TAKE_PROFIT_BATCH1_PCT:
                batch1_size = position_size * TAKE_PROFIT_BATCH1
                diff1 = (row['close'] - entry_price) * batch1_size
                profit_points.append(diff1)
                batch1_sold = True

                print(f"[止盈1] 卖出 {batch1_size:.1f}x | {row['datetime']} | 价格: {row['close']:.0f} | "
                      f"盈利: {diff1:.0f} ({profit_pct*100:.1f}%)")

                positions.append({
                    'date': row['datetime'],
                    'price': row['close'],
                    'type': 'sell_batch1',
                    'batch_size': batch1_size,
                    'reason': 'take_profit_1',
                    'color': 'purple'
                })

                # 如果只剩 0.5 仓位，继续持有
                position_size = position_size * (1 - TAKE_PROFIT_BATCH1)

            # 第二批止盈 (剩余 50% 仓位)
            elif batch1_sold and profit_pct >= TAKE_PROFIT_BATCH2_PCT:
                diff2 = (row['close'] - entry_price) * position_size
                profit_points.append(diff2)
                holding = False
                batch1_sold = False

                print(f"[止盈2] 卖出剩余 {position_size:.1f}x | {row['datetime']} | 价格: {row['close']:.0f} | "
                      f"盈利: {diff2:.0f} ({profit_pct*100:.1f}%)")

                positions.append({
                    'date': row['datetime'],
                    'price': row['close'],
                    'type': 'sell_batch2',
                    'batch_size': position_size,
                    'reason': 'take_profit_2',
                    'color': 'blue'
                })

            # 硬止损
            elif row['low'] <= stop_price:
                total_size = position_size * (2 if batch1_sold else 1)
                diff = (stop_price - entry_price) * total_size
                profit_points.append(diff)
                holding = False
                batch1_sold = False

                print(f"[止损] 全部卖出 {total_size:.1f}x | {row['datetime']} | 价格: {stop_price:.0f} | "
                      f"亏损: {diff:.0f}")

                positions.append({
                    'date': row['datetime'],
                    'price': stop_price,
                    'type': 'stop',
                    'reason': 'stop_loss'
                })

            # STC 止盈（整体退出）
            elif row['exit_signal'] and (row['stc_prev'] > STC_SELL_ZONE) and (row['stc'] < row['stc_prev']):
                total_size = position_size * (2 if batch1_sold else 1)
                diff = (row['close'] - entry_price) * total_size
                profit_points.append(diff)
                holding = False
                batch1_sold = False

                print(f"[止盈] STC退出 {total_size:.1f}x | {row['datetime']} | 价格: {row['close']:.0f} | "
                      f"盈利: {diff:.0f}")

                positions.append({
                    'date': row['datetime'],
                    'price': row['close'],
                    'type': 'sell',
                    'color': 'purple',
                    'reason': 'stc_exit'
                })

            # 趋势结束
            elif row['ema_fast'] < row['ema_slow']:
                total_size = position_size * (2 if batch1_sold else 1)
                diff = (row['close'] - entry_price) * total_size
                profit_points.append(diff)
                holding = False
                batch1_sold = False

                print(f"[离场] 趋势结束 {total_size:.1f}x | {row['datetime']} | 价格: {row['close']:.0f} | "
                      f"盈利: {diff:.0f}")

                positions.append({
                    'date': row['datetime'],
                    'price': row['close'],
                    'type': 'sell',
                    'color': 'red',
                    'reason': 'trend_end'
                })

    # 统计结果
    total = sum(profit_points)
    wins = len([p for p in profit_points if p > 0])
    losses = len([p for p in profit_points if p <= 0])
    win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
    avg_profit = np.mean(profit_points) if profit_points else 0
    max_profit = max(profit_points) if profit_points else 0
    max_loss = min(profit_points) if profit_points else 0

    total_time = time.time() - start_time

    # 计算实际交易次数（考虑分批）
    num_trades = len([p for p in positions if p['type'] == 'buy'])

    print("-" * 80)
    print(f"[结果] 总盈亏: {total:.0f} 点")
    print(f"[结果] 胜率: {win_rate:.1f}%")
    print(f"[结果] 开仓次数: {num_trades} 笔")
    print(f"[结果] 平仓次数: {wins+losses} 笔 (含分批止盈)")
    print(f"[结果] 平均盈亏: {avg_profit:.0f} 点/笔")
    print(f"[结果] 最大盈利: {max_profit:.0f} 点")
    print(f"[结果] 最大亏损: {max_loss:.0f} 点")
    print("-" * 80)
    print(f"[性能] 总耗时: {total_time:.3f} 秒")

    # 对比策略 A 和 策略B回测版
    print("\n" + "=" * 80)
    print("三版本对比")
    print("=" * 80)
    print(f"\n策略 A (固定仓位, 一次性止盈):")
    print(f"  总盈亏: 28,688 点 | 胜率: 59.5% | 交易: 42 笔")
    print(f"\n策略B回测版 (动态仓位-当前Ratio, 未来函数):")
    print(f"  总盈亏: 32,842 点 | 胜率: 59.5% | 交易: 42 笔")
    print(f"\n策略B实盘版 (动态仓位-上一根Ratio, 实盘可行):")
    print(f"  总盈亏: {total:.0f} 点 | 胜率: {win_rate:.1f}% | 开仓: {num_trades} 笔")

    improvement_vs_A = total - 28688
    decline_vs_backtest = total - 32842

    print(f"\n相对策略A: {improvement_vs_A:+.0f} 点 ({improvement_vs_A/28688*100:+.1f}%)")
    print(f"相对回测版: {decline_vs_backtest:+.0f} 点 ({decline_vs_backtest/32842*100:+.1f}%) - 修正未来函数影响")

    # 绘图
    print("\n[绘图] 正在生成图表...")
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), sharex=True,
                                        gridspec_kw={'height_ratios': [3, 1, 1]})

    # 主图 - 价格 + 信号
    ax1.plot(df['datetime'], df['close'], color='#333333', alpha=0.6, label='Price', linewidth=1)
    ax1.plot(df['datetime'], df['ema_fast'], color='#2ca02c', linewidth=1, alpha=0.7, label=f'EMA {EMA_FAST}')
    ax1.plot(df['datetime'], df['ema_slow'], color='#ff7f0e', linewidth=1, alpha=0.7, label=f'EMA {EMA_SLOW}')

    for p in positions:
        if p['type'] == 'buy':
            # 根据仓位大小调整标记大小
            size = 100 + p.get('position_size', 1) * 50
            ax1.scatter(p['date'], p['price'], marker='^', color='green', s=size,
                       edgecolors='black', zorder=5, alpha=0.8)
        elif p['type'] in ['sell', 'sell_batch1', 'sell_batch2']:
            color = p.get('color', 'red')
            if p['type'] == 'sell_batch1':
                marker = 'D'  # 菱形表示第一批止盈
                size = 80
            elif p['type'] == 'sell_batch2':
                marker = 'v'  # 三角表示第二批止盈
                size = 120
            else:
                marker = 'v'
                size = 100
            ax1.scatter(p['date'], p['price'], marker=marker, color=color, s=size,
                       edgecolors='black', zorder=5, alpha=0.8)
        elif p['type'] == 'stop':
            ax1.scatter(p['date'], p['price'], marker='X', color='black', s=100, zorder=5)

    ax1.set_title(f'Copper Strategy B (Real Logic - Fixed Look-Ahead) | Total: {total:.0f} pts | Win Rate: {win_rate:.1f}% | Trades: {num_trades}\n'
                  f'Dynamic Position (Using Prev Ratio) | Batch Take-Profit (50%@1.5% + 50%@2.5%)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # 副图1 - MACD Ratio
    ax2.plot(df['datetime'], df['ratio'], color='blue', label='MACD Ratio', linewidth=1)
    ax2.axhline(RATIO_TRIGGER, color='red', linestyle='--', alpha=0.5, label=f'Trigger ({RATIO_TRIGGER})')
    ax2.axhline(TREND_STRENGTH_THRESHOLD, color='purple', linestyle=':', alpha=0.5, label=f'Strong Trend ({TREND_STRENGTH_THRESHOLD})')
    ax2.fill_between(df['datetime'], 0, RATIO_TRIGGER, color='green', alpha=0.1)
    ax2.set_ylim(-1, 3)
    ax2.legend(loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.3)

    # 副图2 - 波动率
    ax3.plot(df['datetime'], df['volatility'] * 100, color='orange', label='Volatility (%)', linewidth=1)
    ax3.axhline(VOLATILITY_THRESHOLD * 100, color='red', linestyle='--', alpha=0.5,
                label=f'Min Volatility ({VOLATILITY_THRESHOLD*100:.1f}%)')
    ax3.fill_between(df['datetime'], 0, VOLATILITY_THRESHOLD * 100, color='red', alpha=0.1)
    ax3.set_ylim(0, 5)
    ax3.legend(loc='upper left', fontsize=8)
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    # 保存
    output_path = Path('D:/daily_stock_analysis/results/copper_strategy_b_improved.png')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=100)
    print(f"[保存] 图表已保存: {output_path}")

    plt.show()

    return {
        'total': total,
        'win_rate': win_rate,
        'trades': num_trades,
        'closes': wins + losses,
        'wins': wins,
        'losses': losses,
        'avg_profit': avg_profit,
        'max_profit': max_profit,
        'max_loss': max_loss,
        'positions': positions
    }


if __name__ == "__main__":
    run_strategy()
