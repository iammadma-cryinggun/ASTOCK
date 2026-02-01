# 📋 环境变量配置清单

## 🎯 最小配置（必填）

### 方案 1：仅 DeepSeek（推荐，便宜）

```bash
# DeepSeek API（主力）
OPENAI_API_KEY=sk-你的DeepSeek-Key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
OPENAI_TEMPERATURE=0.7

# 自选股列表
STOCK_LIST=600519,300750,002594
```

**获取方式：**
1. 访问：https://platform.deepseek.com/
2. 注册登录
3. 进入 API Keys 页面
4. 创建新的 API Key
5. 免费额度：500万tokens
6. 价格：¥1/百万tokens

---

### 方案 2：仅 Gemini（免费，有限制）

```bash
# Gemini API（免费）
GEMINI_API_KEY=AIzaSy你的Gemini-Key
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_MODEL_FALLBACK=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7

# 自选股列表
STOCK_LIST=600519,300750,002594
```

**获取方式：**
1. 访问：https://aistudio.google.com/
2. 登录 Google 账号
3. 创建 API Key
4. 免费额度：15次/天

---

## 🌟 推荐配置（多模型备份）

```bash
# ===== 主力：DeepSeek =====
OPENAI_API_KEY=sk-你的DeepSeek-Key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
OPENAI_TEMPERATURE=0.7

# ===== 备选：通义千问（可选）=====
QWEN_API_KEY=sk-你的通义千问-Key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-turbo

# ===== 兜底：Gemini（免费）=====
GEMINI_API_KEY=AIzaSy你的Gemini-Key
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_MODEL_FALLBACK=gemini-1.5-flash

# ===== 自选股列表 =====
STOCK_LIST=600519,300750,002594
```

---

## 📱 可选配置

### Telegram 通知

```bash
TELEGRAM_BOT_TOKEN=你的Bot_Token
TELEGRAM_CHAT_ID=你的Chat_ID
```

**获取方式：** 参考 `docs/telegram-guide.md`

### 企业微信通知

```bash
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的Key
```

### 飞书通知

```bash
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/你的Key
```

### 邮件通知

```bash
EMAIL_SENDER=your_email@qq.com
EMAIL_PASSWORD=your_email_auth_code
EMAIL_RECEIVERS=receiver@example.com
```

---

## 🔍 完整配置示例

```bash
# ===================================
# 自选股列表
# ===================================
STOCK_LIST=600519,300750,002594

# ===================================
# AI 模型配置
# ===================================

# 主力：DeepSeek
OPENAI_API_KEY=sk-xxxxxxxxxxxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
OPENAI_TEMPERATURE=0.7

# 备选：通义千问（可选）
# QWEN_API_KEY=sk-xxxxxxxxxxxx
# QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# QWEN_MODEL=qwen-turbo

# 兜底：Gemini（免费）
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxx
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_MODEL_FALLBACK=gemini-1.5-flash

# ===================================
# 搜索引擎配置（可选）
# ===================================
# TAVILY_API_KEYS=tvly-xxxxxxxxxxxx
# SERPAPI_API_KEYS=your_serpapi_key

# ===================================
# 通知渠道配置（可选）
# ===================================
# TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
# TELEGRAM_CHAT_ID=123456789

# ===================================
# 系统配置（通常使用默认值）
# ===================================
LOG_DIR=./logs
LOG_LEVEL=INFO
MAX_WORKERS=3
GEMINI_REQUEST_DELAY=2.0
GEMINI_MAX_RETRIES=5

# ===================================
# WebUI 配置
# ===================================
WEBUI_ENABLED=true
WEBUI_HOST=127.0.0.1
WEBUI_PORT=8000

# ===================================
# 定时任务配置（可选）
# ===================================
SCHEDULE_ENABLED=false
SCHEDULE_TIME=18:00
MARKET_REVIEW_ENABLED=true
```

---

## ✅ 配置检查清单

部署前请确认：

- [ ] 已配置至少一个 AI 模型（DeepSeek 或 Gemini）
- [ ] 已填写 STOCK_LIST（自选股代码）
- [ ] AI API Key 格式正确（不以 `your_` 或 `sk-your` 开头）
- [ ] 如需通知，已配置通知渠道

---

## 🚀 快速测试

配置完成后，运行以下命令测试：

```bash
# 测试所有模型
python test_models.py

# 测试分析功能
python main.py --debug --stocks 600519

# 启动 WebUI
python main.py --webui
```

---

## 📞 需要帮助？

- 完整指南：`docs/cloud-models-guide.md`
- Telegram 配置：`docs/telegram-guide.md`
- Zeabur 部署：`ZEAEBUR_DEPLOYMENT.md`
