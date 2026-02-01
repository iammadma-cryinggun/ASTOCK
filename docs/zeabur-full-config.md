# 🚀 Zeabur 完整配置清单（含 Telegram）

## ✅ 必须配置的环境变量

### 📊 AI 模型配置（11个变量）

```
OPENAI_API_KEY=sk-你的通义千问Key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-turbo
OPENAI_TEMPERATURE=0.7
STOCK_LIST=600519,300750,002594
WEBUI_ENABLED=true
WEBUI_HOST=0.0.0.0
WEBUI_PORT=8000
LOG_LEVEL=INFO
LOG_DIR=/app/logs
GEMINI_REQUEST_DELAY=2.0
GEMINI_MAX_RETRIES=5
```

---

## 📱 Telegram 通知配置（2个变量）

### 获取 Telegram Bot Token 和 Chat ID

**步骤 1：创建 Telegram Bot**
1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot`
3. 按提示设置 bot 名称（如：`MyStockBot`）
4. 获得Bot Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

**步骤 2：获取 Chat ID**
1. 在 Telegram 搜索 `@getidsbot`
2. 发送 `/start`
3. 机器人会返回你的 Chat ID（纯数字，如：`123456789`）

### 在 Zeabur 添加 Telegram 变量

```
TELEGRAM_BOT_TOKEN=你的Bot_Token
TELEGRAM_CHAT_ID=你的Chat_ID
```

**完整示例：**
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

---

## 🌟 完整配置（AI + Telegram）

### 复制以下所有内容到 Zeabur 环境变量：

```
OPENAI_API_KEY=sk-你的通义千问Key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-turbo
OPENAI_TEMPERATURE=0.7
STOCK_LIST=600519,300750,002594
WEBUI_ENABLED=true
WEBUI_HOST=0.0.0.0
WEBUI_PORT=8000
LOG_LEVEL=INFO
LOG_DIR=/app/logs
GEMINI_REQUEST_DELAY=2.0
GEMINI_MAX_RETRIES=5
TELEGRAM_BOT_TOKEN=你的Bot_Token
TELEGRAM_CHAT_ID=你的Chat_ID
```

**总计：13 个环境变量**

---

## 📋 配置检查清单

部署前确认：

### AI 模型配置
- [ ] `OPENAI_API_KEY` = `sk-xxx`
- [ ] `OPENAI_BASE_URL` = `https://dashscope.aliyuncs.com/compatible-mode/v1`
- [ ] `OPENAI_MODEL` = `qwen-turbo`
- [ ] `STOCK_LIST` = `600519,300750,002594`

### WebUI 配置
- [ ] `WEBUI_ENABLED` = `true`
- [ ] `WEBUI_HOST` = `0.0.0.0`
- [ ] `WEBUI_PORT` = `8000`

### Telegram 通知（可选）
- [ ] `TELEGRAM_BOT_TOKEN` = `123456789:ABCxxx`
- [ ] `TELEGRAM_CHAT_ID` = `123456789`

---

## 🚀 快速配置步骤

### 步骤 1：获取通义千问 API Key（2分钟）
1. 访问：https://dashscope.aliyuncs.com/
2. 注册/登录（阿里云账号）
3. 进入「API-KEY 管理」
4. 创建新的 API Key
5. 复制 Key（格式：`sk-xxxxx`）

### 步骤 2：获取 Telegram 配置（3分钟）
1. **创建 Bot**：
   - 打开 Telegram
   - 搜索 `@BotFather`
   - 发送 `/newbot`
   - 设置 bot 名称和用户名
   - 复制 Bot Token

2. **获取 Chat ID**：
   - 搜索 `@getidsbot`
   - 发送 `/start`
   - 复制 Chat ID

### 步骤 3：在 Zeabur 配置（2分钟）
1. 登录 Zeabur
2. 选择 `ASTOCK` 项目
3. 点击「环境变量」
4. 点击「添加变量」
5. 逐个添加上面的 13 个变量
6. 点击「保存更改」

### 步骤 4：等待自动部署
- Zeabur 自动检测 GitHub 更新
- 1-2 分钟完成部署

### 步骤 5：测试
1. 访问：`https://mystock.zeabur.app/`
2. 输入股票代码：`600519`
3. 点击「🚀 分析」
4. 检查 Telegram 是否收到通知

---

## 📱 其他通知渠道（可选）

### 企业微信
```
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的Key
```

### 飞书
```
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/你的Key
```

### 邮件
```
EMAIL_SENDER=your_email@qq.com
EMAIL_PASSWORD=your_email_auth_code
EMAIL_RECEIVERS=receiver@example.com
```

---

## ⚠️ 常见问题

### Q：Telegram 通知收不到？

**检查：**
1. Bot Token 是否正确
2. Chat ID 是否正确
3. 是否向 Bot 发送过 `/start` 命令
4. 查看 Zeabur 日志确认错误

**测试方法：**
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage" \
  -d "chat_id=<YOUR_CHAT_ID>&text=测试消息"
```

### Q：可以不配置 Telegram 吗？

**答：** 可以！Telegram 是可选的。不配置的话，分析结果只会显示在 WebUI 上，不会推送到 Telegram。

### Q：想同时配置多个通知渠道？

**答：** 可以！同时配置多个，系统会全部推送。例如：
- Telegram
- 企业微信
- 邮件

---

## 📞 需要帮助？

- **Telegram 配置指南**：`docs/telegram-guide.md`
- **Zeabur 故障排查**：`docs/zeabur-troubleshoot.md`
- **云端模型配置**：`docs/cloud-models-guide.md`
