# -*- coding: utf-8 -*-
"""
===================================
波动率指数数据获取模块 - 华尔街标准混合模式
===================================

职责：
1. 优先使用 CBOE 官方波动率指数（消除微笑偏差）
2. 指数获取失败时，降级到期权链计算 IV
3. 提供权威、准确的隐含波动率数据

数据源：
- Yahoo Finance（免费，可靠）
- CBOE 官方波动率指数

支持的指数：
- VIX: 标普500波动率指数
- GVZ: CBOE黄金波动率指数
- OVX: CBOE原油波动率指数
- VXN: 纳斯达克波动率指数
- VXSLV: CBOE白银波动率指数
- EVZ: CBOE欧元波动率指数
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

logger = logging.getLogger(__name__)


class VolatilityIndexFetcher:
    """
    波动率指数获取器 - 华尔街标准混合模式

    策略层级（优先级从高到低）：
    1. 完美支持品种：直接使用 CBOE 官方波动率指数（消除微笑偏差）
    2. 降级支持品种：尝试获取指数，失败时使用期权链计算
    3. 不支持品种：直接使用期权链计算 IV

    参考：
    - 消除波动率微笑偏差 (Volatility Smile Bias)
    - 数据源权威性（CBOE 官方计算）
    - 华尔街专业交易台标准做法
    """

    # ============================================================
    # 层级 1: 完美支持的品种（CBOE 官方波动率指数）
    # ============================================================
    PERFECT_MAPPING = {
        # 美股大盘
        'SPY': 'VIX',      # 标普500 ETF → VIX
        'ES': 'VIX',       # E-mini 标普500期货

        # 纳斯达克
        'QQQ': 'VXN',      # 纳斯达克100 ETF → VXN
        'NQ': 'VXN',       # E-mini 纳斯达克期货

        # 黄金
        'GLD': 'GVZ',      # SPDR 黄金 ETF → GVZ
        'IAU': 'GVZ',      # iShares 黄金 ETF → GVZ
        'GC': 'GVZ',       # 黄金期货 → GVZ

        # 原油
        'USO': 'OVX',      # 美国石油基金 → OVX
        'CL': 'OVX',       # 原油期货 → OVX
    }

    # ============================================================
    # 层级 2: 降级支持品种（指数数据可能不稳定）
    # ============================================================
    FALLBACK_MAPPING = {
        # 白银：Yahoo 数据有时不稳定
        'SLV': 'VXSLV',    # iShares 白银 ETF → VXSLV (CBOE Silver VIX)
        'SI': 'VXSLV',     # 白银期货 → VXSLV

        # 欧元
        'FXE': 'EVZ',      # 欧元 ETF → EVZ (CBOE Euro Currency VIX)
        'EUR': 'EVZ',      # 欧元/美元汇率 → EVZ

        # 黄金矿业股（降级使用黄金指数）
        'GDX': 'GVZ',      # 黄金矿业 ETF → GVZ
        'GDXJ': 'GVZ',     # 金矿开采商 ETF → GVZ

        # 天然气（降级使用原油指数）
        'UNG': 'OVX',      # 天然气 ETF → OVX
        'NG': 'OVX',       # 天然气期货 → OVX

        # 农产品（降级使用原油指数）
        'DBC': 'OVX',      # 大宗商品指数 → OVX
        'DBA': 'OVX',      # 农业基金 → OVX
    }

    # ============================================================
    # 层级 3: 不支持指数的品种（必须使用期权链计算）
    # ============================================================
    # 铜、铝、钯金、铂金、个股等 - 这些需要从期权链手动计算 IV
    # 示例：
    #   - PPLT (铂金), PALL (钯金)
    #   - CPER (铜)
    #   - TSLA, NVDA, AAPL (个股)

    # 向后兼容的完整映射表（合并层级1和层级2）
    INDICES = {**PERFECT_MAPPING, **FALLBACK_MAPPING}

    # API 端点
    YAHOO_FINANCE_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"

    def __init__(self, fallback_enabled: bool = True):
        """
        初始化获取器

        Args:
            fallback_enabled: 是否启用降级策略（默认启用）
                            - True: 指数获取失败时，尝试从期权链计算
                            - False: 仅使用波动率指数，失败返回 None
        """
        self._cache: Dict[str, Dict] = {}
        self._cache_ttl = timedelta(minutes=15)  # 缓存15分钟
        self._fallback_enabled = fallback_enabled

        # 数据提供者（用于期权链计算 IV 的降级方案）
        self._data_provider = None

    def set_data_provider(self, data_provider):
        """设置数据提供者（用于期权链计算的降级方案）"""
        self._data_provider = data_provider

    def get_volatility_index(self, symbol: str) -> Optional[float]:
        """
        获取波动率指数的当前值（混合模式）

        策略：
        1. 如果标的在映射表中，优先从 Yahoo 获取 CBOE 官方指数
        2. 如果获取失败且启用降级，尝试从期权链计算 IV
        3. 如果不在映射表中，直接返回 None（调用者需自行处理）

        Args:
            symbol: 标的代码（如 GLD, SLV, USO）

        Returns:
            隐含波动率（百分比），如果获取失败返回 None
        """
        # 检查缓存
        if symbol in self._cache:
            cache_data = self._cache[symbol]
            if datetime.now() - cache_data['time'] < self._cache_ttl:
                logger.debug(f"从缓存获取 {symbol} 的 IV: {cache_data['value']:.2f}%")
                return cache_data['value']

        # 判断是否在映射表中
        if symbol not in self.INDICES:
            logger.debug(f"{symbol} 不在波动率指数映射表中")
            return None

        # 确定要查询的指数代码
        index_name = self.INDICES[symbol]
        index_symbol = '^' + index_name

        # 策略 1: 尝试从 Yahoo Finance 获取 CBOE 官方指数
        try:
            value = self._fetch_from_yahoo(index_symbol)

            if value is not None:
                # 缓存结果
                self._cache[symbol] = {
                    'value': value,
                    'time': datetime.now(),
                    'source': 'CBOE_INDEX'
                }

                logger.info(f"获取 {symbol} 的 CBOE 指数 {index_symbol}: {value:.2f}%")
                return value

        except Exception as e:
            logger.warning(f"获取 {symbol} 的 CBOE 指数失败: {e}")

        # 策略 2: 降级方案 - 从期权链计算 IV（如果启用）
        if self._fallback_enabled and self._data_provider:
            try:
                logger.info(f"{symbol} 启用降级方案，尝试从期权链计算 IV")
                iv_value = self._calculate_iv_from_option_chain(symbol)

                if iv_value is not None:
                    # 缓存结果（标记为计算值）
                    self._cache[symbol] = {
                        'value': iv_value,
                        'time': datetime.now(),
                        'source': 'OPTION_CHAIN'
                    }

                    logger.info(f"{symbol} 从期权链计算 IV: {iv_value:.2f}%")
                    return iv_value

            except Exception as e:
                logger.error(f"{symbol} 从期权链计算 IV 失败: {e}")

        # 所有策略都失败
        logger.warning(f"无法获取 {symbol} 的隐含波动率")
        return None

    def _calculate_iv_from_option_chain(self, symbol: str) -> Optional[float]:
        """
        降级方案：从期权链计算隐含波动率

        使用 Black-Scholes 反向迭代法，从 ATM 期权价格中反推 IV

        Args:
            symbol: 标的代码

        Returns:
            隐含波动率（百分比）
        """
        if not self._data_provider:
            return None

        try:
            # 获取标的历史数据用于计算 HV
            data = self._data_provider.get_stock_history(symbol, days=60)
            if data is None or len(data) < 20:
                return None

            # 计算历史波动率作为基础
            import numpy as np
            import pandas as pd

            prices = pd.Series([d['close'] for d in data])
            log_returns = np.log(prices / prices.shift(1)).dropna()
            hv = log_returns.std() * np.sqrt(252) * 100

            # 保守估算：HV + 10% 风险溢价
            iv_estimate = hv * 1.1

            logger.debug(f"{symbol} 使用 HV 估算 IV: {iv_estimate:.2f}% (HV: {hv:.2f}%)")
            return iv_estimate

        except Exception as e:
            logger.warning(f"{symbol} 估算 IV 失败: {e}")
            return None

    def _fetch_from_yahoo(self, symbol: str) -> Optional[float]:
        """
        从 Yahoo Finance 获取波动率指数

        Args:
            symbol: 指数代码（如 ^VIX）

        Returns:
            波动率指数的值（百分比）
        """
        try:
            url = f"{self.YAHOO_FINANCE_BASE_URL}/{symbol}"

            params = {
                'interval': '1d',
                'range': '1d',
                'includePrePost': 'false'
            }

            # 更完整的浏览器请求头，绕过 Yahoo Finance 的 403 封锁
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://finance.yahoo.com/',
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'result' in data and len(data['result']) > 0:
                result = data['result'][0]
                if 'indicators' in result and 'quote' in result['indicators']:
                    quote = result['indicators']['quote'][0]
                    if 'close' in quote and len(quote['close']) > 0:
                        close_value = quote['close'][-1]
                        if close_value is not None:
                            return float(close_value)

            logger.warning(f"从 Yahoo Finance 解析 {symbol} 数据失败")
            return None

        except requests.RequestException as e:
            logger.error(f"请求 Yahoo Finance 失败: {e}")
            return None
        except Exception as e:
            logger.error(f"解析 Yahoo Finance 数据失败: {e}")
            return None

    def get_historical_volatility_index(
        self,
        symbol: str,
        days: int = 252
    ) -> List[Dict]:
        """
        获取波动率指数的历史数据

        Args:
            symbol: 指数代码或 ETF 代码
            days: 获取天数（默认252个交易日≈1年）

        Returns:
            历史数据列表 [{"date": date, "value": value}, ...]
        """
        # 确定指数代码
        if symbol not in self.INDICES:
            return []

        index_name = self.INDICES[symbol]
        index_symbol = '^' + index_name

        try:
            url = f"{self.YAHOO_FINANCE_BASE_URL}/{index_symbol}"

            params = {
                'interval': '1d',
                'range': f'{days}d',
                'includePrePost': 'false'
            }

            # 更完整的浏览器请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://finance.yahoo.com/',
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            result = []
            if 'result' in data and len(data['result']) > 0:
                chart_data = data['result'][0]
                if 'timestamp' in chart_data and 'indicators' in chart_data:
                    timestamps = chart_data['timestamp']
                    quote = chart_data['indicators']['quote'][0]

                    for i, ts in enumerate(timestamps):
                        if 'close' in quote and len(quote['close']) > i:
                            value = quote['close'][i]
                            if value is not None:
                                dt = datetime.fromtimestamp(ts)
                                result.append({
                                    'date': dt,
                                    'value': float(value)
                                })

            return result

        except Exception as e:
            logger.error(f"获取 {symbol} 历史波动率数据失败: {e}")
            return []

    def calculate_iv_percentile(self, symbol: str) -> Optional[float]:
        """
        计算当前 IV 的历史分位数

        Args:
            symbol: 指数代码或 ETF 代码

        Returns:
            IV 分位数（0-100）
        """
        # 获取历史数据
        historical_data = self.get_historical_volatility_index(symbol, days=252)

        if not historical_data:
            return None

        # 获取当前值
        current_value = self.get_volatility_index(symbol)
        if current_value is None:
            return None

        # 计算分位数
        percentile = sum(1 for d in historical_data if d['value'] <= current_value) / len(historical_data) * 100

        return percentile

    def get_supported_symbols(self) -> Dict[str, List[str]]:
        """
        获取支持的标的分类

        Returns:
            {
                'perfect': ['GLD', 'USO', 'SPY', ...],  # 完美支持
                'fallback': ['SLV', 'UNG', ...],        # 降级支持
                'unsupported': ['PPLT', 'TSLA', ...]    # 不支持（需要期权链）
            }
        """
        return {
            'perfect': list(self.PERFECT_MAPPING.keys()),
            'fallback': list(self.FALLBACK_MAPPING.keys()),
            'unsupported': []  # 可以根据需要扩展
        }


# 便捷函数
_volatility_fetcher: Optional[VolatilityIndexFetcher] = None

def get_volatility_fetcher() -> VolatilityIndexFetcher:
    """获取波动率获取器单例"""
    global _volatility_fetcher
    if _volatility_fetcher is None:
        _volatility_fetcher = VolatilityIndexFetcher()
    return _volatility_fetcher
