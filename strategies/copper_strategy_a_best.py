# -*- coding: utf-8 -*-
"""
===================================
沪铜期货策略 A - 最优参数版
===================================

经过网格优化后的最佳参数配置
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import time

# ==========================================
# ⚙️ 最优参数配置
# ==========================================
FILE_PATH = r'D:\期货数据\沪铜4小时K线_20260203_130227.csv'

# 网格优化后的最优参数
EMA_FAST = 5
EMA_SLOW = 15
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
RSI_PERIOD = 14

# 优化后的关键参数 ⭐
RATIO_TRIGGER = 1.15      # 保持不变
RSI_FILTER = 45          # 从 50 降低到 45 ⭐
STC_SELL_ZONE = 85       # 从 90 降低到 85 ⭐

STC_LENGTH = 10
STC_FAST = 23
STC_SLOW = 50
STOP_LOSS_PCT = 0.02


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


def run_strategy():
    print("=" * 80)
    print("沪铜策略 A - 最优参数版 (网格优化)")
    print("=" * 80)
    print("\n最优参数配置:")
    print(f"  RATIO_TRIGGER: {RATIO_TRIGGER} (原版: 1.15)")
    print(f"  RSI_FILTER: {RSI_FILTER} (原版: 50) ⭐")
    print(f"  STC_SELL_ZONE: {STC_SELL_ZONE} (原版: 90) ⭐")
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
    ema_cross = (df['ema_fast_prev'] <= df['ema_slow_prev']) & (df['ema_fast'] > df['ema_slow'])

    df['sniper_signal'] = trend_up & ratio_safe & ratio_shrinking & turning_up & is_strong
    df['chase_signal'] = ema_cross & is_strong
    df['buy_signal'] = df['sniper_signal'] | df['chase_signal']

    stc_exit = (df['stc_prev'] > STC_SELL_ZONE) & (df['stc'] < df['stc_prev'])
    trend_exit = df['ema_fast'] < df['ema_slow']
    df['exit_signal'] = stc_exit | trend_exit

    # 回测
    print("\n[交易] === 流水记录 ===")
    positions = []
    holding = False
    entry_price = 0.0
    profit_points = []

    for i in range(1, len(df)):
        row = df.iloc[i]

        if not holding:
            if row['buy_signal']:
                holding = True
                entry_price = row['close']
                reason = 'sniper' if row['sniper_signal'] else 'chase'
                reason_text = "狙击开多" if reason == 'sniper' else "暴力追涨"
                ratio_info = f"| Ratio收敛: {row['ratio_prev']:.2f}->{row['ratio']:.2f}" if reason == 'sniper' else "| EMA金叉 + RSI强势"
                print(f"[买入] {reason_text} | {row['datetime']} | 价格: {row['close']:.0f} {ratio_info}")
                positions.append({'date': row['datetime'], 'price': row['close'], 'type': 'buy', 'reason': reason})

        elif holding:
            stop_price = entry_price * (1 - STOP_LOSS_PCT)

            if row['low'] <= stop_price:
                holding = False
                diff = stop_price - entry_price
                profit_points.append(diff)
                print(f"[卖出] 硬止损 | {row['datetime']} | 价格: {stop_price:.0f} | 亏损: {diff:.0f}")
                positions.append({'date': row['datetime'], 'price': stop_price, 'type': 'stop', 'reason': 'stop_loss'})

            elif row['exit_signal'] and (row['stc_prev'] > STC_SELL_ZONE) and (row['stc'] < row['stc_prev']):
                holding = False
                diff = row['close'] - entry_price
                profit_points.append(diff)
                print(f"[卖出] STC止盈 | {row['datetime']} | 价格: {row['close']:.0f} | 盈利: {diff:.0f}")
                positions.append({'date': row['datetime'], 'price': row['close'], 'type': 'sell', 'color': 'purple', 'reason': 'stc_profit'})

            elif row['ema_fast'] < row['ema_slow']:
                holding = False
                diff = row['close'] - entry_price
                profit_points.append(diff)
                print(f"[卖出] 趋势离场 | {row['datetime']} | 价格: {row['close']:.0f} | 盈利: {diff:.0f}")
                positions.append({'date': row['datetime'], 'price': row['close'], 'type': 'sell', 'color': 'red', 'reason': 'trend_end'})

    # 统计结果
    total = sum(profit_points)
    wins = len([p for p in profit_points if p > 0])
    losses = len([p for p in profit_points if p <= 0])
    win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
    avg_profit = np.mean(profit_points) if profit_points else 0
    max_profit = max(profit_points) if profit_points else 0
    max_loss = min(profit_points) if profit_points else 0

    total_time = time.time() - start_time

    print("-" * 80)
    print(f"[结果] 总盈亏: {total:.0f} 点")
    print(f"[结果] 胜率: {win_rate:.1f}%")
    print(f"[结果] 交易: {wins}胜 {losses}负 (共 {wins+losses} 笔)")
    print(f"[结果] 平均盈亏: {avg_profit:.0f} 点/笔")
    print(f"[结果] 最大盈利: {max_profit:.0f} 点")
    print(f"[结果] 最大亏损: {max_loss:.0f} 点")
    print("-" * 80)
    print(f"[性能] 总耗时: {total_time:.3f} 秒")

    # 对比原版
    print("\n" + "=" * 80)
    print("与原版参数对比")
    print("=" * 80)
    print(f"\n原版 (RSI_FILTER=50, STC_SELL_ZONE=90):")
    print(f"  总盈亏: 26,878 点 | 胜率: 61.0% | 交易: 41 笔")
    print(f"\n最优版 (RSI_FILTER=45, STC_SELL_ZONE=85):")
    print(f"  总盈亏: {total:.0f} 点 | 胜率: {win_rate:.1f}% | 交易: {wins+losses} 笔")
    improvement = total - 26878
    print(f"\n改进: {improvement:+.0f} 点 ({improvement/26878*100:+.1f}%) ⭐")

    # 绘图
    print("\n[绘图] 正在生成图表...")
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

    # 主图
    ax1.plot(df['datetime'], df['close'], color='#333333', alpha=0.6, label='Price')
    ax1.plot(df['datetime'], df['ema_fast'], color='#2ca02c', linewidth=1.5, label=f'EMA {EMA_FAST}')
    ax1.plot(df['datetime'], df['ema_slow'], color='#ff7f0e', linewidth=1.5, label=f'EMA {EMA_SLOW}')

    for p in positions:
        if p['type'] == 'buy':
            ax1.scatter(p['date'], p['price'], marker='^', color='green', s=120, edgecolors='black', zorder=5)
        elif p['type'] == 'sell':
            color = p.get('color', 'red')
            marker = 'v' if color == 'red' else 'D'
            ax1.scatter(p['date'], p['price'], marker=marker, color=color, s=120, edgecolors='black', zorder=5)
        elif p['type'] == 'stop':
            ax1.scatter(p['date'], p['price'], marker='X', color='black', s=100, zorder=5)

    ax1.set_title(f'Copper Strategy A (Optimized Parameters) | Total: {total:.0f} pts | Win Rate: {win_rate:.1f}% | Trades: {wins+losses}\nRSI_FILTER={RSI_FILTER} (was 50) | STC_SELL_ZONE={STC_SELL_ZONE} (was 90) | Improvement: +{improvement:.0f} pts ({improvement/26878*100:+.1f}%)', fontsize=12)
    ax1.legend(loc='upper left')

    # 副图
    ax2.plot(df['datetime'], df['ratio'], color='blue', label='MACD Ratio')
    ax2.axhline(RATIO_TRIGGER, color='red', linestyle='--', label=f'Trigger ({RATIO_TRIGGER})')
    ax2.fill_between(df['datetime'], 0, RATIO_TRIGGER, color='green', alpha=0.1)
    ax2.set_ylim(-1, 3)
    ax2.legend()

    plt.tight_layout()

    # 保存
    output_path = Path('D:/daily_stock_analysis/results/copper_strategy_a_best.png')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=100)
    print(f"[保存] 图表已保存: {output_path}")

    plt.show()


if __name__ == "__main__":
    run_strategy()
