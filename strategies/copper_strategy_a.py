# -*- coding: utf-8 -*-
"""
===================================
沪铜期货策略 - 方案A (利润最大化)
===================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# ==========================================
# ⚙️ 策略核心配置: 方案A (利润最大化)
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
RATIO_TRIGGER = 1.15      # 狙击阈值

# STC 参数 (用于逃顶)
STC_LENGTH = 10
STC_FAST = 23
STC_SLOW = 50
STC_SELL_ZONE = 90        # STC 超买线

# 止损参数
STOP_LOSS_PCT = 0.02      # 2% 硬止损 (约1500-2000点)


def calculate_indicators(df):
    # 1. EMA 趋势系统
    df['ema_fast'] = df['close'].ewm(span=EMA_FAST, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=EMA_SLOW, adjust=False).mean()

    # 2. MACD & Ratio 动能系统
    exp1 = df['close'].ewm(span=MACD_FAST, adjust=False).mean()
    exp2 = df['close'].ewm(span=MACD_SLOW, adjust=False).mean()
    df['macd_dif'] = exp1 - exp2
    df['macd_dea'] = df['macd_dif'].ewm(span=MACD_SIGNAL, adjust=False).mean()
    # 计算比值 (核心)
    df['ratio'] = df.apply(lambda x: x['macd_dif'] / x['macd_dea'] if x['macd_dea'] != 0 else 0, axis=1)

    # 3. RSI 强弱系统
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 4. STC 震荡系统 (用于止盈)
    stc_macd = df['close'].ewm(span=STC_FAST, adjust=False).mean() - df['close'].ewm(span=STC_SLOW, adjust=False).mean()
    stoch_period = STC_LENGTH
    min_macd = stc_macd.rolling(window=stoch_period).min()
    max_macd = stc_macd.rolling(window=stoch_period).max()
    denom = max_macd - min_macd
    denom = denom.replace(0, np.nan)
    stoch_k = 100 * (stc_macd - min_macd) / denom
    stoch_k = stoch_k.fillna(50)
    stoch_d = stoch_k.rolling(window=3).mean()
    min_stoch_d = stoch_d.rolling(window=stoch_period).min()
    max_stoch_d = stoch_d.rolling(window=stoch_period).max()
    denom_2 = max_stoch_d - min_stoch_d
    denom_2 = denom_2.replace(0, np.nan)
    stc_raw = 100 * (stoch_d - min_stoch_d) / denom_2
    stc_raw = stc_raw.fillna(50)
    df['stc'] = stc_raw.rolling(window=3).mean()

    return df


def run_strategy():
    print(f"[启动] 策略: 方案A (全火力进攻版)...")

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

    print(f"\n[数据] 统计信息:")
    print(f"  时间范围: {df['datetime'].iloc[0]} ~ {df['datetime'].iloc[-1]}")
    print(f"  K线数量: {len(df)} 根")
    print(f"  价格区间: {df['close'].min():.0f} ~ {df['close'].max():.0f}")

    print("\n[交易] === 流水记录 ===")

    positions = []
    holding = False
    entry_price = 0.0
    profit_points = []

    for i in range(1, len(df)):
        date = df['datetime'].iloc[i]
        price = df['close'].iloc[i]
        low_price = df['low'].iloc[i]

        # 指标获取
        ema_fast = df['ema_fast'].iloc[i]
        ema_slow = df['ema_slow'].iloc[i]
        dif = df['macd_dif'].iloc[i]
        prev_dif = df['macd_dif'].iloc[i-1]

        ratio = df['ratio'].iloc[i]
        prev_ratio = df['ratio'].iloc[i-1]

        rsi = df['rsi'].iloc[i]
        stc = df['stc'].iloc[i]
        prev_stc = df['stc'].iloc[i-1]

        # ------------------------------------------------
        # [买入] 逻辑 (无乖离率限制，敢于追涨)
        # ------------------------------------------------
        if not holding:
            trend_up = (ema_fast > ema_slow)

            # 1. 狙击条件 (回调精准买入)
            # 核心逻辑: Ratio在安全区 且 Ratio正在收敛(动能衰竭)
            ratio_safe = (0 < ratio < RATIO_TRIGGER)
            ratio_shrinking = (ratio < prev_ratio)
            turning_up = (dif > prev_dif)
            is_strong = (rsi > RSI_FILTER)

            sniper_entry = trend_up and ratio_safe and ratio_shrinking and turning_up and is_strong

            # 2. 追涨条件 (趋势启动买入)
            # 移除了 BIAS_LIMIT，只要金叉且强势就干！
            ema_cross = (df['ema_fast'].iloc[i-1] <= df['ema_slow'].iloc[i-1]) and (ema_fast > ema_slow)

            chase_entry = ema_cross and is_strong

            if sniper_entry:
                holding = True
                entry_price = price
                print(f"[买入] 狙击开多 | {date} | 价格: {price:.0f} | Ratio收敛: {prev_ratio:.2f}->{ratio:.2f}")
                positions.append({'date': date, 'price': price, 'type': 'buy'})
                positions[-1]['reason'] = 'sniper'

            elif chase_entry:
                holding = True
                entry_price = price
                print(f"[买入] 暴力追涨 | {date} | 价格: {price:.0f} | EMA金叉 + RSI强势")
                positions.append({'date': date, 'price': price, 'type': 'buy'})
                positions[-1]['reason'] = 'chase'

        # ------------------------------------------------
        # [卖出] 逻辑 (STC逃顶 + 硬止损)
        # ------------------------------------------------
        elif holding:
            stop_price = entry_price * (1 - STOP_LOSS_PCT)

            # 1. 硬止损 (保命底线)
            if low_price <= stop_price:
                holding = False
                diff = stop_price - entry_price
                profit_points.append(diff)
                print(f"[卖出] 硬止损   | {date} | 价格: {stop_price:.0f} | 亏损: {diff:.0f}")
                positions.append({'date': date, 'price': stop_price, 'type': 'stop'})
                positions[-1]['reason'] = 'stop_loss'

            # 2. STC 逃顶 (保住利润)
            elif (prev_stc > STC_SELL_ZONE) and (stc < prev_stc):
                holding = False
                diff = price - entry_price
                profit_points.append(diff)
                print(f"[卖出] STC止盈  | {date} | 价格: {price:.0f} | 盈利: {diff:.0f}")
                positions.append({'date': date, 'price': price, 'type': 'sell', 'color': 'purple'})
                positions[-1]['reason'] = 'stc_profit'

            # 3. 趋势结束 (最后防线)
            elif (ema_fast < ema_slow):
                holding = False
                diff = price - entry_price
                profit_points.append(diff)
                print(f"[卖出] 趋势离场 | {date} | 价格: {price:.0f} | 盈利: {diff:.0f}")
                positions.append({'date': date, 'price': price, 'type': 'sell', 'color': 'red'})
                positions[-1]['reason'] = 'trend_end'

    # --- 统计结果 ---
    total = sum(profit_points)
    wins = len([p for p in profit_points if p > 0])
    losses = len([p for p in profit_points if p <= 0])
    win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
    avg_profit = np.mean(profit_points) if profit_points else 0
    max_profit = max(profit_points) if profit_points else 0
    max_loss = min(profit_points) if profit_points else 0

    print("-" * 40)
    print(f"[结果] 最终总盈亏: {total:.0f} 点")
    print(f"[结果] 最终胜率:   {win_rate:.1f}%")
    print(f"[结果] 交易场次:   {wins}胜 {losses}负 (共 {wins+losses} 笔)")
    print(f"[结果] 平均盈亏:   {avg_profit:.0f} 点/笔")
    print(f"[结果] 最大盈利:  {max_profit:.0f} 点")
    print(f"[结果] 最大亏损:  {max_loss:.0f} 点")

    # --- 绘图 ---
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

    ax1.set_title(f'Copper Strategy A (Max Profit) | Total: {total:.0f} pts | Win Rate: {win_rate:.1f}% | Trades: {wins+losses}', fontsize=14)
    ax1.legend(loc='upper left')

    # 副图
    ax2.plot(df['datetime'], df['ratio'], color='blue', label='MACD Ratio')
    ax2.axhline(RATIO_TRIGGER, color='red', linestyle='--', label=f'Trigger ({RATIO_TRIGGER})')
    ax2.fill_between(df['datetime'], 0, RATIO_TRIGGER, color='green', alpha=0.1)
    ax2.set_ylim(-1, 3)
    ax2.legend()

    plt.tight_layout()

    # 保存图表
    output_path = Path('D:/daily_stock_analysis/results/copper_strategy_a_backtest.png')
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
        'positions': positions
    }


if __name__ == "__main__":
    run_strategy()
