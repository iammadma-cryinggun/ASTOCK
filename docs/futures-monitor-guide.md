# 期货波动率监控使用指南 - 华尔街标准混合模式

## 🎯 功能概述

本系统实现了基于 **IV-HV 背离** 的期货/贵金属期权风险监控，采用**华尔街专业交易台标准做法**：

### 核心策略层级

**层级 1: 完美支持品种**（CBOE 官方波动率指数）
- 直接使用 CBOE 官方波动率指数（VIX、GVZ、OVX 等）
- **消除波动率微笑偏差 (Volatility Smile Bias)**
- 数据源权威：交易所已用复杂算法加权平均所有行权价

**层级 2: 降级支持品种**（指数数据可能不稳定）
- 优先尝试获取 CBOE 指数
- 失败时自动降级到 HV 估算

**层级 3: 不支持品种**（必须使用期权链计算）
- 铜、铝、钯金、铂金、个股等
- 需要从期权链手动计算 IV

## 📊 核心指标

### 1. 波动率指标

| 指标 | 说明 | 用途 |
|------|------|------|
| **IV (隐含波动率)** | 市场预期波动率，决定期权价格 | 衡量杠杆成本 |
| **HV (历史波动率)** | 标的实际波动率 | 衡量实际动能 |
| **IV 分位数** | IV 在历史中的位置 (0-100%) | 判断是否处于极端 |
| **IV-HV 背离度** | IV - HV 的差值 | 检测风险信号 |

### 2. 风险信号

**极端背离信号 (🔴):**
- IV 分位数 ≥ 95%
- IV-HV 背离度 ≥ 30%

**高风险信号 (🟠):**
- IV 分位数 ≥ 90%
- IV-HV 背离度 ≥ 20%

**警告信号 (🟡):**
- IV 分位数 ≥ 80%
- IV-HV 背离度 ≥ 15%

**安全状态 (🟢):**
- 未达到上述阈值

## 🔬 核心逻辑

```
风险判断公式：
[实际动能收益] < [维持高 IV 的成本]

当 IV >> HV 时：
- 期权杠杆极其昂贵（时间损耗 Theta 高）
- 但实际动能不足（HV 低）
- 多头面临时间损耗反噬
- 一旦横盘或上涨放缓，崩盘开始
```

## 📋 支持的标的映射

### 层级 1: 完美支持（CBOE 官方指数）

| 标的资产 | 标的代码 | 波动率指数 | 备注 |
|---------|---------|-----------|------|
| **美股大盘** | SPY, ES | ^VIX | 标普500 VIX |
| **纳斯达克** | QQQ, NQ | ^VXN | 纳斯达克 VIX |
| **黄金** | GLD, IAU, GC | ^GVZ | 黄金 VIX |
| **原油** | USO, CL | ^OVX | 原油 VIX |

### 层级 2: 降级支持（指数可能不稳定）

| 标的资产 | 标的代码 | 波动率指数 | 备注 |
|---------|---------|-----------|------|
| **白银** | SLV, SI | ^VXSLV | Yahoo 数据不稳定 |
| **欧元** | FXE, EUR | ^EVZ | 欧元 VIX |
| **黄金矿业** | GDX, GDXJ | ^GVZ | 降级使用黄金指数 |
| **天然气** | UNG, NG | ^OVX | 降级使用原油指数 |
| **农产品** | DBC, DBA | ^OVX | 降级使用原油指数 |

### 层级 3: 不支持指数（需要期权链）

以下品种**不存在**免费公开的波动率指数：
- **铜:** CPER, HG=F
- **钯金:** PALL
- **铂金:** PPLT
- **个股:** TSLA, NVDA, AAPL 等

## 🚀 使用方法

### 方法 1: 命令行分析

```bash
# 分析所有默认标的
python examples/futures_analysis_example.py

# 分析指定标的
python -c "
from src.futures_monitor import get_volatility_monitor
monitor = get_volatility_monitor()
report = monitor.generate_risk_report(['GLD', 'SLV', 'USO'])
print(report)
"
```

### 方法 2: WebUI 查看

访问 WebUI 的期货监控页面：
```
http://127.0.0.1:8000/futures
```

功能：
- 📊 查看所有标的的实时指标
- 🚨 极端风险预警
- 📈 IV/HV 趋势图
- 🔍 按风险等级筛选

### 方法 3: API 调用

```bash
# 获取所有标的监控数据
curl http://127.0.0.1:8000/api/futures/volatility

# 获取极端风险标的
curl http://127.0.0.1:8000/api/futures/extreme-risk

# 生成风险报告
curl http://127.0.0.1:8000/api/futures/report
```

## 💡 原理说明

### 为什么使用 CBOE 官方指数？

1. **消除波动率微笑偏差**
   - 单个期权 IV 只代表某个行权价的波动率
   - CBOE 指数是所有行权价的加权平均，代表整个市场的恐惧程度

2. **数据源权威性**
   - CBOE 已经用复杂的算法（包括牛顿迭代法）计算了几万次
   - 最终答案比我们自己反推更准确、更客观

3. **华尔街标准做法**
   - 专业交易台 (Prop Desk) 都使用官方指数
   - 这是机构级的风控工具

