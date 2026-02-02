# -*- coding: utf-8 -*-
"""
===================================
期货期权隐含波动率与 VIX 指数计算模块（完整版）
===================================

职责：
1. 计算 IV（隐含波动率）- Black-76 模型 + 牛顿迭代法
2. 计算 VIX 指数（方差互换算法）
3. 多商品配置管理（针对不同品种的参数校准）
4. 三大过滤器：流动性、利率切换、IV Rank/IV Percentile

支持的商品类别：
- 贵金属：黄金、白银、铂金、钯金
- 能源化工：原油、燃油、LPG、沥青
- 农产品：大豆、玉米、棉花、白糖
- 黑色系：铁矿石、螺纹钢、热卷
- 有色金属：铜、铝、锌、镍

核心算法：
- Black-76 模型（期货期权专用）
- 牛顿-拉夫逊法（Newton-Raphson）求解 IV
- VIX 方差互换算法（CBOE 标准）
- IV Percentile 智能报警系统
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

import numpy as np
import pandas as pd
from scipy.stats import norm

logger = logging.getLogger(__name__)


# ==========================================
# 1. 数据模型定义
# ==========================================

class CurrencyType(Enum):
    """货币类型"""
    USD = "USD"  # 美元利率
    CNY = "CNY"  # 人民币利率


class OptionType(Enum):
    """期权类型"""
    CALL = "call"   # 看涨期权
    PUT = "put"     # 看跌期权


class CommodityCategory(Enum):
    """商品类别"""
    PRECIOUS_METAL = "precious_metal"    # 贵金属
    ENERGY = "energy"                     # 能源化工
    AGRICULTURE = "agriculture"           # 农产品
    FERROUS = "ferrous"                   # 黑色系
    NON_FERROUS = "non_ferrous"           # 有色金属


@dataclass
class OptionData:
    """期权数据"""
    symbol: str              # 期权代码（如 "IO2406-C-3500"）
    option_type: OptionType  # 期权类型
    strike: float            # 行权价
    market_price: float      # 市场价格（中间价）
    bid: float               # 买一价
    ask: float               # 卖一价
    volume: int              # 成交量
    open_interest: int       # 持仓量
    expiry_date: datetime    # 到期日

    def __post_init__(self):
        """数据校验"""
        if self.market_price <= 0:
            raise ValueError(f"期权价格必须大于0: {self.symbol} price={self.market_price}")
        if self.strike <= 0:
            raise ValueError(f"行权价必须大于0: {self.symbol} strike={self.strike}")


@dataclass
class FuturesData:
    """期货数据"""
    symbol: str          # 期货代码（如 "AG2406"）
    price: float         # 当前价格
    currency: CurrencyType  # 货币类型


@dataclass
class ImpliedVolatilityResult:
    """隐含波动率计算结果"""
    symbol: str          # 期权代码
    iv: float            # 隐含波动率（小数形式，如 0.25 = 25%）
    iterations: int      # 迭代次数
    converged: bool      # 是否收敛
    theoretical_price: float  # 理论价格
    error: float         # 误差（理论价 - 市场价）
    vega: float          # Vega 值


@dataclass
class VIXResult:
    """VIX 指数计算结果"""
    symbol: str          # 商品代码（如 "SLV"）
    vix: float           # VIX 指数（百分比，如 25.3）
    call_contribution: float  # 看涨期权贡献
    put_contribution: float    # 看跌期权贡献
    total_options: int   # 使用的期权总数
    calculation_time: datetime  # 计算时间
    iv_rank: Optional[float] = None  # IV Rank（0-100）
    iv_percentile: Optional[float] = None  # IV Percentile（0-100）


# ==========================================
# 2. Black-76 模型实现
# ==========================================

class Black76Model:
    """
    Black-76 期权定价模型

    适用于期货期权的定价，与 Black-Scholes 的区别在于贴现因子的处理。

    公式：
    c = e^(-rT) * [F * N(d1) - K * N(d2)]
    p = e^(-rT) * [K * N(-d2) - F * N(-d1)]

    其中：
    d1 = [ln(F/K) + (σ²/2)T] / (σ√T)
    d2 = d1 - σ√T
    """

    @staticmethod
    def call_price(F: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        计算看涨期权理论价格

        Args:
            F: 期货当前价格 (Futures Price)
            K: 行权价 (Strike Price)
            T: 剩余时间（年化）
            r: 无风险利率（年化）
            sigma: 波动率（年化）

        Returns:
            看涨期权理论价格
        """
        # 边界检查
        if T < 1e-6:  # 到期或临近到期
            return max(F - K, 0.0) * np.exp(-r * T)

        if sigma < 1e-6:  # 零波动率
            return max(F - K, 0.0) * np.exp(-r * T)

        # 计算 d1, d2
        d1 = (np.log(F / K) + (0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        # Black-76 公式
        price = np.exp(-r * T) * (F * norm.cdf(d1) - K * norm.cdf(d2))
        return price

    @staticmethod
    def put_price(F: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        计算看跌期权理论价格

        Args:
            F: 期货当前价格
            K: 行权价
            T: 剩余时间（年化）
            r: 无风险利率（年化）
            sigma: 波动率（年化）

        Returns:
            看跌期权理论价格
        """
        # 边界检查
        if T < 1e-6:
            return max(K - F, 0.0) * np.exp(-r * T)

        if sigma < 1e-6:
            return max(K - F, 0.0) * np.exp(-r * T)

        # 计算 d1, d2
        d1 = (np.log(F / K) + (0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        # Black-76 公式（看跌）
        price = np.exp(-r * T) * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
        return price

    @staticmethod
    def vega(F: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        计算 Vega（期权价格对波动率的敏感度）

        公式：
        vega = F * e^(-rT) * N'(d1) * √T

        其中 N'(d1) 是标准正态分布的概率密度函数

        Args:
            F: 期货当前价格
            K: 行权价
            T: 剩余时间（年化）
            r: 无风险利率（年化）
            sigma: 波动率（年化）

        Returns:
            Vega 值（价格对波动率的导数）
        """
        if T < 1e-6 or sigma < 1e-6:
            return 0.0

        d1 = (np.log(F / K) + (0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        vega = F * np.exp(-r * T) * norm.pdf(d1) * np.sqrt(T)
        return vega


# ==========================================
# 3. 隐含波动率计算器（牛顿迭代法）
# ==========================================

class ImpliedVolatilityCalculator:
    """
    隐含波动率计算器

    使用牛顿-拉夫逊法（Newton-Raphson）求解非线性方程：
    f(σ) = 理论价格(σ) - 市场价格 = 0

    迭代公式：
    σ_{n+1} = σ_n - f(σ_n) / f'(σ_n)
            = σ_n - (理论价 - 市场价) / vega
    """

    def __init__(
        self,
        tolerance: float = 1e-6,
        max_iterations: int = 100,
        initial_sigma: float = 0.5
    ):
        """
        初始化计算器

        Args:
            tolerance: 收敛阈值（默认 1e-6）
            max_iterations: 最大迭代次数（默认 100）
            initial_sigma: 初始波动率猜测值（默认 50%）
        """
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        self.initial_sigma = initial_sigma

    def calculate(
        self,
        option: OptionData,
        futures: FuturesData,
        risk_free_rate: float
    ) -> ImpliedVolatilityResult:
        """
        计算隐含波动率

        Args:
            option: 期权数据
            futures: 期货数据
            risk_free_rate: 无风险利率（年化）

        Returns:
            ImpliedVolatilityResult 计算结果
        """
        # 计算剩余时间（年化）
        T = self._calculate_time_to_expiry(option.expiry_date)

        # 初始化
        sigma = self.initial_sigma
        F = futures.price
        K = option.strike
        r = risk_free_rate
        market_price = option.market_price

        # 选择定价函数
        if option.option_type == OptionType.CALL:
            price_func = Black76Model.call_price
        else:
            price_func = Black76Model.put_price

        # 牛顿迭代法
        for i in range(self.max_iterations):
            # 计算理论价格
            theoretical_price = price_func(F, K, T, r, sigma)

            # 计算误差
            diff = theoretical_price - market_price

            # 检查收敛
            if abs(diff) < self.tolerance:
                return ImpliedVolatilityResult(
                    symbol=option.symbol,
                    iv=sigma,
                    iterations=i + 1,
                    converged=True,
                    theoretical_price=theoretical_price,
                    error=diff,
                    vega=Black76Model.vega(F, K, T, r, sigma)
                )

            # 计算 Vega
            vega = Black76Model.vega(F, K, T, r, sigma)

            # 防止除零
            if abs(vega) < 1e-8:
                logger.warning(f"[{option.symbol}] Vega 接近零，停止迭代")
                break

            # 更新 sigma
            sigma = sigma - diff / vega

            # 边界保护
            sigma = max(0.001, min(sigma, 5.0))  # 限制在 [0.1%, 500%]

        # 未收敛，返回最后一次结果
        return ImpliedVolatilityResult(
            symbol=option.symbol,
            iv=sigma,
            iterations=self.max_iterations,
            converged=False,
            theoretical_price=theoretical_price,
            error=diff,
            vega=vega
        )

    def _calculate_time_to_expiry(self, expiry_date: datetime) -> float:
        """
        计算剩余时间（年化）

        Args:
            expiry_date: 到期日

        Returns:
            年化时间（如 30天 = 30/365 = 0.0822）
        """
        now = datetime.now(expiry_date.tzinfo)
        time_diff = expiry_date - now
        seconds = time_diff.total_seconds()

        if seconds <= 0:
            logger.warning(f"期权已到期: {expiry_date}")
            return 0.0

        # 年化（使用 365 天）
        T = seconds / (365.25 * 24 * 3600)

        # 防止 T 过小导致计算不稳定
        if T < 0.001:  # 小于约 9 小时
            logger.debug(f"剩余时间过小: {T:.6f} 年，设为 0.001")
            T = 0.001

        return T


# ==========================================
# 4. 三大过滤器
# ==========================================

class LiquidityFilter:
    """
    过滤器 1：流动性检查

    过滤掉流动性差的期权，这些期权的价格失真，计算出来的 IV 不可靠。
    """

    def __init__(
        self,
        min_volume: int = 500,
        min_open_interest: int = 1000,
        max_bid_ask_spread_pct: float = 0.20
    ):
        """
        初始化过滤器

        Args:
            min_volume: 最小成交量（手）
            min_open_interest: 最小持仓量（手）
            max_bid_ask_spread_pct: 最大买卖价差百分比（默认 20%）
        """
        self.min_volume = min_volume
        self.min_open_interest = min_open_interest
        self.max_bid_ask_spread_pct = max_bid_ask_spread_pct

    def filter(self, option: OptionData) -> Tuple[bool, str]:
        """
        检查期权是否通过流动性过滤

        Args:
            option: 期权数据

        Returns:
            (是否通过, 原因)
        """
        # 检查 1：成交量
        if option.volume < self.min_volume:
            return False, f"成交量过低: {option.volume} < {self.min_volume}"

        # 检查 2：持仓量
        if option.open_interest < self.min_open_interest:
            return False, f"持仓量过低: {option.open_interest} < {self.min_open_interest}"

        # 检查 3：买卖价差
        if option.ask > 0:
            spread_pct = (option.ask - option.bid) / option.ask
            if spread_pct > self.max_bid_ask_spread_pct:
                return False, f"买卖价差过大: {spread_pct*100:.1f}% > {self.max_bid_ask_spread_pct*100:.1f}%"

        return True, "通过流动性检查"


class InterestRateProvider:
    """
    过滤器 2：无风险利率切换

    根据期货币种选择对应的无风险利率：
    - USD: 美元利率（美国国债收益率）
    - CNY: 人民币利率（Shibor 或 LPR）
    """

    # 默认利率（需要定期更新）
    DEFAULT_RATES = {
        CurrencyType.USD: 0.045,  # 4.5%（美国国债收益率）
        CurrencyType.CNY: 0.020,  # 2.0%（Shibor）
    }

    def __init__(self, custom_rates: Optional[Dict[CurrencyType, float]] = None):
        """
        初始化利率提供器

        Args:
            custom_rates: 自定义利率（覆盖默认值）
        """
        self.rates = self.DEFAULT_RATES.copy()
        if custom_rates:
            self.rates.update(custom_rates)

    def get_rate(self, currency: CurrencyType) -> float:
        """获取指定货币的无风险利率"""
        return self.rates.get(currency, 0.03)  # 默认 3%


class IVPredictileCalculator:
    """
    过滤器 3：IV Rank & IV Percentile（IV 相对位置）

    **关键概念**：不要用 IV 绝对值来判断高低，要用历史分位数！

    IV Rank 衡量当前 IV 在过去一年最低点和最高点之间的位置：
    - IVR = 0：当前是过去一年波动率最低的时候（死水一潭）
    - IVR = 100：当前是过去一年波动率最高的时候（极度恐慌/狂热）

    IV Percentile 统计过去一年中，有多少天的 IV 低于今天的 IV：
    - 能剔除极端的"黑天鹅"尖峰对数据的扭曲
    - 更加科学，更适合程序报警

    示例：
    - 过去一年白银 IV 在 [15%, 45%] 波动
    - 当前 IV = 30%
    - IV Rank = (30 - 15) / (45 - 15) = 50%
    - IV Percentile 可能 = 55%（因为有几天极端值）
    """

    def __init__(self, lookback_days: int = 252):
        """
        初始化计算器

        Args:
            lookback_days: 回溯天数（默认 252 天 = 1 个交易日年）
        """
        self.lookback_days = lookback_days
        self.iv_history: Dict[str, List[Tuple[datetime, float]]] = {}  # symbol -> [(date, iv), ...]

    def add_observation(self, symbol: str, iv: float, timestamp: Optional[datetime] = None):
        """添加一个新的 IV 观测值"""
        if timestamp is None:
            timestamp = datetime.now()

        if symbol not in self.iv_history:
            self.iv_history[symbol] = []

        self.iv_history[symbol].append((timestamp, iv))

        # 限制历史长度
        max_length = self.lookback_days * 3  # 保留 3 倍长度的数据
        if len(self.iv_history[symbol]) > max_length:
            self.iv_history[symbol] = self.iv_history[symbol][-max_length:]

    def calculate_metrics(self, symbol: str, current_iv: float) -> Dict[str, float]:
        """
        计算 IV Rank 和 IV Percentile

        Args:
            symbol: 商品代码
            current_iv: 当前隐含波动率（小数形式，如 0.25）

        Returns:
            {
                'iv_rank': float,      # 0-100
                'iv_percentile': float, # 0-100
                '1y_high': float,      # 过去一年最高 IV
                '1y_low': float,       # 过去一年最低 IV
                'sample_size': int     # 样本数量
            }
        """
        if symbol not in self.iv_history:
            logger.warning(f"商品 {symbol} 没有 IV 历史数据")
            return {
                'iv_rank': 50.0,
                'iv_percentile': 50.0,
                '1y_high': current_iv,
                '1y_low': current_iv,
                'sample_size': 0
            }

        # 提取历史 IV 值
        history = self.iv_history[symbol][-self.lookback_days:]
        iv_values = [iv for _, iv in history]

        if len(iv_values) < 50:  # 至少 50 个观测值
            logger.warning(f"商品 {symbol} 历史数据不足: {len(iv_values)} < 50")
            return {
                'iv_rank': 50.0,
                'iv_percentile': 50.0,
                '1y_high': current_iv,
                '1y_low': current_iv,
                'sample_size': len(iv_values)
            }

        # 计算 IV Rank（绝对位置）
        iv_min = min(iv_values)
        iv_max = max(iv_values)

        if iv_max - iv_min < 1e-6:  # 波动率几乎不变
            iv_rank = 50.0
        else:
            iv_rank = (current_iv - iv_min) / (iv_max - iv_min) * 100

        # 计算 IV Percentile（相对排位）
        # 统计有多少天的 IV <= 当前 IV
        percentile = sum(1 for iv in iv_values if iv <= current_iv) / len(iv_values) * 100

        return {
            'iv_rank': round(iv_rank, 2),
            'iv_percentile': round(percentile, 2),
            '1y_high': iv_max,
            '1y_low': iv_min,
            'sample_size': len(iv_values)
        }

    def save_history(self, filepath: str):
        """保存历史数据到文件"""
        data = {}
        for symbol, history in self.iv_history.items():
            data[symbol] = [
                {'date': dt.isoformat(), 'iv': iv}
                for dt, iv in history
            ]

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"IV 历史数据已保存到: {filepath}")

    def load_history(self, filepath: str):
        """从文件加载历史数据"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for symbol, records in data.items():
                for record in records:
                    dt = datetime.fromisoformat(record['date'])
                    iv = record['iv']
                    self.iv_history.setdefault(symbol, []).append((dt, iv))

            logger.info(f"IV 历史数据已从 {filepath} 加载，商品数: {len(data)}")

        except Exception as e:
            logger.error(f"加载 IV 历史数据失败: {e}")


# ==========================================
# 5. VIX 指数计算器（方差互换算法）
# ==========================================

class VIXCalculator:
    """
    VIX 指数计算器（方差互换算法）

    CBOE VIX 的核心思想：不依赖期权定价模型（如 Black-Scholes），
    而是直接利用期权价格的加权平均来计算方差互换率。

    简化公式：
    VIX² = (2/T) * Σ [ΔK_i / K_i² * e^(RT) * Q(K_i)]

    简化实现：使用虚值期权的加权平均 IV
    """

    def calculate(
        self,
        options: List[OptionData],
        futures: FuturesData,
        iv_results: Dict[str, ImpliedVolatilityResult],
        risk_free_rate: float
    ) -> VIXResult:
        """
        计算 VIX 指数

        Args:
            options: 期权链列表
            futures: 期货数据
            iv_results: IV 计算结果字典 {symbol: result}
            risk_free_rate: 无风险利率

        Returns:
            VIXResult VIX 指数结果
        """
        if not options:
            raise ValueError("期权列表为空，无法计算 VIX")

        # 分类期权
        otm_calls = []  # 虚值看涨期权（K > F）
        otm_puts = []   # 虚值看跌期权（K < F）

        for opt in options:
            if opt.symbol not in iv_results:
                continue

            iv_result = iv_results[opt.symbol]
            if not iv_result.converged:
                continue

            # 判断是否为虚值期权
            if opt.option_type == OptionType.CALL and opt.strike > futures.price:
                otm_calls.append((opt, iv_result))
            elif opt.option_type == OptionType.PUT and opt.strike < futures.price:
                otm_puts.append((opt, iv_result))

        if not otm_calls and not otm_puts:
            raise ValueError("没有可用的虚值期权")

        # 计算加权平均 IV（使用期权价格作为权重）
        total_weight = 0.0
        weighted_iv = 0.0
        call_contribution = 0.0
        put_contribution = 0.0

        # 看涨期权贡献
        for opt, iv_result in otm_calls:
            weight = opt.market_price
            weighted_iv += iv_result.iv * weight
            total_weight += weight
            call_contribution += iv_result.iv * weight

        # 看跌期权贡献
        for opt, iv_result in otm_puts:
            weight = opt.market_price
            weighted_iv += iv_result.iv * weight
            total_weight += weight
            put_contribution += iv_result.iv * weight

        # 计算 VIX
        if total_weight > 0:
            vix_iv = weighted_iv / total_weight
            vix = vix_iv * np.sqrt(252) * 100  # 年化并转为百分比
        else:
            # 备选方案：简单平均
            all_ivs = [iv_result.iv for _, iv_result in otm_calls + otm_puts]
            vix_iv = np.mean(all_ivs)
            vix = vix_iv * np.sqrt(252) * 100

        return VIXResult(
            symbol=futures.symbol,
            vix=vix,
            call_contribution=call_contribution / total_weight if total_weight > 0 else 0,
            put_contribution=put_contribution / total_weight if total_weight > 0 else 0,
            total_options=len(otm_calls) + len(otm_puts),
            calculation_time=datetime.now()
        )


# ==========================================
# 6. 多商品配置系统
# ==========================================

@dataclass
class CommodityConfig:
    """商品配置"""
    symbol: str                    # 商品代码
    name: str                      # 商品名称
    category: CommodityCategory    # 商品类别
    currency: CurrencyType         # 货币类型
    high_iv_threshold: float       # 高 IV 阈值（小数形式）
    extreme_iv_threshold: float    # 极端 IV 阈值
    ignore_months: List[int] = field(default_factory=list)  # 排除月份（如农产品的天气炒作期）


# 默认商品配置
DEFAULT_COMMODITY_CONFIGS = {
    # 贵金属
    "SLV": CommodityConfig(
        symbol="SLV",
        name="白银",
        category=CommodityCategory.PRECIOUS_METAL,
        currency=CurrencyType.USD,
        high_iv_threshold=0.40,   # 40%
        extreme_iv_threshold=0.60  # 60%
    ),
    "GC": CommodityConfig(
        symbol="GC",
        name="黄金",
        category=CommodityCategory.PRECIOUS_METAL,
        currency=CurrencyType.USD,
        high_iv_threshold=0.25,   # 黄金相对稳定
        extreme_iv_threshold=0.40
    ),

    # 能源化工
    "CL": CommodityConfig(
        symbol="CL",
        name="原油",
        category=CommodityCategory.ENERGY,
        currency=CurrencyType.USD,
        high_iv_threshold=0.50,   # 原油波动大
        extreme_iv_threshold=0.80
    ),
    "SC": CommodityConfig(
        symbol="SC",
        name="上海原油",
        category=CommodityCategory.ENERGY,
        currency=CurrencyType.CNY,
        high_iv_threshold=0.45,
        extreme_iv_threshold=0.70
    ),

    # 农产品
    "S": CommodityConfig(
        symbol="S",
        name="大豆",
        category=CommodityCategory.AGRICULTURE,
        currency=CurrencyType.USD,
        high_iv_threshold=0.25,   # 农产品波动较小
        extreme_iv_threshold=0.40,
        ignore_months=[7, 8]     # 7-8月是天气炒作期，阈值需调整
    ),
    "SR": CommodityConfig(
        symbol="SR",
        name="白糖",
        category=CommodityCategory.AGRICULTURE,
        currency=CurrencyType.CNY,
        high_iv_threshold=0.20,
        extreme_iv_threshold=0.35
    ),

    # 黑色系
    "I": CommodityConfig(
        symbol="I",
        name="铁矿石",
        category=CommodityCategory.FERROUS,
        currency=CurrencyType.CNY,
        high_iv_threshold=0.50,   # 铁矿石波动极大
        extreme_iv_threshold=0.90
    ),
    "RB": CommodityConfig(
        symbol="RB",
        name="螺纹钢",
        category=CommodityCategory.FERROUS,
        currency=CurrencyType.CNY,
        high_iv_threshold=0.45,
        extreme_iv_threshold=0.80
    ),

    # 有色金属
    "HG": CommodityConfig(
        symbol="HG",
        name="铜",
        category=CommodityCategory.NON_FERROUS,
        currency=CurrencyType.USD,
        high_iv_threshold=0.35,
        extreme_iv_threshold=0.55
    ),
}


# ==========================================
# 7. 智能报警系统（基于 IV Percentile）
# ==========================================

class IVAlertSystem:
    """
    IV 智能报警系统

    使用 IV Percentile 实现统一的报警逻辑，不需要为每个品种单独设绝对值。

    通用校准表（适用于所有商品）：
    - 0-20: 低波动（沉睡）
    - 20-50: 正常
    - 50-80: 升温（低级警报）
    - 80-95: 高波动（高级警报）
    - 95-100: 极值（红色警报）
    """

    @staticmethod
    def get_alert_level(iv_percentile: float) -> Tuple[str, str]:
        """
        根据 IV Percentile 获取报警级别

        Args:
            iv_percentile: IV 百分位 (0-100)

        Returns:
            (级别, 描述, 操作建议)
        """
        if iv_percentile >= 95:
            return "🚨 极值", "过去一年最疯狂的几天", "第一性原理买点：IV 回归均值的最佳时刻"
        elif iv_percentile >= 80:
            return "🔥 高波动", "重大事件前夕或恐慌", "期权极贵：适合做卖方(Sell Put)，或准备抄底现货"
        elif iv_percentile >= 50:
            return "⚠️ 升温", "趋势开始形成或小恐慌", "关注趋势突破"
        elif iv_percentile >= 20:
            return "✅ 正常", "日常震荡", "按技术面交易"
        else:
            return "💤 低波动", "市场没人玩或极度自满", "期权便宜：适合买入期权(Long Gamma)做埋伏"

    @staticmethod
    def should_alert(iv_percentile: float, threshold: float = 80) -> bool:
        """
        判断是否应该触发警报

        Args:
            iv_percentile: IV 百分位
            threshold: 警报阈值（默认 80）

        Returns:
            是否应该警报
        """
        return iv_percentile >= threshold


# ==========================================
# 8. 综合服务类
# ==========================================

class VolatilityIndexService:
    """
    波动率指数服务（综合入口）

    整合所有功能：IV 计算、VIX 计算、过滤器、多商品配置、智能报警
    """

    def __init__(
        self,
        commodity_configs: Optional[Dict[str, CommodityConfig]] = None,
        enable_liquidity_filter: bool = True,
        enable_iv_percentile: bool = True,
        iv_history_file: str = "./data/iv_history.json"
    ):
        """
        初始化服务

        Args:
            commodity_configs: 商品配置字典（默认使用 DEFAULT_COMMODITY_CONFIGS）
            enable_liquidity_filter: 是否启用流动性过滤
            enable_iv_percentile: 是否启用 IV Percentile 计算
            iv_history_file: IV 历史数据文件路径
        """
        self.commodity_configs = commodity_configs or DEFAULT_COMMODITY_CONFIGS
        self.iv_calculator = ImpliedVolatilityCalculator()
        self.vix_calculator = VIXCalculator()
        self.rate_provider = InterestRateProvider()
        self.alert_system = IVAlertSystem()

        # IV Percentile 计算器
        self.iv_percentile_calc = IVPredictileCalculator() if enable_iv_percentile else None

        # 加载历史数据
        if self.iv_percentile_calc and iv_history_file:
            try:
                self.iv_percentile_calc.load_history(iv_history_file)
            except Exception as e:
                logger.info(f"未找到 IV 历史数据文件，将创建新文件: {e}")

        # 可选过滤器
        self.liquidity_filter = LiquidityFilter() if enable_liquidity_filter else None

        self.iv_history_file = iv_history_file

        logger.info("波动率指数服务初始化完成")
        logger.info(f"支持的商品: {list(self.commodity_configs.keys())}")

    def calculate_single_iv(
        self,
        option: OptionData,
        futures: FuturesData,
        symbol: Optional[str] = None
    ) -> ImpliedVolatilityResult:
        """
        计算单个期权的隐含波动率

        Args:
            option: 期权数据
            futures: 期货数据
            symbol: 商品代码（用于获取配置）

        Returns:
            ImpliedVolatilityResult
        """
        # 获取配置
        config = self.commodity_configs.get(symbol) if symbol else None

        # 流动性过滤
        if self.liquidity_filter:
            passed, reason = self.liquidity_filter.filter(option)
            if not passed:
                logger.warning(f"[{option.symbol}] 流动性过滤失败: {reason}")
                # 仍然计算，但记录警告

        # 获取无风险利率
        currency = config.currency if config else futures.currency
        risk_free_rate = self.rate_provider.get_rate(currency)

        # 计算 IV
        result = self.iv_calculator.calculate(option, futures, risk_free_rate)

        # 保存到 IV Percentile 历史
        if self.iv_percentile_calc and symbol:
            self.iv_percentile_calc.add_observation(symbol, result.iv)

        logger.info(
            f"[{option.symbol}] IV = {result.iv*100:.2f}% "
            f"(迭代{result.iterations}次, 收敛={result.converged})"
        )

        return result

    def calculate_vix_index(
        self,
        options: List[OptionData],
        futures: FuturesData,
        symbol: str
    ) -> VIXResult:
        """
        计算 VIX 指数

        Args:
            options: 期权链列表
            futures: 期货数据
            symbol: 商品代码

        Returns:
            VIXResult
        """
        logger.info(f"[{symbol}] 开始计算 VIX 指数，期权数量: {len(options)}")

        # 获取配置
        config = self.commodity_configs.get(symbol)
        if not config:
            logger.warning(f"未找到商品 {symbol} 的配置，使用默认参数")

        # 获取无风险利率
        currency = config.currency if config else futures.currency
        risk_free_rate = self.rate_provider.get_rate(currency)

        # 计算所有期权的 IV
        iv_results = {}
        for option in options:
            try:
                result = self.calculate_single_iv(option, futures, symbol)
                iv_results[option.symbol] = result
            except Exception as e:
                logger.error(f"[{option.symbol}] IV 计算失败: {e}")

        logger.info(f"[{symbol}] 成功计算 {len(iv_results)}/{len(options)} 个期权的 IV")

        # 计算 VIX
        vix_result = self.vix_calculator.calculate(options, futures, iv_results, risk_free_rate)

        # 计算 IV Rank 和 IV Percentile（如果启用）
        if self.iv_percentile_calc:
            vix_iv = vix_result.vix / 100 / np.sqrt(252)  # 转回小数形式
            metrics = self.iv_percentile_calc.calculate_metrics(symbol, vix_iv)
            vix_result.iv_rank = metrics['iv_rank']
            vix_result.iv_percentile = metrics['iv_percentile']

        # 解读 VIX 水平
        if config:
            interpretation = self._interpret_vix(vix_result, config)
            logger.info(f"[{symbol}] VIX = {vix_result.vix:.2f} - {interpretation}")

        return vix_result

    def _interpret_vix(self, vix_result: VIXResult, config: CommodityConfig) -> str:
        """解读 VIX 水平（结合 IV Percentile）"""
        if vix_result.iv_percentile is not None:
            # 使用 IV Percentile（更科学）
            level, status, advice = self.alert_system.get_alert_level(vix_result.iv_percentile)
            return f"{level} (IV Percentile: {vix_result.iv_percentile:.0f}%) - {status} - {advice}"
        else:
            # 降级使用绝对值
            if vix_result.vix > config.extreme_iv_threshold * 100:
                return f"极度恐慌 (VIX > {config.extreme_iv_threshold*100:.0f}%)"
            elif vix_result.vix > config.high_iv_threshold * 100:
                return f"恐慌 (VIX > {config.high_iv_threshold*100:.0f}%)"
            elif vix_result.vix < 12:
                return "极度贪婪 (VIX < 12%)"
            else:
                return "正常波动"

    def get_signal(self, symbol: str, vix_result: VIXResult) -> str:
        """
        根据 VIX 生成交易信号建议

        Args:
            symbol: 商品代码
            vix_result: VIX 计算结果

        Returns:
            信号建议
        """
        config = self.commodity_configs.get(symbol)
        if not config:
            return "未知商品，无法生成信号"

        # 使用 IV Percentile（如果可用）
        if vix_result.iv_percentile is not None:
            level, status, advice = self.alert_system.get_alert_level(vix_result.iv_percentile)
            return f"{level} - {advice} (IV Percentile: {vix_result.iv_percentile:.0f}%)"

        # 降级使用绝对值
        vix = vix_result.vix
        iv_rank = vix_result.iv_rank

        iv_rank_str = f"{iv_rank:.0f}" if iv_rank is not None else "N/A"

        if vix > config.extreme_iv_threshold * 100:
            return f"极度恐慌，考虑抄底（IV Rank: {iv_rank_str}）"
        elif vix > config.high_iv_threshold * 100:
            return f"恐慌，谨慎观望（IV Rank: {iv_rank_str}）"
        elif vix < 12:
            return f"极度贪婪，警惕风险（IV Rank: {iv_rank_str}）"
        else:
            return f"正常波动，按技术面交易（IV Rank: {iv_rank_str}）"

    def save_iv_history(self):
        """保存 IV 历史数据"""
        if self.iv_percentile_calc and self.iv_history_file:
            self.iv_percentile_calc.save_history(self.iv_history_file)

    def should_alert(self, symbol: str, vix_result: VIXResult, threshold: float = 80) -> bool:
        """
        判断是否应该触发警报

        Args:
            symbol: 商品代码
            vix_result: VIX 计算结果
            threshold: IV Percentile 阈值（默认 80）

        Returns:
            是否应该警报
        """
        if vix_result.iv_percentile is None:
            return False

        return self.alert_system.should_alert(vix_result.iv_percentile, threshold)


# ==========================================
# 9. 便捷函数
# ==========================================

_volatility_service: Optional[VolatilityIndexService] = None

def get_volatility_service() -> VolatilityIndexService:
    """获取波动率指数服务单例"""
    global _volatility_service
    if _volatility_service is None:
        _volatility_service = VolatilityIndexService()
    return _volatility_service


# ==========================================
# 10. 测试代码
# ==========================================

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
    )

    print("=" * 70)
    print("期货期权隐含波动率与 VIX 指数计算测试（完整版）")
    print("=" * 70)

    # 创建服务
    service = get_volatility_service()

    # 测试用例：白银期权
    print("\n[测试 1] 白银期权 IV 计算")
    print("-" * 70)

    # 模拟期权数据
    option_data = OptionData(
        symbol="AG2406-C-5000",
        option_type=OptionType.CALL,
        strike=5000,
        market_price=150,
        bid=145,
        ask=155,
        volume=1000,
        open_interest=5000,
        expiry_date=datetime.now() + timedelta(days=30)
    )

    futures_data = FuturesData(
        symbol="AG2406",
        price=4900,
        currency=CurrencyType.CNY
    )

    # 计算 IV
    result = service.calculate_single_iv(option_data, futures_data, "SLV")

    print(f"期权代码: {result.symbol}")
    print(f"隐含波动率: {result.iv*100:.2f}%")
    print(f"理论价格: {result.theoretical_price:.2f}")
    print(f"市场价格: {option_data.market_price:.2f}")
    print(f"误差: {result.error:.4f}")
    print(f"Vega: {result.vega:.4f}")
    print(f"迭代次数: {result.iterations}")
    print(f"是否收敛: {result.converged}")

    # 测试 VIX 计算（需要期权链）
    print("\n[测试 2] VIX 指数计算")
    print("-" * 70)

    # 模拟期权链（多个行权价）
    option_chain = []
    base_strike = 4800
    for i in range(10):
        strike = base_strike + i * 50
        # 看涨期权
        option_chain.append(OptionData(
            symbol=f"AG2406-C-{strike}",
            option_type=OptionType.CALL,
            strike=strike,
            market_price=max(50, 4900 - strike + 100),
            bid=0,
            ask=0,
            volume=1000,
            open_interest=5000,
            expiry_date=datetime.now() + timedelta(days=30)
        ))
        # 看跌期权
        option_chain.append(OptionData(
            symbol=f"AG2406-P-{strike}",
            option_type=OptionType.PUT,
            strike=strike,
            market_price=max(50, strike - 4900 + 100),
            bid=0,
            ask=0,
            volume=1000,
            open_interest=5000,
            expiry_date=datetime.now() + timedelta(days=30)
        ))

    try:
        vix_result = service.calculate_vix_index(option_chain, futures_data, "SLV")
        print(f"商品: {vix_result.symbol}")
        print(f"VIX 指数: {vix_result.vix:.2f}")
        print(f"看涨贡献: {vix_result.call_contribution*100:.2f}%")
        print(f"看跌贡献: {vix_result.put_contribution*100:.2f}%")
        print(f"期权数量: {vix_result.total_options}")
        print(f"IV Rank: {vix_result.iv_rank:.1f}%" if vix_result.iv_rank else "IV Rank: N/A")
        print(f"IV Percentile: {vix_result.iv_percentile:.1f}%" if vix_result.iv_percentile else "IV Percentile: N/A")

        signal = service.get_signal("SLV", vix_result)
        print(f"\n交易信号: {signal}")

        # 测试智能报警
        should_alert = service.should_alert("SLV", vix_result, threshold=80)
        print(f"是否触发警报: {should_alert}")

    except Exception as e:
        print(f"VIX 计算失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
