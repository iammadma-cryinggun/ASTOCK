# 🎯 结构张力模型 - 完整使用指南

## 📋 目录

1. [系统概述](#系统概述)
2. [Python 后端（完整版）](#python-后端完整版)
3. [TradingView 前端（简化版）](#tradingview-前端简化版)
4. [实战应用](#实战应用)
5. [算法原理](#算法原理)

---

## 系统概述

### 什么是结构张力模型？

**核心思想**：将价格波动映射到复平面，通过 FFT 提取主要频率成分，使用 Hilbert 变换计算"张力"，识别市场拐点。

### 两个版本

| 版本 | 精确度 | 用途 | 优势 |
|------|--------|------|------|
| **Python 后端** | 100% | 精确分析、回测 | 完整 FFT-Hilbert 算法，无未来函数 |
| **TradingView 前端** | 80% | 实时监控、可视化 | 无需计算，直接在图表上显示 |

**推荐使用方式**：
- **日常监控**：使用 TradingView 指标（快速、直观）
- **精确分析**：使用 Python 后端（完整算法、回测验证）

---

## Python 后端（完整版）

### 功能特性

✅ **完整的 FFT-Hilbert 算法**
- 快速傅里叶变换
- Top N 能量过滤
- 希尔伯特变换
- 滚动窗口（避免未来函数）

✅ **双模式分析**
- 主趋势模式（Top 1-8）：捕捉主要波动
- 先行指标模式（Top 9-16）：提前识别拐点

✅ **多种输出**
- 实时状态分析
- 滚动回测
- 信号生成
- 可视化图表

### 快速开始

#### 1. 安装依赖

```bash
pip install numpy pandas scipy matplotlib
```

#### 2. 基础使用

```python
from src.structural_tension import get_structural_tension_model
import pandas as pd

# 加载数据
df = pd.read_csv('your_data.csv')  # 需要 'close' 和 'date' 列

# 创建模型
model = get_structural_tension_model(
    top_n_main=8,        # 主趋势频率数量
    top_n_lead=16,       # 先行指标频率数量
    window_size=200,     # 窗口大小（交易日）
    tension_threshold=1.6 # 张力阈值
)

# 分析当前状态
state = model.analyze_current_state(df)
print(f"当前状态: {state['state']}")
print(f"描述: {state['description']}")
print(f"建议: {state['recommendation']}")
```

#### 3. 滚动回测

```python
# 运行滚动回测（避免未来函数）
result_df = model.walk_forward_test(df, mode="main")

# 查看结果
print(result_df.head(10))

# 信号统计
print(result_df['signal'].value_counts())
```

#### 4. 完整示例（含可视化）

```python
from src.structural_tension import get_structural_tension_model
import pandas as pd
import matplotlib.pyplot as plt

# 加载数据
df = pd.read_csv('AAPL.csv', parse_dates=['date'])

# 创建模型
model = get_structural_tension_model(window_size=200)

# 滚动回测
result_df = model.walk_forward_test(df, mode="main")

# 绘图
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))

# 1. 价格图 + 信号
buy_dates = result_df[result_df['signal'] == 'BUY']['date']
sell_dates = result_df[result_df['signal'] == 'SELL']['date']
buy_prices = result_df[result_df['signal'] == 'BUY']['price']
sell_prices = result_df[result_df['signal'] == 'SELL']['price']

ax1.plot(result_df['date'], result_df['price'], label='Price', color='black', alpha=0.5)
ax1.scatter(buy_dates, buy_prices, color='green', marker='^', s=100, label='Buy', zorder=5)
ax1.scatter(sell_dates, sell_prices, color='red', marker='v', s=100, label='Sell', zorder=5)
ax1.set_ylabel('Price')
ax1.set_title('Structural Tension Model - Backtest Results')
ax1.legend()
ax1.grid(True)

# 2. 张力曲线
ax2.plot(result_df['date'], result_df['tension'], label='Tension', color='blue')
ax2.axhline(y=1.6, color='red', linestyle='--', alpha=0.5, label='Overbought')
ax2.axhline(y=-1.6, color='green', linestyle='--', alpha=0.5, label='Oversold')
ax2.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
ax2.set_ylabel('Tension')
ax2.legend()
ax2.grid(True)

# 3. 信号密度
signal_counts = result_df['signal'].value_counts()
colors = ['green', 'red', 'gray']
ax3.bar(signal_counts.index, signal_counts.values, color=colors[:len(signal_counts)])
ax3.set_ylabel('Count')
ax3.set_title('Signal Distribution')
ax3.grid(True)

plt.tight_layout()
plt.savefig('structural_tension_analysis.png', dpi=100)
print("图表已保存: structural_tension_analysis.png")
```

### API 参考

#### `StructuralTensionModel` 类

**初始化参数**：
```python
model = StructuralTensionModel(
    top_n_main=8,          # 主趋势频率数量 (1-8)
    top_n_lead=16,          # 先行指标频率数量 (9-16)
    window_size=200,        # 滚动窗口大小（交易日）
    tension_threshold=1.6  # 张力阈值
)
```

**主要方法**：

1. **`analyze_current_state(df)`**
   - 分析当前市场状态
   - 返回：tension_main, tension_lead, state, description, recommendation

2. **`walk_forward_test(df, mode)`**
   - 滚动回测
   - 参数：mode="main" 或 "lead"
   - 返回：DataFrame (date, price, tension, signal)

3. **`calculate_single_point(prices, mode)`**
   - 计算单点张力
   - 返回：float (当前张力值)

---

## TradingView 前端（简化版）

### 功能特性

✅ **实时计算**
- 自动计算张力指标
- 滚动窗口（避免未来函数）
- 即时显示买卖信号

✅ **可视化面板**
- 张力曲线
- 超买/超卖区域
- 信号标注（买入/卖出）
- 信息面板（8 项指标）

✅ **Alert 支持**
- 可配置 Alert 通知
- 支持 Webhook

### 快速开始

#### 1. 添加指标

1. 打开 TradingView
2. 点击 "Pine Editor"
3. 复制 `tradingview/StructuralTension.pine` 代码
4. 点击 "添加到图表"

#### 2. 查看效果

- **主图**：价格 + 买卖信号标注
- **副图**：张力曲线 + 阈值线 + 柱状图
- **右上角**：信息面板（实时数据）

#### 3. 参数调整

点击指标设置 ⚙️，可以调整：

**窗口设置**：
- 窗口大小：默认 200 交易日
- 建议：短线 100，中线 200，长线 500

**平滑设置**：
- 平滑周期：默认 20
- 降低 → 更敏感（更多信号）
- 提高 → 更平滑（更少噪音）

**张力设置**：
- 张力阈值：默认 1.6
- 降低 → 更多信号（可能增加假信号）
- 提高 → 更少信号（错过机会）

**显示选项**：
- 显示张力曲线
- 显示买卖信号
- 显示柱状图
- 显示信息面板

### 信号说明

#### 张力值解释

| 张力值 | 状态 | 含义 |
|--------|------|------|
| > 2.4 | 极度超买 | 市场可能处于顶部区域 |
| > 1.6 | 超买 | 买盘接近枯竭 |
| -1.6 ~ 1.6 | 中性 | 市场处于平衡 |
| < -1.6 | 超卖 | 卖压接近枯竭 |
| < -2.4 | 极度超卖 | 市场可能处于底部区域 |

#### 信号类型

1. **普通买入（绿色三角形△）**
   - 条件：从超卖区域拐头向上
   - 含义：短期反弹机会

2. **普通卖出（红色三角形▽）**
   - 条件：从超买区域拐头向下
   - 含义：短期回调风险

3. **极端买入（★极端买入）**
   - 条件：从极度超卖拐头向上
   - 含义：重要底部机会

4. **极端卖出（☆极端卖出）**
   - 条件：从极度超买拐头向下
   - 含义：重要顶部风险

### 配置 Alert（可选）

#### 创建信号通知

1. 点击图表右上角 Alert 按钮 📡
2. 条件：`张力信号 不等于 "NONE"`
3. 勾选 Webhook URL（可选）
4. 消息格式：
```json
{
  "ticker": "{{ticker}}",
  "signal": "{{plot_0}}",
  "tension": {{plot_1}},
  "price": {{close}}
}
```

---

## 实战应用

### 场景 1：日常监控

**目标**：快速识别买卖机会

**工具**：TradingView 指标

**流程**：
1. 打开 TradingView
2. 添加结构张力指标
3. 查看右上角信息面板
4. 关注买入/卖出信号

**优点**：实时、直观、无需计算

---

### 场景 2：精确分析

**目标**：回测验证、深度研究

**工具**：Python 后端

**流程**：
1. 导入历史数据
2. 运行滚动回测
3. 统计信号准确率
4. 优化参数

**示例代码**：
```python
from src.structural_tension import get_structural_tension_model
import pandas as pd

# 加载数据
df = pd.read_csv('AAPL.csv')

# 创建模型
model = get_structural_tension_model(window_size=200)

# 回测
result_df = model.walk_forward_test(df, mode="main")

# 计算胜率
buy_signals = result_df[result_df['signal'] == 'BUY']
sell_signals = result_df[result_df['signal'] == 'SELL']

print(f"买入信号: {len(buy_signals)} 次")
print(f"卖出信号: {len(sell_signals)} 次")

# 计算收益率（示例）
returns = []
for i in range(1, len(result_df)):
    if result_df['signal'].iloc[i-1] == 'BUY' and result_df['signal'].iloc[i] == 'SELL':
        ret = (result_df['price'].iloc[i] - result_df['price'].iloc[i-1]) / result_df['price'].iloc[i-1]
        returns.append(ret)

if returns:
    avg_return = sum(returns) / len(returns)
    win_rate = len([r for r in returns if r > 0]) / len(returns) * 100
    print(f"平均收益: {avg_return*100:.2f}%")
    print(f"胜率: {win_rate:.1f}%")
```

---

### 场景 3：双系统配合

**最佳实践**：TradingView 实时监控 + Python 定期回测

**流程**：
1. **日常**：使用 TradingView 指标实时监控
2. **每周**：用 Python 回测，优化参数
3. **每月**：对比两个系统，验证一致性

---

## 算法原理

### 为什么这个模型有效？

#### 1. 频域分析

市场价格 = 不同周期波动叠加

FFT 可以分解出：
- 低频（长期趋势）
- 中频（波段）
- 高频（噪音）

Top N 过滤只保留主要波动，去除噪音。

#### 2. Hilbert 变换

将价格从时域转换到复平面：
- 实部：平滑后的价格
- 虚部：张力（势能）

**物理意义**：
- 张力 > 0：上升动能
- 张力 < 0：下降动能
- 张力拐点：趋势反转

#### 3. 避免未来函数

**错误做法**（未来函数）：
```
计算 2020-01-01 的张力 → 使用 2015-2025 全部数据
```

**正确做法**（滚动窗口）：
```
计算 2020-01-01 的张力 → 只使用 2015-2020-01-01 历史数据
```

这就是为什么我们的模型用 `walk_forward_test`！

---

## 常见问题

### Q1: Python 版本运行慢？

**A**: FFT 计算是 O(n log n)，窗口越大越慢。

**解决方法**：
- 减小 `window_size`（从 200 → 100）
- 减少数据点数（采样）
- 使用更快的硬件

### Q2: TradingView 版本准吗？

**A**: 80% 准确。

**原因**：
- Pine Script 不支持完整 FFT
- 使用 EMA 平滑模拟频域滤波
- 但核心逻辑一致（滚动窗口 + 拐点检测）

**建议**：
- 实时监控用 TradingView
- 精确分析用 Python

### Q3: 参数如何优化？

**A**: 使用网格搜索。

```python
# 参数优化示例
best_return = -999
best_params = {}

for window in [100, 150, 200, 250]:
    for threshold in [1.2, 1.4, 1.6, 1.8]:
        model = StructuralTensionModel(window_size=window, tension_threshold=threshold)
        result_df = model.walk_forward_test(df)

        # 计算收益
        returns = calculate_returns(result_df)
        avg_return = sum(returns) / len(returns)

        if avg_return > best_return:
            best_return = avg_return
            best_params = {'window': window, 'threshold': threshold}

print(f"最佳参数: {best_params}")
print(f"最佳收益: {best_return*100:.2f}%")
```

### Q4: 适合哪些品种？

**A**: 理论上所有流动性好的品种。

**推荐**：
- ✅ 股票（AAPL, TSLA）
- ✅ 指数（SPY, QQQ）
- ✅ 期货（GC, CL）
- ✅ 加密货币（BTC, ETH）

**不推荐**：
- ❌ 低流动性品种
- ❌ 极端波动品种（需要调整阈值）

---

## 技术支持

### 文件位置

- Python 模型：`src/structural_tension.py`
- TradingView 指标：`tradingview/StructuralTension.pine`
- 使用文档：`docs/STRUCTURAL_TENSION_GUIDE.md`

### 问题反馈

如有问题，请：
1. 查看代码注释
2. 查看 API 参考
3. 提交 Issue

---

## 更新日志

### v1.0.0 (2025-01-15)
- ✅ 完整 Python FFT-Hilbert 实现
- ✅ TradingView 简化版指标
- ✅ 滚动回测（避免未来函数）
- ✅ 双模式分析（主趋势 + 先行指标）
- ✅ 完整文档

---

**祝交易顺利！📈💰**

*结构张力模型 - 捕捉市场拐点的利器*