### IV 是如何计算的？

**层級 1（CBOE 官方指数）：**
- VIX, GVZ, OVX 等本身就是 CBOE 计算好的波动率指数
- 这些指数的"价格"本身就是百分比（如 18.5 代表 18.5%）
- 直接使用即可，无需额外计算

**层級 2 & 3（降级方案）：**
- 使用 Black-Scholes 模型反向迭代
- 从 ATM 期权价格中反推 IV
- 或使用 HV × 1.1 作为保守估算

## 🎯 策略应用

### 1. 风险规避

**当检测到极端背离时：**
- ❌ 避免做多
- ❌ 避免买入看涨期权
- ✅ 考虑对冲仓位
- ✅ 考虑买入看跌期权（对冲）

**示例：**
```
GLD: IV=40%, HV=21%, 背离度=19%
→ 黄金期权极其昂贵，但实际动能不足
→ 建议：避免做多GLD，或使用Put对冲
```

### 2. 时机选择

**入场时机（IV 回归理性后）：**
- GLD IV 回到 20% 左右
- SLV IV 回到 40% 左右
- IV-HV 背离度 < 10%

**离场时机（IV 极端时）：**
- IV 分位数 > 90%
- IV-HV 背离度 > 20%

### 3. 波动率交易

**做空波动率策略（适用条件）：**
- IV 处于极端高位（>95% 分位）
- 预期波动率会回归
- 可以考虑：
  - 卖出跨式组合 (Straddle)
  - 卖出宽跨式组合 (Strangle)
  - 铁鹰式组合 (Iron Condor)

⚠️ **警告：** 这些策略风险极高，需要专业知识和严格风控

## 📖 配置说明

### 环境变量配置

在 `.env` 文件中添加：

```bash
# 启用期货监控
FUTURES_MONITOR_ENABLED=true

# 监控标的列表（逗号分隔）
FUTURES_SYMBOLS=GLD,SLV,IAU,USO,UNG,DBC

# 风险阈值配置
IV_WARNING_THRESHOLD=80
IV_DANGER_THRESHOLD=90
IV_EXTREME_THRESHOLD=95
IV_HV_DIVERGENCE_WARNING=0.15
IV_HV_DIVERGENCE_DANGER=0.20
IV_HV_DIVERGENCE_EXTREME=0.30
```

## 🆘 故障排查

### 问题 1: 无法获取数据

**检查：**
```bash
# 测试数据源
python -c "
from src.data_provider import get_data_provider
dp = get_data_provider()
data = dp.get_stock_history('GLD', days=60)
print(f'获取到 {len(data)} 条数据')
"
```

### 问题 2: 白银 IV 获取失败

**说明：** 白银 (^VXSLV) 数据在 Yahoo 上不稳定，属于正常现象

**解决方案：** 系统会自动降级到 HV 估算

### 问题 3: 报告为空

**检查：**
- 标的代码是否正确
- 数据源是否可用
- 查看日志错误信息

## 💡 进阶功能

### 查看支持的标的分类

```python
from src.volatility_index import get_volatility_fetcher

fetcher = get_volatility_fetcher()
supported = fetcher.get_supported_symbols()

print("完美支持:", supported['perfect'])
print("降级支持:", supported['fallback'])
print("不支持:", supported['unsupported'])
```

### 自定义监控标的

```python
from src.futures_monitor import get_volatility_monitor

monitor = get_volatility_monitor()

# 添加自定义标的
custom_symbols = ['GLD', 'SLV', 'GDX', 'GDXJ']
report = monitor.generate_risk_report(custom_symbols)
```

### 设置预警阈值

```python
monitor = get_volatility_monitor()

# 修改阈值
monitor.IV_PERCENTILE_WARNING = 75  # 降低到 75%
monitor.IV_HV_DIVERGENCE_WARNING = 0.12  # 降低到 12%

# 重新分析
extreme = monitor.get_extreme_risk_symbols()
```

## 📞 获取帮助

- GitHub Issues
- 查看日志：`./logs/stock_analysis_*.log`
- 邮件联系：[项目维护者]

## ⚠️ 重要提示

### 数据来源限制

当前实现使用以下数据：
- ✅ CBOE 官方波动率指数（VIX, GVZ, OVX 等）
- ✅ Yahoo Finance 免费 API
- ✅ 历史波动率（HV）计算
- ⚠️ 降级方案使用 HV 估算（当指数数据不可用时）

### 改进方向

**如需更精确的 IV 计算：**
1. 接入付费期权链数据源
2. 实现完整的 Black-Scholes 牛顿迭代法
3. 添加 Put/Call Ratio 指标
4. 添加波动率偏斜 (Skew) 指标

## 📚 参考资料

### 推荐阅读
- 《期权波动率与估值》
- CBOE 波动率指数文档
- VIX 白皮书

### 相关指标
- **VIX** - 标普500波动率指数
- **GVZ** - 黄金波动率指数
- **OVX** - 原油波动率指数
- **VXSLV** - 白银波动率指数
- **EVZ** - 欧元波动率指数
- **VXN** - 纳斯达克波动率指数
