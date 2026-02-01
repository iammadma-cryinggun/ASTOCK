# -*- coding: utf-8 -*-
"""
===================================
期货/贵金属期权波动率监控模块
===================================

职责：
1. 获取期货/ETF 的历史价格数据
2. 计算历史波动率 (HV - Historical Volatility)
3. 获取隐含波动率 (IV - Implied Volatility)
4. 检测 IV-HV 背离信号
5. 生成风险预警报告

监控标的：
- 贵金属：GLD（黄金）、SLV（白银）、IAU（黄金）、PPLT（铂金）、PALL（钯金）
- 商品：USO（原油）、UNG（天然气）、DBA（农产品）、GLL（铜）
- 加密货币：BTC、ETH

核心策略：
- 当 IV 处于历史高位（>90% 分位）且 HV 显著低于 IV 时，发出崩盘预警
- 这意味着杠杆成本过高，但实际动能不足，多头将被时间损耗反噬
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class VolatilityMetrics:
    """波动率指标"""
    symbol: str                    # 标的代码
    name: str                      # 标的名称
    current_price: float           # 当前价格

    # 历史波动率 (HV)
    hv_20d: float                  # 20日历史波动率
    hv_60d: float                  # 60日历史波动率
    hv_percentile: float           # HV 历史分位数

    # 隐含波动率 (IV)
    iv_current: float              # 当前隐含波动率
    iv_percentile: float           # IV 历史分位数（0-100）
    iv_rank: float                 # IV Rank（当前IV相对于历史范围的位置）

    # 背离信号
    iv_hv_divergence: float        # IV-HV 背离度 (IV - HV)
    is_extreme_divergence: bool    # 是否极端背离
    risk_level: str                # 风险等级：low/medium/high/extreme

    # 期权链数据（如果有）
    put_call_ratio: Optional[float] = None  # Put/Call 比率
    skew: Optional[float] = None            # 波动率偏斜

    timestamp: datetime = None              # 数据时间


class FuturesVolatilityMonitor:
    """
    期货波动率监控器

    功能：
    1. 计算历史波动率 (HV)
    2. 估算隐含波动率 (IV)
    3. 检测 IV-HV 背离
    4. 生成风险预警
    """

    # 默认监控标的
    DEFAULT_SYMBOLS = {
        # 贵金属 ETF
        'GLD': '黄金SPDR',
        'SLV': '白银iShares',
        'IAU': '黄金iShares',
        'PPLT': '铂金',
        'PALL': '钯金',

        # 商品 ETF
        'USO': '原油',
        'UNG': '天然气',
        'DBC': '大宗商品',
        'DBA': '农产品',

        # 加密货币（如果有数据源）
        # 'BTC': '比特币',
        # 'ETH': '以太坊',
    }

    # IV 历史分位数阈值
    IV_PERCENTILE_WARNING = 80    # 警告阈值
    IV_PERCENTILE_DANGER = 90     # 危险阈值
    IV_PERCENTILE_EXTREME = 95    # 极端阈值

    # IV-HV 背离度阈值
    IV_HV_DIVERGENCE_WARNING = 0.15   # 15% 背离度警告
    IV_HV_DIVERGENCE_DANGER = 0.20     # 20% 背离度危险
    IV_HV_DIVERGENCE_EXTREME = 0.30    # 30% 背离度极端

    def __init__(self, data_provider=None):
        """
        初始化监控器

        Args:
            data_provider: 数据提供者（可选）
        """
        self.data_provider = data_provider

    def calculate_hv(
        self,
        prices: pd.Series,
        window: int = 20,
        annualize: bool = True
    ) -> float:
        """
        计算历史波动率 (HV)

        Args:
            prices: 价格序列
            window: 窗口期（天）
            annualize: 是否年化（一年252个交易日）

        Returns:
            历史波动率（百分比）
        """
        if len(prices) < 2:
            return 0.0

        # 计算对数收益率
        log_returns = np.log(prices / prices.shift(1)).dropna()

        # 计算标准差
        hv = log_returns.std()

        # 年化
        if annualize:
            hv = hv * np.sqrt(252)

        return float(hv * 100)  # 转换为百分比

    def calculate_iv_percentile(
        self,
        current_iv: float,
        historical_iv: List[float]
    ) -> float:
        """
        计算 IV 历史分位数

        Args:
            current_iv: 当前IV
            historical_iv: 历史IV列表

        Returns:
            IV 分位数（0-100）
        """
        if not historical_iv:
            return 50.0  # 默认中间值

        # 计算当前IV在历史中的百分位
        percentile = sum(1 for iv in historical_iv if iv <= current_iv) / len(historical_iv) * 100

        return percentile

    def detect_divergence(
        self,
        iv: float,
        hv: float,
        iv_percentile: float
    ) -> Tuple[bool, str]:
        """
        检测 IV-HV 背离信号

        Args:
            iv: 隐含波动率
            hv: 历史波动率
            iv_percentile: IV 分位数

        Returns:
            (是否背离, 风险等级)
        """
        # 计算背离度
        divergence = iv - hv

        # 判断风险等级
        if iv_percentile >= self.IV_PERCENTILE_EXTREME and divergence >= self.IV_HV_DIVERGENCE_EXTREME:
            return True, "extreme"
        elif iv_percentile >= self.IV_PERCENTILE_DANGER and divergence >= self.IV_HV_DIVERGENCE_DANGER:
            return True, "high"
        elif iv_percentile >= self.IV_PERCENTILE_WARNING and divergence >= self.IV_HV_DIVERGENCE_WARNING:
            return True, "medium"

        return False, "low"

    def analyze_symbol(self, symbol: str, name: str = None) -> Optional[VolatilityMetrics]:
        """
        分析单个标的的波动率指标

        Args:
            symbol: 标的代码
            name: 标的名称（可选）

        Returns:
            波动率指标对象
        """
        if not self.data_provider:
            logger.warning("数据提供者未配置，无法分析期货")
            return None

        try:
            # 获取历史价格数据（用于计算 HV）
            data = self.data_provider.get_stock_history(symbol, days=252)  # 一年数据

            if data is None or len(data) < 60:
                logger.warning(f"数据不足，无法分析 {symbol}")
                return None

            # 提取价格数据
            prices = pd.Series([d['close'] for d in data])
            current_price = float(prices.iloc[-1])

            # 计算 HV（历史波动率）
            hv_20d = self.calculate_hv(prices, window=20)
            hv_60d = self.calculate_hv(prices, window=60)

            # 计算 HV 历史分位数
            hv_list = []
            for i in range(60, len(prices)):
                window_prices = prices.iloc[i-60:i]
                hv = self.calculate_hv(window_prices, window=20)
                hv_list.append(hv)

            hv_percentile = self.calculate_iv_percentile(hv_20d, hv_list)

            # 获取 IV（隐含波动率）- 使用真实的波动率指数
            from src.volatility_index import get_volatility_fetcher

            fetcher = get_volatility_fetcher()

            # 设置数据提供者（用于降级方案）
            if self.data_provider:
                fetcher.set_data_provider(self.data_provider)

            iv_current = fetcher.get_volatility_index(symbol)

            if iv_current is None:
                logger.warning(f"无法获取 {symbol} 的 IV 数据")
                return None

            # 计算 IV 历史分位数 - 使用真实的历史数据（252个交易日）
            iv_percentile = fetcher.calculate_iv_percentile(symbol)

            if iv_percentile is None:
                logger.warning(f"无法计算 {symbol} 的 IV 分位数")
                iv_percentile = 50.0  # 默认值

            # 获取历史 IV 数据用于计算 IV Rank
            historical_iv_data = fetcher.get_historical_volatility_index(symbol, days=252)

            if historical_iv_data:
                iv_values = [d['value'] for d in historical_iv_data]
                iv_min = min(iv_values)
                iv_max = max(iv_values)
                if iv_max > iv_min:
                    iv_rank = (iv_current - iv_min) / (iv_max - iv_min) * 100
                else:
                    iv_rank = 50.0
            else:
                iv_rank = 50.0

            # 检测背离信号
            iv_hv_divergence = iv_current - hv_20d
            is_divergence, risk_level = self.detect_divergence(iv_current, hv_20d, iv_percentile)

            return VolatilityMetrics(
                symbol=symbol,
                name=name or symbol,
                current_price=current_price,
                hv_20d=hv_20d,
                hv_60d=hv_60d,
                hv_percentile=hv_percentile,
                iv_current=iv_current,
                iv_percentile=iv_percentile,
                iv_rank=iv_rank,
                iv_hv_divergence=iv_hv_divergence,
                is_extreme_divergence=is_divergence,
                risk_level=risk_level,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"分析 {symbol} 失败: {e}")
            return None

    def generate_risk_report(self, symbols: List[str] = None) -> str:
        """
        生成波动率风险报告

        Args:
            symbols: 要分析的标的列表（默认使用DEFAULT_SYMBOLS）

        Returns:
            格式化的风险报告文本
        """
        if symbols is None:
            symbols = list(self.DEFAULT_SYMBOLS.keys())

        results = []
        extreme_symbols = []

        for symbol in symbols:
            name = self.DEFAULT_SYMBOLS.get(symbol, symbol)
            metrics = self.analyze_symbol(symbol, name)

            if metrics:
                results.append(metrics)

                # 记录极端风险标的
                if metrics.is_extreme_divergence:
                    extreme_symbols.append(metrics)

        # 生成报告
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("📊 期货/贵金属期权波动率监控报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 60)
        report_lines.append("")

        # 极端风险预警
        if extreme_symbols:
            report_lines.append("🚨 " * 20)
            report_lines.append("【极端风险预警】IV-HV 背离信号")
            report_lines.append("🚨 " * 20)
            report_lines.append("")

            for metrics in extreme_symbols:
                report_lines.append(f"🔴 {metrics.name} ({metrics.symbol})")
                report_lines.append(f"   当前价格: ${metrics.current_price:.2f}")
                report_lines.append(f"   IV (隐含波动率): {metrics.iv_current:.2f}% (历史分位: {metrics.iv_percentile:.1f}%)")
                report_lines.append(f"   HV (历史波动率): {metrics.hv_20d:.2f}%")
                report_lines.append(f"   IV-HV 背离度: {metrics.iv_hv_divergence:.2f}%")
                report_lines.append(f"   风险等级: {metrics.risk_level.upper()}")
                report_lines.append("")
                report_lines.append("   ⚠️ 风险提示:")
                report_lines.append("   当 IV 处于历史高位且显著高于 HV 时，")
                report_lines.append("   意味着期权杠杆极其昂贵，多头面临时间损耗反噬。")
                report_lines.append("   一旦动能不足（甚至不需要下跌，只要横盘），")
                report_lines.append("   昂贵的杠杆成本将导致多头崩盘。")
                report_lines.append("")
            report_lines.append("")

        # 所有标的汇总
        report_lines.append("📋 所有标的波动率指标")
        report_lines.append("")

        for metrics in results:
            # 风险等级标记
            risk_emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'extreme': '🔴'
            }.get(metrics.risk_level, '⚪')

            report_lines.append(f"{risk_emoji} {metrics.name} ({metrics.symbol})")
            report_lines.append(f"   IV: {metrics.iv_current:.2f}% (Pctl: {metrics.iv_percentile:.1f}%) | HV: {metrics.hv_20d:.2f}%")
            report_lines.append(f"   背离度: {metrics.iv_hv_divergence:+.2f}% | 风险: {metrics.risk_level}")
            report_lines.append("")

        report_lines.append("=" * 60)
        report_lines.append("💡 策略说明:")
        report_lines.append("")
        report_lines.append("📌 核心指标:")
        report_lines.append("   • IV (隐含波动率): 市场预期，决定杠杆成本")
        report_lines.append("   • HV (历史波动率): 实际波动，标的表现")
        report_lines.append("   • IV-HV 背离: 当 IV >> HV 时，风险极高")
        report_lines.append("")
        report_lines.append("🎯 风险信号:")
        report_lines.append(f"   • IV 分位数 > {self.IV_PERCENTILE_WARNING}%: 警告")
        report_lines.append(f"   • IV 分位数 > {self.IV_PERCENTILE_DANGER}%: 危险")
        report_lines.append(f"   • IV-HV 背离 > {self.IV_HV_DIVERGENCE_WARNING}%: 预警")
        report_lines.append("")
        report_lines.append("💰 建议操作:")
        report_lines.append("   • 极端背离时: 避免做多，考虑对冲或减仓")
        report_lines.append("   • IV 回归理性后: 考虑建立多头仓位")
        report_lines.append("")
        report_lines.append("⚠️  免责声明: 本报告不构成投资建议，仅供参考")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    def get extreme_risk_symbols(self, symbols: List[str] = None) -> List[VolatilityMetrics]:
        """
        获取所有极端风险的标的

        Args:
            symbols: 要分析的标的列表

        Returns:
            极端风险标的列表
        """
        if symbols is None:
            symbols = list(self.DEFAULT_SYMBOLS.keys())

        extreme_list = []

        for symbol in symbols:
            name = self.DEFAULT_SYMBOLS.get(symbol, symbol)
            metrics = self.analyze_symbol(symbol, name)

            if metrics and metrics.is_extreme_divergence:
                extreme_list.append(metrics)

        # 按背离度排序
        extreme_list.sort(key=lambda m: m.iv_hv_divergence, reverse=True)

        return extreme_list


# 便捷函数
def get_volatility_monitor(data_provider=None) -> FuturesVolatilityMonitor:
    """获取波动率监控器实例"""
    return FuturesVolatilityMonitor(data_provider)
