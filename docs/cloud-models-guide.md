# 🌐 云端API模型配置指南（无需GPU）

本指南汇总了所有可以通过API调用的云端AI模型，无需本地GPU。

## 📋 可用模型列表

### 🇨🇳 国内模型（推荐，中文友好）

| 模型 | 提供商 | 免费额度 | 价格 | API地址 | 特点 |
|------|--------|----------|------|---------|------|
| **DeepSeek-Chat** | DeepSeek | 500万tokens | ¥1/百万tokens | `https://api.deepseek.com/v1` | ✅已配置，便宜，中文好 |
| **DeepSeek-V3** | DeepSeek | - | - | `https://api.deepseek.com/v1` | 最新模型 |
| **通义千问-Turbo** | 阿里云 | 100万tokens | ¥0.5/百万tokens | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 速度快，便宜 |
| **通义千问-Plus** | 阿里云 | - | ¥4/百万tokens | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 能力强 |
| **Kimi（Moonshot）** | Moonshot | 新用户送100万tokens | ¥12/百万tokens | `https://api.moonshot.cn/v1` | 长文本强 |
| **智谱GLM-4** | 智谱AI | 25万tokens | ¥50/百万tokens | `https://open.bigmodel.cn/api/paas/v4` | 逻辑强 |
| **百川4** | 百川智能 | 100万tokens | ¥0.3/百万tokens | `https://api.baichuan-ai.com/v1` | 便宜 |
| **腾讯混元** | 腾讯 | 100万tokens | ¥7/百万tokens | `https://api.hunyuan.cloud.tencent.com/v1` | 稳定 |

### 🌍 国外模型（需要代理）

| 模型 | 提供商 | 免费额度 | 价格 | API地址 | 特点 |
|------|--------|----------|------|---------|------|
| **Gemini 2.0 Flash** | Google | 15次/天免费 | - | GoogleAI SDK | ✅已配置，快速免费 |
| **Gemini 1.5 Pro** | Google | - | 按使用 | GoogleAI SDK | 能力强 |
| **GPT-4o-mini** | OpenAI | - | $0.15/百万tokens | `https://api.openai.com/v1` | 快速便宜 |
| **GPT-4o** | OpenAI | - | $2.5/百万tokens | `https://api.openai.com/v1` | 通用最强 |
| **Claude 3.5 Sonnet** | Anthropic | - | $3/百万tokens | `https://api.anthropic.com/v1` | 代码好 |
| **Groq (Llama 3.1)** | Groq | 免费加速 | - | `https://api.groq.com/openai/v1` | ⚡超快推理 |

### 🆓 完全免费的模型

| 模型 | 提供商 | 限制 | 获取方式 |
|------|--------|------|----------|
| **Gemini 2.0 Flash** | Google | 15次/天 | https://aistudio.google.com/ |
| **Groq (Llama 3.1 70B)** | Groq | 限流 | https://groq.com/ |
| **HuggingFace Inference** | HF | 有限制 | https://huggingface.co/inference-api |

## 🎯 推荐配置方案

### 方案 1：完全免费（适合测试）

```bash
# .env 配置
GEMINI_API_KEY=你的Gemini_Key
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_MODEL_FALLBACK=gemini-1.5-flash

# 备用：Groq（需要注册）
OPENAI_API_KEY=gsk_xxxxx
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.1-70b-versatile
```

### 方案 2：性价比最高（推荐）

```bash
# .env 配置
# 主力：DeepSeek（便宜、中文好）
OPENAI_API_KEY=sk-xxxxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

# 备用：通义千问Turbo（便宜）
OPENAI_API_KEY_2=sk-xxxxx
OPENAI_BASE_URL_2=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL_2=qwen-turbo

# 兜底：Gemini（免费）
GEMINI_API_KEY=你的Gemini_Key
GEMINI_MODEL=gemini-2.0-flash-exp
```

### 方案 3：专业版（多模型ensemble）

```bash
# 情绪分析：通义千问Turbo（便宜快速）
QWEN_API_KEY=sk-xxxxx
QWEN_MODEL=qwen-turbo

# 综合分析：DeepSeek（便宜好）
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_MODEL=deepseek-chat

# 深度分析：Kimi（长文本强）
KIMI_API_KEY=sk-xxxxx
KIMI_MODEL=moonshot-v1-8k

# 兜底：Gemini（免费）
GEMINI_API_KEY=你的Gemini_Key
```

