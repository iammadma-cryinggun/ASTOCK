# -*- coding: utf-8 -*-
"""
===================================
结构张力模型 (Structural Tension Model)
===================================

核心思想：
将价格波动映射到复平面，通过 FFT 提取主要频率成分，
使用 Hilbert 变换计算"张力"（虚部），识别市场的拐点。

避免未来函数：使用滚动窗口，每个时刻只能看到历史数据。

算法步骤：
1. 对数化价格
2. 去趋势（线性回归）
3. FFT 变换
4. Top N 能量过滤
5. iFFT 重构
6. Hilbert 变换
7. 计算张力（虚部）
8. 标准化

参考：
- LPPL (Log-Periodic Power Law)
- 希尔伯特-黄变换
- 频域分析
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import signal
from scipy.fft import fft, ifft
from scipy.signal import detrend, hilbert
from scipy.stats import linregress

logger = logging.getLogger(__name__)


class StructuralTensionModel:
    """
    结构张力模型

    使用 FFT-Hilbert 方法提取价格的结构性特征，
    通过"张力"指标识别市场的拐点。
    """

    def __init__(
        self,
        top_n_main: int = 8,          # 主趋势频率数量 (Top 1-8)
        top_n_lead: int = 16,          # 先行指标频率数量 (Top 9-16)
        window_size: int = 200,        # 滚动窗口大小（交易日）
        tension_threshold: float = 1.6 # 张力阈值
    ):
        """
        初始化结构张力模型

        Args:
            top_n_main: 主趋势频率数量（Top N，1-8）
            top_n_lead: 先行指标频率数量（Top N，9-16）
            window_size: 计算窗口大小（至少 100 个交易日）
            tension_threshold: 张力阈值，超过此值视为极端
        """
        self.top_n_main = top_n_main
        self.top_n_lead = top_n_lead
        self.window_size = window_size
        self.tension_threshold = tension_threshold

        logger.info(f"[StructuralTension] 初始化完成")
        logger.info(f"  主趋势 Top N: {top_n_main}")
        logger.info(f"  先行指标 Top N: {top_n_lead}")
        logger.info(f"  窗口大小: {window_size} 交易日")
        logger.info(f"  张力阈值: {tension_threshold}")

    def preprocess(self, prices: np.ndarray) -> np.ndarray:
        """
        数据预处理：对数化 + 去趋势

        Args:
            prices: 原始价格序列

        Returns:
            预处理后的序列
        """
        # 1. 对数化（将涨跌幅线性化）
        log_prices = np.log(prices)

        # 2. 去趋势（移除线性趋势）
        detrended = detrend(log_prices)

        return detrended

    def extract_top_n_frequencies(
        self,
        f_vals: np.ndarray,
        top_n: int
    ) -> np.ndarray:
        """
        提取 Top N 最强频率成分

        Args:
            f_vals: FFT 结果
            top_n: 保留的频率数量

        Returns:
            滤波后的 FFT 结果
        """
        n = len(f_vals)
        half = n // 2

        # 获取振幅（能量）
        amplitudes = np.abs(f_vals[:half])

        # 忽略直流分量（频率 0）
        amplitudes[0] = 0

        # 找到 Top N 的索引
        top_indices = np.argsort(amplitudes)[-top_n:]

        # 构建滤波器
        filt = np.zeros_like(f_vals, dtype=complex)
        for idx in top_indices:
            filt[idx] = f_vals[idx]
            # 负频率共轭
            filt[-idx] = np.conj(f_vals[idx])

        return filt

    def reconstruct_signal(self, f_vals: np.ndarray) -> np.ndarray:
        """
        信号重构：iFFT

        Args:
            f_vals: 滤波后的 FFT 结果

        Returns:
            重构的时域信号
        """
        recon = np.real(ifft(f_vals))
        return recon

    def calculate_tension(self, signal: np.ndarray) -> np.ndarray:
        """
        计算张力：Hilbert 变换后的虚部

        Args:
            signal: 重构的信号

        Returns:
            张力序列（虚部）
        """
        # Hilbert 变换
        analytic = hilbert(signal)

        # 虚部代表"势能"或"旋转力矩"
        tension = np.imag(analytic)

        return tension

    def normalize_tension(self, tension: np.ndarray) -> np.ndarray:
        """
        标准化张力（除以标准差）

        Args:
            tension: 原始张力序列

        Returns:
            标准化后的张力
        """
        std = np.std(tension)
        if std == 0:
            return tension
        return tension / std

    def calculate_single_point(
        self,
        prices: np.ndarray,
        mode: str = "main"
    ) -> float:
        """
        计算单点张力（避免未来函数）

        Args:
            prices: 价格序列（必须是历史数据）
            mode: "main"（主趋势）或 "lead"（先行指标）

        Returns:
            当前时刻的张力值
        """
        if len(prices) < self.window_size:
            logger.warning(f"[StructuralTension] 数据不足：{len(prices)} < {self.window_size}")
            return 0.0

        # 只使用最近 window_size 个数据点
        window_prices = prices[-self.window_size:]

        # 1. 预处理
        processed = self.preprocess(window_prices)

        # 2. FFT
        f_vals = fft(processed)

        # 3. Top N 过滤
        top_n = self.top_n_main if mode == "main" else self.top_n_lead
        filtered = self.extract_top_n_frequencies(f_vals, top_n)

        # 4. 重构
        recon = self.reconstruct_signal(filtered)

        # 5. Hilbert 变换 + 张力
        tension = self.calculate_tension(recon)

        # 6. 标准化
        normalized = self.normalize_tension(tension)

        # 返回最后一个点的值（当前时刻）
        return float(normalized[-1])

    def walk_forward_test(
        self,
        df: pd.DataFrame,
        mode: str = "main"
    ) -> pd.DataFrame:
        """
        滚动回测（避免未来函数）

        模拟真实交易：每个时刻只能看到历史数据。

        Args:
            df: DataFrame，必须包含 'close' 和 'date' 列
            mode: "main"（主趋势）或 "lead"（先行指标）

        Returns:
            结果 DataFrame，包含 date, price, tension, signal
        """
        prices = df['close'].values
        dates = df['date'].values if 'date' in df.columns else df.index

        results = []

        logger.info(f"[StructuralTension] 开始滚动回测 (mode={mode})...")
        logger.info(f"  数据点数: {len(prices)}")
        logger.info(f"  窗口大小: {self.window_size}")

        # 从第 window_size 个点开始，逐个计算
        for i in range(self.window_size, len(prices)):
            # 截取"当时"可见的数据（绝不看未来）
            history_window = prices[:i+1]

            # 计算当前时刻的张力
            try:
                tension = self.calculate_single_point(history_window, mode)

                results.append({
                    'date': dates[i],
                    'price': prices[i],
                    'tension': tension
                })
            except Exception as e:
                logger.error(f"[StructuralTension] 计算失败 (i={i}): {e}")
                continue

            # 每 100 个点输出一次进度
            if (i - self.window_size) % 100 == 0:
                logger.info(f"  进度: {i - self.window_size}/{len(prices) - self.window_size}")

        result_df = pd.DataFrame(results)

        # 生成信号
        result_df['signal'] = self._generate_signals(result_df)

        logger.info(f"[StructuralTension] 回测完成，共 {len(result_df)} 个数据点")

        return result_df

    def _generate_signals(self, df: pd.DataFrame) -> List[str]:
        """
        生成交易信号

        规则：
        - 张力从低到高拐头向上 → 买入信号
        - 张力从高到低拐头向下 → 卖出信号

        Args:
            df: 包含 tension 列的 DataFrame

        Returns:
            信号列表
        """
        signals = []
        tensions = df['tension'].values

        for i in range(1, len(tensions)):
            prev = tensions[i-1]
            curr = tensions[i]

            # 拐头向上（之前 < -threshold，现在 > 之前）
            if prev < -self.tension_threshold and curr > prev:
                signals.append("BUY")

            # 拐头向下（之前 > threshold，现在 < 之前）
            elif prev > self.tension_threshold and curr < prev:
                signals.append("SELL")

            else:
                signals.append("HOLD")

        # 第一天没有信号
        signals.insert(0, "HOLD")

        return signals

    def analyze_current_state(
        self,
        df: pd.DataFrame
    ) -> Dict[str, any]:
        """
        分析当前市场状态

        Args:
            df: DataFrame，必须包含 'close' 列

        Returns:
            当前状态字典
        """
        prices = df['close'].values

        if len(prices) < self.window_size:
            return {
                'error': f'数据不足，需要至少 {self.window_size} 个交易日'
            }

        # 计算主趋势和先行指标的张力
        tension_main = self.calculate_single_point(prices, mode="main")
        tension_lead = self.calculate_single_point(prices, mode="lead")

        # 判断状态
        state = self._get_state_description(tension_main, tension_lead)

        return {
            'tension_main': tension_main,
            'tension_lead': tension_lead,
            'state': state['label'],
            'description': state['description'],
            'recommendation': state['recommendation'],
            'risk_level': state['risk_level']
        }

    def _get_state_description(
        self,
        tension_main: float,
        tension_lead: float
    ) -> Dict[str, str]:
        """
        根据张力值判断市场状态

        Args:
            tension_main: 主趋势张力
            tension_lead: 先行指标张力

        Returns:
            状态描述
        """
        # 极端状态
        if tension_main < -2.0:
            label = "极度超卖"
            description = "主趋势张力极低，市场可能处于底部区域"
            recommendation = "考虑买入"
            risk_level = "low"
        elif tension_main > 2.0:
            label = "极度超买"
            description = "主趋势张力极高，市场可能处于顶部区域"
            recommendation = "考虑卖出"
            risk_level = "high"

        # 正常状态
        elif tension_main < -self.tension_threshold:
            label = "超卖"
            description = "主趋势张力较低，卖压可能接近枯竭"
            recommendation = "关注买入机会"
            risk_level = "medium"
        elif tension_main > self.tension_threshold:
            label = "超买"
            description = "主趋势张力较高，买盘可能接近枯竭"
            recommendation = "关注卖出风险"
            risk_level = "medium"

        # 中性状态
        else:
            label = "中性"
            description = "主趋势张力正常，市场处于平衡状态"
            recommendation = "观望"
            risk_level = "low"

        # 先行指标提示
        if tension_lead > 1.0 and tension_main < 0:
            description += "，先行指标提示可能即将反转向上"
        elif tension_lead < -1.0 and tension_main > 0:
            description += "，先行指标提示可能即将反转向下"

        return {
            'label': label,
            'description': description,
            'recommendation': recommendation,
            'risk_level': risk_level
        }


# === 便捷函数 ===

_structural_tension_model: Optional[StructuralTensionModel] = None


def get_structural_tension_model(
    top_n_main: int = 8,
    top_n_lead: int = 16,
    window_size: int = 200,
    tension_threshold: float = 1.6
) -> StructuralTensionModel:
    """
    获取结构张力模型单例

    Args:
        top_n_main: 主趋势 Top N
        top_n_lead: 先行指标 Top N
        window_size: 窗口大小
        tension_threshold: 张力阈值

    Returns:
        StructuralTensionModel 实例
    """
    global _structural_tension_model

    if _structural_tension_model is None:
        _structural_tension_model = StructuralTensionModel(
            top_n_main=top_n_main,
            top_n_lead=top_n_lead,
            window_size=window_size,
            tension_threshold=tension_threshold
        )

    return _structural_tension_model


if __name__ == "__main__":
    # 测试代码
    import matplotlib.pyplot as plt

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )

    # 生成模拟数据
    print("=" * 60)
    print("结构张力模型测试")
    print("=" * 60)

    # 创建模拟价格数据（正弦波 + 噪音 + 趋势）
    np.random.seed(42)
    n = 500
    t = np.linspace(0, 4*np.pi, n)
    prices = 100 + 10*np.sin(t) + 5*np.sin(3*t) + np.random.randn(n)*2

    df = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=n),
        'close': prices
    })

    # 创建模型
    model = get_structural_tension_model(window_size=100)

    # 滚动回测
    print("\n[测试] 运行滚动回测...")
    result_df = model.walk_forward_test(df, mode="main")

    # 分析当前状态
    print("\n[测试] 当前状态:")
    current_state = model.analyze_current_state(df)
    for key, value in current_state.items():
        print(f"  {key}: {value}")

    # 计算信号统计
    print("\n[测试] 信号统计:")
    signal_counts = result_df['signal'].value_counts()
    for signal, count in signal_counts.items():
        print(f"  {signal}: {count}")

    # 绘图（如果需要）
    try:
        import matplotlib
        matplotlib.use('Agg')  # 非交互式后端
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))

        # 原始价格
        ax1.plot(result_df['date'], result_df['price'], label='Price', color='black')
        ax1.set_ylabel('Price')
        ax1.set_title('Structural Tension Model - Walk Forward Test')
        ax1.legend()
        ax1.grid(True)

        # 张力
        ax2.plot(result_df['date'], result_df['tension'], label='Tension', color='blue')
        ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax2.axhline(y=1.6, color='red', linestyle='--', alpha=0.5, label='Threshold')
        ax2.axhline(y=-1.6, color='green', linestyle='--', alpha=0.5)
        ax2.set_ylabel('Tension')
        ax2.legend()
        ax2.grid(True)

        # 信号
        buy_dates = result_df[result_df['signal'] == 'BUY']['date']
        sell_dates = result_df[result_df['signal'] == 'SELL']['date']
        buy_prices = result_df[result_df['signal'] == 'BUY']['price']
        sell_prices = result_df[result_df['signal'] == 'SELL']['price']

        ax3.plot(result_df['date'], result_df['price'], color='black', alpha=0.3)
        ax3.scatter(buy_dates, buy_prices, color='green', marker='^', s=100, label='Buy', zorder=5)
        ax3.scatter(sell_dates, sell_prices, color='red', marker='v', s=100, label='Sell', zorder=5)
        ax3.set_ylabel('Price')
        ax3.set_xlabel('Date')
        ax3.legend()
        ax3.grid(True)

        plt.tight_layout()
        plt.savefig('structural_tension_test.png', dpi=100)
        print("\n[完成] 图表已保存: structural_tension_test.png")
    except ImportError:
        print("\n[跳过] matplotlib 未安装，跳过绘图")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
