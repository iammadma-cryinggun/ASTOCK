# -*- coding: utf-8 -*-
"""
===================================
沪铜期货策略 A - 网格参数优化
===================================

测试多个参数组合，寻找最优配置
"""

import pandas as pd
import numpy as np
from pathlib import Path
import time
from itertools import product
from typing import Dict, List, Tuple

# 数据路径
FILE_PATH = r'D:\期货数据\沪铜4小时K线_20260203_130227.csv'


# ==========================================
# 参数网格定义
# ==========================================

# 网格配置（可调整）
PARAM_GRID = {
    'RATIO_TRIGGER': [0.9, 1.0, 1.15, 1.3, 1.5],
    'RSI_FILTER': [45, 50, 55],
    'STC_SELL_ZONE': [85, 90, 95],
    'EMA_FAST': [5],
    'EMA_SLOW': [15],
    'MACD_FAST': [12],
    'MACD_SLOW': [26],
    'MACD_SIGNAL': [9],
    'RSI_PERIOD': [14],
    'STOP_LOSS_PCT': [0.02],
}

# 如果要测试更多参数，取消注释以下代码
# PARAM_GRID = {
#     'RATIO_TRIGGER': [0.8, 0.9, 1.0, 1.15, 1.3, 1.5],
#     'RSI_FILTER': [40, 45, 50, 55, 60],
#     'STC_SELL_ZONE': [80, 85, 90, 95],
#     'EMA_FAST': [3, 5, 7],
#     'EMA_SLOW': [10, 15, 20],
#     'STOP_LOSS_PCT': [0.015, 0.02, 0.025],
# }


def calculate_indicators(df, params):
    """计算技术指标"""
    # 1. EMA
    df['ema_fast'] = df['close'].ewm(span=params['EMA_FAST'], adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=params['EMA_SLOW'], adjust=False).mean()

    # 2. MACD & Ratio
    exp1 = df['close'].ewm(span=params['MACD_FAST'], adjust=False).mean()
    exp2 = df['close'].ewm(span=params['MACD_SLOW'], adjust=False).mean()
    df['macd_dif'] = exp1 - exp2
    df['macd_dea'] = df['macd_dif'].ewm(span=params['MACD_SIGNAL'], adjust=False).mean()
    df['ratio'] = np.where(df['macd_dea'] != 0, df['macd_dif'] / df['macd_dea'], 0)

    # 3. RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/params['RSI_PERIOD'], adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/params['RSI_PERIOD'], adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 4. STC
    stc_macd = df['close'].ewm(span=params['STC_FAST'], adjust=False).mean() - \
               df['close'].ewm(span=params['STC_SLOW'], adjust=False).mean()
    stoch_period = params['STC_LENGTH']
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