## 📝 快速开始

### 步骤 1：选择并注册模型

**推荐优先级：**
1. **DeepSeek** - 必选，便宜好用
   - 注册：https://platform.deepseek.com/
   - 免费额度：500万tokens

2. **通义千问** - 次选，便宜
   - 注册：https://dashscope.aliyuncs.com/
   - 免费额度：100万tokens

3. **Gemini** - 兜底，免费
   - 注册：https://aistudio.google.com/
   - 免费额度：15次/天

### 步骤 2：配置 .env 文件

```bash
# 复制示例配置
cp .env.example .env.new

# 编辑配置
nano .env.new
```

### 步骤 3：测试配置

```bash
# 测试 DeepSeek
python -c "
from openai import OpenAI
client = OpenAI(
    api_key='你的key',
    base_url='https://api.deepseek.com/v1'
)
response = client.chat.completions.create(
    model='deepseek-chat',
    messages=[{'role': 'user', 'content': '你好'}],
    max_tokens=10
)
print(response.choices[0].message.content)
"
```

## 🔧 各模型注册地址汇总

### 国内模型

| 模型 | 注册地址 | 文档地址 |
|------|----------|----------|
| DeepSeek | https://platform.deepseek.com/ | https://platform.deepseek.com/docs |
| 通义千问 | https://dashscope.aliyuncs.com/ | https://help.aliyun.com/zh/dashscope/ |
| Kimi | https://platform.moonshot.cn/ | https://platform.moonshot.cn/docs |
| 智谱GLM | https://open.bigmodel.cn/ | https://open.bigmodel.cn/dev/api |
| 百川 | https://platform.baichuan-ai.com/ | https://platform.baichuan-ai.com/ |
| 腾讯混元 | https://cloud.tencent.com/product/hunyuan | https://cloud.tencent.com/document/product/1729/104753 |

### 国外模型

| 模型 | 注册地址 | 文档地址 |
|------|----------|----------|
| Gemini | https://aistudio.google.com/ | https://ai.google.dev/docs |
| OpenAI | https://platform.openai.com/ | https://platform.openai.com/docs |
| Groq | https://groq.com/ | https://console.groq.com/docs |
| Anthropic | https://console.anthropic.com/ | https://docs.anthropic.com/ |

## 💡 使用建议

### 按使用场景选择

**快速分析（实时）：**
- 通义千问Turbo（快、便宜）
- DeepSeek-Chat（平衡）

**深度分析（非实时）：**
- Kimi（长文本）
- 智谱GLM-4（逻辑强）
- GPT-4o（通用强）

**完全免费：**
- Gemini 2.0 Flash（有次数限制）
- Groq（有限流）

### 成本对比（按100万tokens计算）

| 模型 | 价格（人民币） |
|------|---------------|
| 百川4 | ¥0.3 |
| 通义千问Turbo | ¥0.5 |
| DeepSeek | ¥1 |
| 智谱GLM-4 | ¥50 |
| Kimi | ¥12 |
| GPT-4o-mini | ¥1.05 |
| GPT-4o | ¥17.5 |
| Gemini 2.0 | ¥? (按使用) |

### 推荐组合（月成本 < ¥10）

```bash
# 主力：DeepSeek (90%使用)
OPENAI_API_KEY=sk-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

# 辅助：通义千问 (10%使用)
# 用于简单任务，节省成本
```

## ⚠️ 注意事项

### 1. API Key 安全
- ❌ 不要提交到公开仓库
- ✅ 使用 .env 文件
- ✅ 定期更换 Key

### 2. 速率限制
各模型有不同的速率限制：
- DeepSeek: 按余额限制
- 通义千问: QPS限制
- Gemini: 15次/天（免费版）

### 3. 网络问题
- 国外模型需要代理
- 建议优先使用国内模型

### 4. 模型切换
系统会自动切换，无需手动操作

## 🚀 下一步

1. 注册 DeepSeek 和通义千问
2. 更新 .env 配置
3. 运行测试：`python main.py --debug --stocks 600519`

## 📞 需要帮助？

- GitHub Issues
- 查看日志：`./logs/stock_analysis_*.log`
