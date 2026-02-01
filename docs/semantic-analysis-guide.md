# 专业金融语义分析模型配置指南

## 概述

本项目已集成专业金融语义分析模型，用于增强新闻情绪分析和财报深度挖掘能力。

---

## 支持的专业模型

### 1. FinBERT-Chinese（新闻情绪快速打分）

**特点：**
- 毫秒级响应速度
- 对"跌停"、"减持"等金融词汇敏感
- 专门在中文金融语料上训练

**使用方式：** Hugging Face Inference API（云端调用，无需本地GPU）

**环境变量配置：**
```bash
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxx
```

**获取 API Key：**
1. 访问 https://huggingface.co/
2. 注册账号并登录
3. 进入 Settings → Access Tokens
4. 创建新的 Token（选择 Read 权限）

**应用场景：**
- 实时新闻情绪快速评分
- 大批量新闻标题情绪分析
- 替代通用LLM做情绪分类（速度提升1000倍）

---

### 2. XuanYuan-70B（轩辕-70B，财报深度分析）

**特点：**
- 70B参数，逻辑推理能力最强
- 专门针对金融文档训练
- 能看懂财报里的陷阱（商誉减值、关联交易等）

**使用方式：** 云端 API（无需本地GPU）

**环境变量配置：**
```bash
XUANYUAN_API_KEY=your_xuanyuan_api_key
XUANYUAN_BASE_URL=https://api.xuanyuan.ai/v1
```

**应用场景：**
- 财报/公告深度分析
- 识别财务风险信号
- 复杂金融文档理解

**注意：** 轩辕大模型 API 地址需要确认（示例地址可能不准确）

---

## 集成架构

### 语义分析路由器（SemanticRouter）

根据任务类型智能选择最佳模型：

| 任务类型 | 最佳模型 | 响应时间 | 成本 |
|---------|---------|---------|------|
| `news_sentiment` | FinBERT-Chinese | 毫秒级 | 低 |
| `financial_report` | XuanYuan-70B | 秒级 | 中 |
| `macro_analysis` | DeepSeek/千问 | 秒级 | 低 |
| `general` | DeepSeek/千问 | 秒级 | 低 |

### 代码示例

```python
from src.semantic_router import get_semantic_router, TaskType

router = get_semantic_router()

# 快速情绪分析
result = router.analyze(
    task_type=TaskType.NEWS_SENTIMENT,
    content="宁德时代发布业绩预告，净利润同比增长50%"
)
# 输出: score=0.85, label='positive', 耗时<100ms

# 财报深度分析
result = router.analyze(
    task_type=TaskType.FINANCIAL_REPORT,
    content="[财报全文...]"
)
# 输出: 深度分析报告，识别风险点
```

---

## 配置优先级

### 无需配置（可选）
如果未配置专业模型 API Key，系统会自动回退到通用 LLM（DeepSeek/千问/Gemini）。

### 推荐配置（增强体验）
1. **最低成本**：仅配置 `HUGGINGFACE_API_KEY`（FinBERT）
   - 优势：新闻情绪分析速度提升 1000 倍
   - 成本：Hugging Face 免费版有限制，但足够个人使用

2. **完整配置**：FinBERT + XuanYuan
   - 优势：新闻快筛 + 财报深挖
   - 成本：需确认轩辕 API 定价

---

## 快速开始

### 1. 配置环境变量

编辑 `.env` 文件：

```bash
# 专业金融模型（可选）
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxx
# XUANYUAN_API_KEY=your_xuanyuan_key
# XUANYUAN_BASE_URL=https://api.xuanyuan.ai/v1

# 通用 LLM（必需，至少配置一个）
OPENAI_API_KEY=sk-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
```

### 2. 测试集成

```bash
python -m src.semantic_router
```

预期输出：
```
=== 测试新闻情绪分析 ===

新闻: 宁德时代发布业绩预告，净利润同比增长50%，超市场预期
  情绪: positive (0.980)
  置信度: 0.980
  模型: FinBERT-Chinese
  耗时: 87ms

新闻: 某公司公告控股股东减持5%股份
  情绪: negative (-0.950)
  置信度: 0.950
  模型: FinBERT-Chinese
  耗时: 75ms

新闻: 证监会发布新规，加强对上市公司监管
  情绪: neutral (0.000)
  置信度: 0.850
  模型: FinBERT-Chinese
  耗时: 68ms
```

### 3. 集成到主流程

语义路由器已自动集成到 `src/analyzer.py`，当检测到新闻分析任务时会自动使用 FinBERT。

无需额外配置，系统会智能选择最佳模型。

---

## 故障排查

### FinBERT 调用失败

**错误：** `[FinBERT] API 返回错误: 503`

**原因：** Hugging Face Inference API 免费版有队列等待时间

**解决方案：**
1. 等待几秒后重试
2. 或升级到付费版（$9/月）
3. 或回退到通用 LLM（自动）

### XuanYuan 调用失败

**错误：** `[轩辕] API 调用尚未实现，使用通用 LLM 替代`

**原因：** XuanYuan API 调用逻辑尚未完整实现

**解决方案：**
1. 暂时使用通用 LLM
2. 或联系开发者实现轩辕 API 集成

---

## 模型对比

| 特性 | FinBERT-Chinese | XuanYuan-70B | DeepSeek | 通义千问 |
|------|----------------|--------------|----------|----------|
| 响应速度 | ⚡⚡⚡ 毫秒级 | ⚡⚡ 秒级 | ⚡⚡ 秒级 | ⚡⚡ 秒级 |
| 金融专业性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 逻辑推理 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 成本 | 低/免费 | 中 | 低 | 低 |
| 需要GPU | ❌ | ❌ | ❌ | ❌ |

---

## 后续计划

- [ ] 完成 XuanYuan API 调用实现
- [ ] 集成 DISC-FinLLM（期货宏观分析）
- [ ] 添加 Cornucopia（知识图谱关联）
- [ ] 支持多模型结果融合（投票机制）

---

## 参考链接

- **FinBERT 论文**：https://arxiv.org/abs/1908.10063
- **FinBERT-Chinese 模型**：https://huggingface.co/chtma/finbert-chinese
- **轩辕大模型**：需确认官方链接
- **Hugging Face Inference API**：https://huggingface.co/docs/api-inference/index