def run_backtest(df, params):
    """运行单次回测"""
    df = calculate_indicators(df.copy(), params)

    # 预计算前值
    df['ema_fast_prev'] = df['ema_fast'].shift(1)
    df['ema_slow_prev'] = df['ema_slow'].shift(1)
    df['ratio_prev'] = df['ratio'].shift(1)
    df['dif_prev'] = df['macd_dif'].shift(1)
    df['stc_prev'] = df['stc'].shift(1)

    # 信号条件
    trend_up = df['ema_fast'] > df['ema_slow']
    ratio_safe = (df['ratio'] > 0) & (df['ratio'] < params['RATIO_TRIGGER'])
    ratio_shrinking = df['ratio'] < df['ratio_prev']
    turning_up = df['macd_dif'] > df['dif_prev']
    is_strong = df['rsi'] > params['RSI_FILTER']
    ema_cross = (df['ema_fast_prev'] <= df['ema_slow_prev']) & (df['ema_fast'] > df['ema_slow'])

    df['sniper_signal'] = trend_up & ratio_safe & ratio_shrinking & turning_up & is_strong
    df['chase_signal'] = ema_cross & is_strong
    df['buy_signal'] = df['sniper_signal'] | df['chase_signal']

    stc_exit = (df['stc_prev'] > params['STC_SELL_ZONE']) & (df['stc'] < df['stc_prev'])
    trend_exit = df['ema_fast'] < df['ema_slow']
    df['exit_signal'] = stc_exit | trend_exit

    # 回测循环
    holding = False
    entry_price = 0.0
    profit_points = []
    wins = 0
    losses = 0

    for i in range(1, len(df)):
        row = df.iloc[i]

        if not holding:
            if row['buy_signal']:
                holding = True
                entry_price = row['close']
        elif holding:
            stop_price = entry_price * (1 - params['STOP_LOSS_PCT'])

            if row['low'] <= stop_price:
                holding = False
                diff = stop_price - entry_price
                profit_points.append(diff)
                if diff > 0:
                    wins += 1
                else:
                    losses += 1

            elif row['exit_signal'] and (row['stc_prev'] > params['STC_SELL_ZONE']) and (row['stc'] < row['stc_prev']):
                holding = False
                diff = row['close'] - entry_price
                profit_points.append(diff)
                if diff > 0:
                    wins += 1
                else:
                    losses += 1

            elif row['ema_fast'] < row['ema_slow']:
                holding = False
                diff = row['close'] - entry_price
                profit_points.append(diff)
                if diff > 0:
                    wins += 1
                else:
                    losses += 1

    # 统计结果
    total = sum(profit_points)
    win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
    avg_profit = np.mean(profit_points) if profit_points else 0
    max_profit = max(profit_points) if profit_points else 0
    max_loss = min(profit_points) if profit_points else 0
    max_drawdown = calculate_max_drawdown(profit_points)

    return {
        'total_profit': total,
        'win_rate': win_rate,
        'trades': wins + losses,
        'wins': wins,
        'losses': losses,
        'avg_profit': avg_profit,
        'max_profit': max_profit,
        'max_loss': max_loss,
        'max_drawdown': max_drawdown,
        'profit_factor': calculate_profit_factor(profit_points)
    }


def calculate_max_drawdown(profit_list):
    """计算最大回撤"""
    if not profit_list:
        return 0

    cumulative = np.cumsum(profit_list)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = running_max - cumulative
    return max(drawdown)


def calculate_profit_factor(profit_list):
    """计算盈亏比"""
    if not profit_list:
        return 0

    profits = [p for p in profit_list if p > 0]
    losses = [abs(p) for p in profit_list if p < 0]

    if not losses:
        return float('inf') if profits else 0

    return sum(profits) / sum(losses)


def generate_param_combinations():
    """生成所有参数组合"""
    keys = PARAM_GRID.keys()
    values = PARAM_GRID.values()
    combinations = [dict(zip(keys, v)) for v in product(*values)]

    # 添加固定参数
    fixed_params = {
        'STC_LENGTH': 10,
        'STC_FAST': 23,
        'STC_SLOW': 50,
    }

    for combo in combinations:
        combo.update(fixed_params)

    return combinations


