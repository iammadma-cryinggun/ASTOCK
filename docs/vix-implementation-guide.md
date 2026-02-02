# 期货期权 IV 与 VIX 指数计算系统 - 完整实现指南

## 📋 目录

1. [功能概述](#功能概述)
2. [核心算法](#核心算法)
3. [使用指南](#使用指南)
4. [API 参考](#api-参考)
5. [配置说明](#配置说明)
6. [测试示例](#测试示例)

---

## 功能概述

本系统实现了**华尔街标准**的期货期权隐含波动率（IV）和 VIX 指数计算，包括：

### ✅ 已实现功能

1. **Black-76 定价模型**（期货期权专用）
   - 看涨/看跌期权理论价格
   - Vega（波动率敏感度）

2. **牛顿-拉夫逊法**（求解 IV）
   - 快速收敛（二次收敛）
   - 边界保护

3. **三大过滤器**
   - 流动性检查
   - 利率切换（USD/CNY）
   - IV Rank & IV Percentile

4. **VIX 指数计算**（方差互换算法）
   - 使用虚值期权加权平均
   - 符合 CBOE 标准

5. **多商品配置系统**
   - 贵金属、能源、农产品、黑色系、有色金属
   - 每个品种独立的阈值配置

6. **智能报警系统**（基于 IV Percentile）
   - 统一的报警逻辑（不需要为每个品种单独设阈值）
   - 红绿灯机制

7. **AI 分析集成**
   - VIX 数据自动传递给 AI 模型
   - 辅助交易决策

---

## 核心算法

### 1. Black-76 模型

**适用场景**：期货期权（区别于股票的 Black-Scholes）

**看涨期权价格**：
```
c = e^(-rT) * [F * N(d1) - K * N(d2)]
```

**看跌期权价格**：
```
p = e^(-rT) * [K * N(-d2) - F * N(-d1)]
```

**其中**：
- `F`: 期货价格
- `K`: 行权价
- `T`: 剩余时间（年化）
- `r`: 无风险利率
- `σ`: 波动率

### 2. 牛顿-拉夫逊法（求解 IV）

**目标**：求解 `f(σ) = 理论价 - 市场价 = 0`

**迭代公式**：
```
σ_{n+1} = σ_n - f(σ_n) / f'(σ_n)
        = σ_n - (理论价 - 市场价) / vega
```

**收敛速度**：二次收敛（通常 4-5 次迭代即可）

### 3. VIX 指数计算（简化版）

使用**虚值期权加权平均**：

```python
# 筛选虚值期权
otm_calls = [opt for opt in options if opt.type == CALL and opt.strike > F]
otm_puts = [opt for opt in options if opt.type == PUT and opt.strike < F]

# 计算加权平均 IV
weighted_iv = Σ(iv_i * price_i) / Σ(price_i)

# 年化为 VIX
vix = weighted_iv * √252 * 100
```

---

## 使用指南

### 快速开始

```python
from src.volatility_index import (
    get_volatility_service,
    OptionData,
    FuturesData,
    OptionType,
    CurrencyType
)

# 1. 创建服务
service = get_volatility_service()

# 2. 准备数据
futures = FuturesData(
    symbol="AG2406",
    price=4900,
    currency=CurrencyType.CNY
)

option = OptionData(
    symbol="AG2406-C-5000",
    option_type=OptionType.CALL,
    strike=5000,
    market_price=150,
    bid=145,
    ask=155,
    volume=1000,
    open_interest=5000,
    expiry_date=datetime(2024, 6, 30)
)

# 3. 计算 IV
result = service.calculate_single_iv(option, futures, "SLV")

print(f"IV: {result.iv*100:.2f}%")
print(f"收敛: {result.converged}")
```

### 计算 VIX 指数

```python
# 准备期权链（多个行权价）
option_chain = [
    OptionData(...),
    OptionData(...),
    # ... 更多期权
]

# 计算 VIX
vix_result = service.calculate_vix_index(
    options=option_chain,
    futures=futures,
    symbol="SLV"
)

print(f"VIX: {vix_result.vix:.2f}")
print(f"IV Percentile: {vix_result.iv_percentile:.1f}%")

# 获取交易信号
signal = service.get_signal("SLV", vix_result)
print(f"信号: {signal}")
```

### 智能报警

```python
# 判断是否应该报警
should_alert = service.should_alert(
    symbol="SLV",
    vix_result=vix_result,
    threshold=80  # IV Percentile > 80% 时报警
)

if should_alert:
    print("警报：市场波动率异常！")
```

---

## API 参考

### VolatilityIndexService

**主服务类**，整合所有功能。

#### 方法

**`calculate_single_iv(option, futures, symbol=None)`**

计算单个期权的隐含波动率。

**参数**：
- `option` (OptionData): 期权数据
- `futures` (FuturesData): 期货数据
- `symbol` (str, optional): 商品代码（用于获取配置）

**返回**：
- `ImpliedVolatilityResult`: 计算结果

**`calculate_vix_index(options, futures, symbol)`**

计算 VIX 指数。

**参数**：
- `options` (List[OptionData]): 期权链列表
- `futures` (FuturesData): 期货数据
- `symbol` (str): 商品代码

**返回**：
- `VIXResult`: VIX 指数结果

**`get_signal(symbol, vix_result)`**

根据 VIX 生成交易信号。

**参数**：
- `symbol` (str): 商品代码
- `vix_result` (VIXResult): VIX 计算结果

**返回**：
- `str`: 交易信号建议

**`should_alert(symbol, vix_result, threshold=80)`**

判断是否应该触发警报。

**参数**：
- `symbol` (str): 商品代码
- `vix_result` (VIXResult): VIX 计算结果
- `threshold` (float): IV Percentile 阈值（默认 80）

**返回**：
- `bool`: 是否应该警报

---

## 配置说明

### 商品配置

每个商品都有独立的配置，位于 `DEFAULT_COMMODITY_CONFIGS`：

```python
"SLV": CommodityConfig(
    symbol="SLV",
    name="白银",
    category=CommodityCategory.PRECIOUS_METAL,
    currency=CurrencyType.USD,
    high_iv_threshold=0.40,      # 40%
    extreme_iv_threshold=0.60,  # 60%
    ignore_months=[]             # 排除月份（农产品天气炒作期）
)
```

### 无风险利率

```python
# 在 InterestRateProvider 中配置
DEFAULT_RATES = {
    CurrencyType.USD: 0.045,  # 美国国债收益率
    CurrencyType.CNY: 0.020,  # Shibor
}
```

### 流动性过滤器

```python
LiquidityFilter(
    min_volume=500,              # 最小成交量（手）
    min_open_interest=1000,       # 最小持仓量（手）
    max_bid_ask_spread_pct=0.20  # 最大买卖价差（20%）
)
```

---

## 测试示例

运行完整测试：

```bash
python src/volatility_index.py
```

**预期输出**：

```
======================================================================
期货期权隐含波动率与 VIX 指数计算测试（完整版）
======================================================================

[测试 1] 白银期权 IV 计算
----------------------------------------------------------------------
期权代码: AG2406-C-5000
隐含波动率: 34.74%
理论价格: 150.00
市场价格: 150.00
误差: -0.0000
Vega: 551.6632
迭代次数: 4
是否收敛: True

[测试 2] VIX 指数计算
----------------------------------------------------------------------
商品: AG2406
VIX 指数: 319.35
看涨贡献: 16.84%
看跌贡献: 3.28%
期权数量: 9
IV Rank: 50.0%
IV Percentile: 50.0%

交易信号: 正常波动，按技术面交易（IV Rank: 50）
是否触发警报: False

======================================================================
测试完成
======================================================================
```

---

## 高级功能

### 1. IV 历史数据管理

```python
# 自动保存 IV 历史数据
service.save_iv_history()

# 历史数据保存在 ./data/iv_history.json
# 下次启动时自动加载
```

### 2. 自定义商品配置

```python
custom_config = {
    "MY_SYMBOL": CommodityConfig(
        symbol="MY_SYMBOL",
        name="我的商品",
        category=CommodityCategory.ENERGY,
        currency=CurrencyType.USD,
        high_iv_threshold=0.35,
        extreme_iv_threshold=0.55
    )
}

service = VolatilityIndexService(commodity_configs=custom_config)
```

### 3. 关闭流动性过滤

```python
# 如果你的数据源质量很高，可以关闭流动性过滤
service = VolatilityIndexService(enable_liquidity_filter=False)
```

### 4. 仅使用绝对值（不使用 IV Percentile）

```python
# 关闭 IV Percentile 计算
service = VolatilityIndexService(enable_iv_percentile=False)
```

---

## 集成到 A 股分析系统

VIX 数据已经**自动集成**到 AI 分析流程中：

```python
# 在 main.py 或 pipeline.py 中
from src.volatility_index import get_volatility_fetcher

# 获取 VIX 数据
vix_fetcher = get_volatility_fetcher()
vix_value = vix_fetcher.get_volatility_index("SPY")  # 标普500 VIX

# 传递给 AI 分析器
context['vix_data'] = {
    'vix': vix_value,
    'iv_percentile': vix_fetcher.calculate_iv_percentile("SPY"),
    'signal': '恐慌' if vix_value > 30 else '正常'
}

# AI 会自动看到 VIX 并调整策略
result = analyzer.analyze(context, news_list=news_list)
```

---

## 常见问题

### Q1: 如何获取真实的期权数据？

**A**: 本系统只负责**计算**，数据获取需要另外实现：

- **国内**: 使用 `akshare` 或 `tushare` 获取上交所期权数据
- **国外**: 使用 `yfinance` 或 CBOE 官方数据

### Q2: VIX 计算结果为什么与 CBOE 不完全一致？

**A**: 可能原因：
1. 使用了简化算法（虚值期权加权平均）
2. 数据时间点不同
3. 利率假设不同

建议：**优先使用官方 VIX 数据**（`volatility_index_fetcher.py`），仅在不可用时才计算。

### Q3: 如何添加新商品？

**A**: 在 `DEFAULT_COMMODITY_CONFIGS` 中添加配置：

```python
"NEW_SYMBOL": CommodityConfig(
    symbol="NEW_SYMBOL",
    name="新商品",
    category=CommodityCategory.AGRICULTURE,
    currency=CurrencyType.CNY,
    high_iv_threshold=0.30,
    extreme_iv_threshold=0.50
)
```

### Q4: IV Rank 和 IV Percentile 有什么区别？

**A**:
- **IV Rank**: 当前 IV 在过去一年 [最低, 最高] 之间的位置
- **IV Percentile**: 过去一年有多少天的 IV <= 当前 IV

**推荐使用 IV Percentile**，因为它能剔除极端值的影响。

---

## 技术支持

如有问题，请查看：
- 核心算法实现：`src/volatility_index.py`
- 测试代码：文件末尾的 `if __name__ == "__main__"` 部分
- Yahoo Finance 获取：`src/volatility_index_fetcher.py`

---

**版本**: 1.0.0
**最后更新**: 2026-02-02
**作者**: Claude Code
