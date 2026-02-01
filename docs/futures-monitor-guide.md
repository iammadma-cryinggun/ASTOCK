# 期货波动率监控使用指南

## 🎯 功能概述

本系统实现了基于 **IV-HV 背离** 的期货/贵金属期权风险监控，通过检测隐含波动率(IV) 与历史波动率(HV) 的背离信号，预测市场崩盘风险。

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

## 📋 监控标的

### 贵金属 ETF
- **GLD** - SPDR 黄金信托
- **SLV** - iShares 白银信托
- **IAU** - iShares 黄金信托
- **PPLT** - Aberdeen 标准铂金ETF
- **PALL** - Aberdeen 标准钯金ETF

### 商品 ETF
- **USO** - 美国石油基金
- **UNG** - 天然气ETF
- **DBC** - Invesco 大宗商品指数
- **DBA** - Invesco 农业基金
- **DBB** - Invesco 基础金属ETF

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

## 📊 报告示例

```
============================================================
📊 期货/贵金属期权波动率监控报告
生成时间: 2026-02-01 10:30:00
============================================================

🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨
【极端风险预警】IV-HV 背离信号
🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨

🔴 黄金SPDR (GLD)
   当前价格: $185.20
   IV (隐含波动率): 40.21% (历史分位: 100.0%)
   HV (历史波动率): 21.76%
   IV-HV 背离度: 18.45%
   风险等级: extreme

   ⚠️ 风险提示:
   当 IV 处于历史高位且显著高于 HV 时，
   意味着期权杠杆极其昂贵，多头面临时间损耗反噬。
   一旦动能不足（甚至不需要下跌，只要横盘），
   昂贵的杠杆成本将导致多头崩盘。

🔴 白银iShares (SLV)
   当前价格: $22.50
   IV (隐含波动率): 45.30% (历史分位: 98.5%)
   HV (历史波动率): 25.40%
   IV-HV 背离度: 19.90%
   风险等级: extreme

============================================================
```

## ⚠️ 重要提示

### 数据来源限制

当前实现使用以下数据：
- ✅ 历史价格数据（从 AkShare、Yahoo Finance 获取）
- ✅ 历史波动率（HV）计算
- ⚠️ 隐含波动率（IV）估算（简化版）

**真实 IV 数据需要：**
- 期权链数据（VIX、GVZ 等）
- 或期权报价数据
- 这些数据通常需要付费 API

### 改进方向

**如需专业级实现：**
1. 接入期权链数据源
2. 计算真实的 IV（从 ATM 期权隐含波动率）
3. 获取 VIX、GVZ 等波动率指数
4. 添加 Put/Call Ratio 指标
5. 添加波动率偏斜 (Skew) 指标

## 📚 参考资料

### 推荐阅读
- 《期权波动率与估值》
- CBOE 波动率指数文档
- VIX 白皮书

### 相关指标
- **VIX** - 标普500波动率指数
- **GVZ** - 黄金波动率指数
- **OVX** - 原油波动率指数
- **VXEEM** - 新兴市场波动率指数

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

### 问题 2: IV 计算不准确

**说明：** 当前使用简化估算方法，真实 IV 需要期权链数据

### 问题 3: 报告为空

**检查：**
- 标的代码是否正确
- 数据源是否可用
- 查看日志错误信息

## 💡 进阶功能

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
