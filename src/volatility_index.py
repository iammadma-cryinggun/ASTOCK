# -*- coding: utf-8 -*-
"""
===================================
波动率指数数据获取模块
===================================

职责：
1. 获取真实的波动率指数（VIX、GVZ、OVX 等）
2. 这些指数本身就是市场预期的波动率，可以直接作为 IV 使用
3. 避免使用不准确的"简化估算"

数据源：
- Yahoo Finance（免费，可靠）
- AkShare（部分指数）

支持的指数：
- VIX: 标普500波动率指数
- GVZ: CBOE黄金波动率指数（白银ETN）
- OVX: CBOE原油波动率指数
- VXEEM: 新兴市场波动率指数
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

logger = logging.getLogger(__name__)


class VolatilityIndexFetcher:
    """
    波动率指数获取器

    获取真实的波动率指数，这些指数反映了市场预期的波动率
    可以直接作为 IV 使用，而不需要从期权链估算
    """

    # 指数代码映射
    INDICES = {
        # 波动率指数（本身就是 IV）
        '^VIX': 'VIX',           # 标普500波动率指数（恐慌指数）
        '^GVZ': 'GVZ',         # CBOE黄金波动率指数
        '^OVX': 'OVX',         # CBOE原油波动率指数
        '^VXEEM': 'VXEEM',     # 新兴市场波动率指数
        '^VVIX': 'VVIX',       # VIX波动率（波动率的波动率）

        # 商品相关 ETF 的代理指数
        'GLD': 'GVZ',          # 黄金 → 使用 GVZ
        'SLV': 'GVZ',          # 白银 → 使用 GVZ
        'USO': 'OVX',          # 原油 → 使用 OVX
        'IAU': 'GVZ',          # 黄金 → 使用 GVZ
    }

    # API 端点
    YAHOO_FINANCE_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"

    def __init__(self):
        """初始化获取器"""
        self._cache: Dict[str, Dict] = {}
        self._cache_ttl = timedelta(minutes=15)  # 缓存15分钟

    def get_volatility_index(self, symbol: str) -> Optional[float]:
        """
        获取波动率指数的当前值

        Args:
            symbol: 指数代码（如 ^VIX）或 ETF 代码（如 GLD）

        Returns:
            波动率指数的值（百分比）
        """
        # 检查缓存
        if symbol in self._cache:
            cache_data = self._cache[symbol]
            if datetime.now() - cache_data['time'] < self._cache_ttl:
                return cache_data['value']

        # 确定要查询的指数代码
        if symbol in self.INDICES and symbol.startswith('^'):
            # 直接是指数代码
            index_symbol = symbol
        elif symbol in self.INDICES:
            # ETF 代码，映射到对应的指数
            index_symbol = '^' + self.INDICES[symbol]
        else:
            logger.warning(f"未知的指数/ETF代码: {symbol}")
            return None

        try:
            # 从 Yahoo Finance 获取数据
            value = self._fetch_from_yahoo(index_symbol)

            if value is not None:
                # 缓存结果
                self._cache[symbol] = {
                    'value': value,
                    'time': datetime.now()
                }

                logger.debug(f"获取 {symbol} 的波动率指数: {value:.2f}%")
                return value

        except Exception as e:
            logger.error(f"获取 {symbol} 波动率指数失败: {e}")

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
            # Yahoo Finance API
            url = f"{self.YAHOO_FINANCE_BASE_URL}/{symbol}"

            params = {
                'interval': '1d',
                'range': '1d',  # 只需要最新数据
                'includePrePost': 'false'
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 解析响应
            if 'result' in data and len(data['result']) > 0:
                result = data['result'][0]
                if 'indicators' in result and 'quote' in result['indicators']:
                    quote = result['indicators']['quote'][0]
                    if 'close' in quote and len(quote['close']) > 0:
                        # 获取最新收盘价
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
        if symbol in self.INDICES and symbol.startswith('^'):
            index_symbol = symbol
        elif symbol in self.INDICES:
            index_symbol = '^' + self.INDICES[symbol]
        else:
            return []

        try:
            url = f"{self.YAHOO_FINANCE_BASE_URL}/{index_symbol}"

            params = {
                'interval': '1d',
                'range': f'{days}d',
                'includePrePost': 'false'
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
                                # 转换时间戳为日期
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


# 便捷函数
_volatility_fetcher: Optional[VolatilityIndexFetcher] = None

def get_volatility_fetcher() -> VolatilityIndexFetcher:
    """获取波动率获取器单例"""
    global _volatility_fetcher
    if _volatility_fetcher is None:
        _volatility_fetcher = VolatilityIndexFetcher()
    return _volatility_fetcher