def run_grid_optimization():
    """运行网格优化"""
    print("=" * 80)
    print("沪铜策略 A - 网格参数优化")
    print("=" * 80)

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

    print(f"[数据] 时间范围: {df['datetime'].iloc[0]} ~ {df['datetime'].iloc[-1]}")
    print(f"[数据] K线数量: {len(df)} 根")

    # 生成参数组合
    combinations = generate_param_combinations()
    total_combinations = len(combinations)

    print(f"\n[网格] 参数组合总数: {total_combinations}")
    print(f"[网格] 测试参数:")
    for key, values in PARAM_GRID.items():
        print(f"  - {key}: {values}")

    print(f"\n[开始] 网格搜索...")
    print("-" * 80)

    # 运行优化
    results = []
    start_time = time.time()

    for i, params in enumerate(combinations, 1):
        iter_start = time.time()
        result = run_backtest(df, params)
        iter_time = time.time() - iter_start

        result['params'] = params
        result['iter_time'] = iter_time
        results.append(result)

        # 进度输出
        progress = i / total_combinations * 100
        print(f"[{i}/{total_combinations}] {progress:.1f}% | "
              f"总盈亏: {result['total_profit']:.0f} | "
              f"胜率: {result['win_rate']:.1f}% | "
              f"交易: {result['trades']}笔 | "
              f"耗时: {iter_time:.3f}s")

    total_time = time.time() - start_time

    # 排序结果
    results_sorted = sorted(results, key=lambda x: x['total_profit'], reverse=True)

    # 输出最优结果
    print("\n" + "=" * 80)
    print("优化完成！")
    print("=" * 80)
    print(f"[统计] 总耗时: {total_time:.2f} 秒")
    print(f"[统计] 平均每组: {total_time/total_combinations:.3f} 秒")

    # Top 10
    print("\n" + "=" * 80)
    print("Top 10 最优参数组合 (按总盈亏排序)")
    print("=" * 80)

    for i, result in enumerate(results_sorted[:10], 1):
        print(f"\n第 {i} 名:")
        print(f"  总盈亏:     {result['total_profit']:>10.0f} 点")
        print(f"  胜率:       {result['win_rate']:>10.1f}%")
        print(f"  交易次数:   {result['trades']:>10} 笔")
        print(f"  平均盈亏:   {result['avg_profit']:>10.1f} 点")
        print(f"  最大盈利:   {result['max_profit']:>10.0f} 点")
        print(f"  最大亏损:   {result['max_loss']:>10.0f} 点")
        print(f"  最大回撤:   {result['max_drawdown']:>10.0f} 点")
        print(f"  盈亏比:     {result['profit_factor']:>10.2f}")
        print(f"  参数:")
        for key, value in result['params'].items():
            if key in PARAM_GRID.keys():
                print(f"    {key}: {value}")

    # 保存结果
    output_path = Path('D:/daily_stock_analysis/results/copper_optimization_results.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 转换为 DataFrame
    df_results = pd.DataFrame(results)
    # 展开参数字典
    params_df = pd.DataFrame(df_results['params'].tolist())
    df_results = pd.concat([df_results.drop('params', axis=1), params_df], axis=1)

    # 排序
    df_results = df_results.sort_values('total_profit', ascending=False)

    # 保存
    df_results.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n[保存] 结果已保存: {output_path}")

    # 对比原版
    print("\n" + "=" * 80)
    print("原版 vs 最优版本对比")
    print("=" * 80)

    original_params = {
        'RATIO_TRIGGER': 1.15,
        'RSI_FILTER': 50,
        'STC_SELL_ZONE': 90,
        'EMA_FAST': 5,
        'EMA_SLOW': 15,
        'MACD_FAST': 12,
        'MACD_SLOW': 26,
        'MACD_SIGNAL': 9,
        'RSI_PERIOD': 14,
        'STOP_LOSS_PCT': 0.02,
        'STC_LENGTH': 10,
        'STC_FAST': 23,
        'STC_SLOW': 50,
    }

    original_result = run_backtest(df, original_params)
    best_result = results_sorted[0]

    print(f"\n原版参数 (RATIO={original_params['RATIO_TRIGGER']}):")
    print(f"  总盈亏: {original_result['total_profit']:.0f} 点")
    print(f"  胜率: {original_result['win_rate']:.1f}%")
    print(f"  交易: {original_result['trades']} 笔")

    print(f"\n最优参数 (RATIO={best_result['params']['RATIO_TRIGGER']}):")
    print(f"  总盈亏: {best_result['total_profit']:.0f} 点")
    print(f"  胜率: {best_result['win_rate']:.1f}%")
    print(f"  交易: {best_result['trades']} 笔")

    improvement = best_result['total_profit'] - original_result['total_profit']
    improvement_pct = (improvement / abs(original_result['total_profit'])) * 100

    print(f"\n改进:")
    print(f"  绝对提升: {improvement:+.0f} 点 ({improvement_pct:+.1f}%)")

    return results_sorted


if __name__ == "__main__":
    results = run_grid_optimization()
