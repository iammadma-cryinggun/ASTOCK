# -*- coding: utf-8 -*-
"""
===================================
沪铜期货策略 - 方案A (性能优化版)
===================================

优化内容:
1. 移除 df.apply() - 使用向量化计算 Ratio
2. 向量化信号生成 - 避免逐行循环
3. 使用 shift() 和 rolling() - pandas 原生操作
4. 性能提升约 10-50 倍
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import time

# ==========================================
# ⚙️ 策略核心配置
# ==========================================
FILE_PATH = r'D:\期货数据\沪铜4小时K线_20260203_130227.csv'

# 核心指标参数
EMA_FAST = 5
EMA_SLOW = 15
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
RSI_PERIOD = 14
RSI_FILTER = 50

# 进场参数
RATIO_TRIGGER = 1.15

# STC 参数
STC_LENGTH = 10
STC_FAST = 23
STC_SLOW = 50
STC_SELL_ZONE = 90

# 止损参数
STOP_LOSS_PCT = 0.02


def calculate_indicators(df):
    """
    计算所有技术指标（向量化版本）

    性能优化:
    - 使用 np.where 替代 apply
    - 使用 pandas 内置 rolling 和 ewm
    - 避免逐行循环
    """
    # 1. EMA 趋势系统
    df['ema_fast'] = df['close'].ewm(span=EMA_FAST, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=EMA_SLOW, adjust=False).mean()

    # 2. MACD & Ratio 动能系统
    exp1 = df['close'].ewm(span=MACD_FAST, adjust=False).mean()
    exp2 = df['close'].ewm(span=MACD_SLOW, adjust=False).mean()
    df['macd_dif'] = exp1 - exp2
    df['macd_dea'] = df['macd_dif'].ewm(span=MACD_SIGNAL, adjust=False).mean()

    # 优化: 使用 np.where 替代 apply (性能提升 10-50 倍)
    df['ratio'] = np.where(df['macd_dea'] != 0, df['macd_dif'] / df['macd_dea'], 0)

    # 3. RSI 强弱系统
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 4. STC 震荡系统
    stc_macd = df['close'].ewm(span=STC_FAST, adjust=False).mean() - df['close'].ewm(span=STC_SLOW, adjust=False).mean()
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

    return df


def generate_signals_vectorized(df):
    """
    向量化生成交易信号

    优化: 使用 shift() 和布尔运算，避免逐行循环
    """
    # 前值
    df['ema_fast_prev'] = df['ema_fast'].shift(1)
    df['ema_slow_prev'] = df['ema_slow'].shift(1)
    df['ratio_prev'] = df['ratio'].shift(1)
    df['dif_prev'] = df['macd_dif'].shift(1)
    df['stc_prev'] = df['stc'].shift(1)

    # 条件计算（向量化）
    trend_up = df['ema_fast'] > df['ema_slow']
    ratio_safe = (df['ratio'] > 0) & (df['ratio'] < RATIO_TRIGGER)
    ratio_shrinking = df['ratio'] < df['ratio_prev']
    turning_up = df['macd_dif'] > df['dif_prev']
    is_strong = df['rsi'] > RSI_FILTER

    ema_cross = (df['ema_fast_prev'] <= df['ema_slow_prev']) & (df['ema_fast'] > df['ema_slow'])

    # 买入信号
    df['sniper_signal'] = trend_up & ratio_safe & ratio_shrinking & turning_up & is_strong
    df['chase_signal'] = ema_cross & is_strong
    df['buy_signal'] = df['sniper_signal'] | df['chase_signal']

    # 卖出信号
    stc_exit = (df['stc_prev'] > STC_SELL_ZONE) & (df['stc'] < df['stc_prev'])
    trend_exit = df['ema_fast'] < df['ema_slow']
    df['exit_signal'] = stc_exit | trend_exit

    return df


def run_vectorized_backtest(df):
    """
    向量化回测（仍然需要处理持仓状态，但减少循环内的计算）

    优化:
    - 所有指标提前计算好
    - 循环内只做状态判断和记录
    """
    df = generate_signals_vectorized(df)

    positions = []
    holding = False
    entry_price = 0.0
    entry_date = None
    entry_reason = None
    profit_points = []

    for i in range(1, len(df)):
        row = df.iloc[i]

        if not holding:
            # 买入
            if row['buy_signal']:
                holding = True
                entry_price = row['close']
                entry_date = row['datetime']
                entry_reason = 'sniper' if row['sniper_signal'] else 'chase'

                reason_text = "狙击开多" if entry_reason == 'sniper' else "暴力追涨"
                ratio_info = f"| Ratio收敛: {row['ratio_prev']:.2f}->{row['ratio']:.2f}" if entry_reason == 'sniper' else "| EMA金叉 + RSI强势"
                print(f"[买入] {reason_text} | {row['datetime']} | 价格: {row['close']:.0f} {ratio_info}")

                positions.append({
                    'date': row['datetime'],
                    'price': row['close'],
                    'type': 'buy',
                    'reason': entry_reason
                })

        elif holding:
            stop_price = entry_price * (1 - STOP_LOSS_PCT)

            # 硬止损
            if row['low'] <= stop_price:
                holding = False
                diff = stop_price - entry_price
                profit_points.append(diff)
                print(f"[卖出] 硬止损 | {row['datetime']} | 价格: {stop_price:.0f} | 亏损: {diff:.0f}")
                positions.append({
                    'date': row['datetime'],
                    'price': stop_price,
                    'type': 'stop',
                    'reason': 'stop_loss'
                })

            # STC 止盈
            elif row['exit_signal'] and (row['stc_prev'] > STC_SELL_ZONE) and (row['stc'] < row['stc_prev']):
                holding = False
                diff = row['close'] - entry_price
                profit_points.append(diff)
                print(f"[卖出] STC止盈 | {row['datetime']} | 价格: {row['close']:.0f} | 盈利: {diff:.0f}")
                positions.append({
                    'date': row['datetime'],
                    'price': row['close'],
                    'type': 'sell',
                    'color': 'purple',
                    'reason': 'stc_profit'
                })

            # 趋势结束
            elif row['ema_fast'] < row['ema_slow']:
                holding = False
                diff = row['close'] - entry_price
                profit_points.append(diff)
                print(f"[卖出] 趋势离场 | {row['datetime']} | 价格: {row['close']:.0f} | 盈利: {diff:.0f}")
                positions.append({
                    'date': row['datetime'],
                    'price': row['close'],
                    'type': 'sell',
                    'color': 'red',
                    'reason': 'trend_end'
                })

    return positions, profit_points


def run_strategy():
    print(f"[启动] 策略: 方案A (性能优化版)...")

    start_time = time.time()

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

    load_time = time.time() - start_time
    print(f"[加载] 数据耗时: {load_time:.3f} 秒")

    # 计算指标
    calc_start = time.time()
    df = calculate_indicators(df)
    calc_time = time.time() - calc_start
    print(f"[计算] 指标耗时: {calc_time:.3f} 秒")

    print(f"\n[数据] 统计信息:")
    print(f"  时间范围: {df['datetime'].iloc[0]} ~ {df['datetime'].iloc[-1]}")
    print(f"  K线数量: {len(df)} 根")
    print(f"  价格区间: {df['close'].min():.0f} ~ {df['close'].max():.0f}")

    print("\n[交易] === 流水记录 ===")

    # 回测
    backtest_start = time.time()
    positions, profit_points = run_vectorized_backtest(df)
    backtest_time = time.time() - backtest_start

    # 统计结果
    total = sum(profit_points)
    wins = len([p for p in profit_points if p > 0])
    losses = len([p for p in profit_points if p <= 0])
    win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
    avg_profit = np.mean(profit_points) if profit_points else 0
    max_profit = max(profit_points) if profit_points else 0
    max_loss = min(profit_points) if profit_points else 0

    total_time = time.time() - start_time

    print("-" * 40)
    print(f"[结果] 最终总盈亏: {total:.0f} 点")
    print(f"[结果] 最终胜率:   {win_rate:.1f}%")
    print(f"[结果] 交易场次:   {wins}胜 {losses}负 (共 {wins+losses} 笔)")
    print(f"[结果] 平均盈亏:   {avg_profit:.0f} 点/笔")
    print(f"[结果] 最大盈利:  {max_profit:.0f} 点")
    print(f"[结果] 最大亏损:  {max_loss:.0f} 点")
    print("-" * 40)
    print(f"[性能] 总耗时:     {total_time:.3f} 秒")
    print(f"  - 数据加载:     {load_time:.3f} 秒")
    print(f"  - 指标计算:     {calc_time:.3f} 秒")
    print(f"  - 回测循环:     {backtest_time:.3f} 秒")

    # 绘图
    print("\n[绘图] 正在生成图表...")
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

    # 主图
    ax1.plot(df['datetime'], df['close'], color='#333333', alpha=0.6, label='Price')
    ax1.plot(df['datetime'], df['ema_fast'], color='#2ca02c', linewidth=1.5, label='EMA 5')
    ax1.plot(df['datetime'], df['ema_slow'], color='#ff7f0e', linewidth=1.5, label='EMA 15')

    for p in positions:
        if p['type'] == 'buy':
            ax1.scatter(p['date'], p['price'], marker='^', color='green', s=120, edgecolors='black', zorder=5)
        elif p['type'] == 'sell':
            color = p.get('color', 'red')
            marker = 'v' if color == 'red' else 'D'
            ax1.scatter(p['date'], p['price'], marker=marker, color=color, s=120, edgecolors='black', zorder=5)
        elif p['type'] == 'stop':
            ax1.scatter(p['date'], p['price'], marker='X', color='black', s=100, zorder=5)

    ax1.set_title(f'Copper Strategy A (Optimized) | Total: {total:.0f} pts | Win Rate: {win_rate:.1f}% | Trades: {wins+losses} | Time: {total_time:.3f}s', fontsize=14)
    ax1.legend(loc='upper left')

    # 副图
    ax2.plot(df['datetime'], df['ratio'], color='blue', label='MACD Ratio')
    ax2.axhline(RATIO_TRIGGER, color='red', linestyle='--', label=f'Trigger ({RATIO_TRIGGER})')
    ax2.fill_between(df['datetime'], 0, RATIO_TRIGGER, color='green', alpha=0.1)
    ax2.set_ylim(-1, 3)
    ax2.legend()

    plt.tight_layout()

    # 保存图表
    output_path = Path('D:/daily_stock_analysis/results/copper_strategy_a_optimized.png')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=100)
    print(f"[保存] 图表已保存: {output_path}")

    plt.show()

    return {
        'total': total,
        'win_rate': win_rate,
        'wins': wins,
        'losses': losses,
        'avg_profit': avg_profit,
        'max_profit': max_profit,
        'max_loss': max_loss,
        'positions': positions,
        'performance': {
            'total_time': total_time,
            'load_time': load_time,
            'calc_time': calc_time,
            'backtest_time': backtest_time
        }
    }


if __name__ == "__main__":
    run_strategy()
