# 🚀 Zeabur 完整配置清单（8080 端口版）

## 📌 重要说明

**Zeabur 端口映射：**
- 对外访问端口：`8080`（HTTPS）
- 容器内部端口：`8000`
- Zeabur 自动处理端口映射，无需额外配置

---

## ✅ 必须配置的 13 个环境变量

### 在 Zeabur 的「环境变量」中逐个添加：

#### 1️⃣ AI 模型配置（11个）

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

#### 2️⃣ Telegram 通知配置（2个）

```
TELEGRAM_BOT_TOKEN=你的Bot_Token
TELEGRAM_CHAT_ID=你的Chat_ID
```

---

## 🎯 完整配置（直接复制）

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

---

## 📋 配置步骤（Zeabur）

### 步骤 1：登录 Zeabur

访问：https://zeabur.com/
登录并选择 `ASTOCK` 项目

### 步骤 2：配置环境变量

1. **点击服务** → 进入服务详情页
2. **点击「环境变量」标签**
3. **点击「添加变量」按钮**
4. **逐个添加**上面的 13 个变量
5. **点击「保存更改」**

**注意：**
- ⚠️ `WEBUI_PORT=8000` 不要改成 8080（这是容器内部端口）
- ⚠️ 每个变量都要单独添加，不要一次粘贴多个

### 步骤 3：确认端口设置

在 Zeabur 服务页面确认：
- **端口**：`8080`（Zeabur 自动配置）
- **类型**：`HTTP`

### 步骤 4：等待自动部署

- Zeabur 会自动检测 GitHub 更新
- 约 1-2 分钟完成部署
- 可以在「部署」标签查看进度

### 步骤 5：测试访问

打开浏览器访问：`https://mystock.zeabur.app/`

**应该看到：**
- 股票代码输入框
- "🚀 分析" 按钮
- 任务列表区域
- 自选股配置区域

---

## 🔍 端口说明

### 端口映射关系

```
外部访问 → Zeabur (8080) → 容器内部 (8000)
```

| 层级 | 端口 | 说明 |
|------|------|------|
| 对外 | `8080` | Zeabur 暴露的端口 |
| 容器内 | `8000` | 应用实际运行端口 |
| 配置 | `WEBUI_PORT=8000` | 不要修改 |

### 访问 URL

- ✅ `https://mystock.zeabur.app/` - 主页
- ✅ `https://mystock.zeabur.app/health` - 健康检查
- ✅ `https://mystock.zeabur.app/history` - 历史记录

---

## 📱 Telegram 配置获取

### 获取 Bot Token（2分钟）

1. 打开 Telegram
2. 搜索 `@BotFather`
3. 发送 `/newbot`
4. 按提示设置 Bot 名称
5. 复制 Bot Token（格式：`123456789:ABCxxx`）

### 获取 Chat ID（1分钟）

**方法 1：使用 getidsbot（推荐）**
1. 搜索 `@getidsbot`
2. 发送 `/start`
3. 复制返回的 Chat ID

**方法 2：使用 API**
1. 访问：`https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
2. 向你的 Bot 发送任意消息
3. 刷新页面，找到 `"chat":{"id":123456789}`
4. 复制 ID

---

## ✅ 配置检查清单

部署前确认：

### AI 模型配置
- [ ] `OPENAI_API_KEY` - 通义千问 API Key
- [ ] `OPENAI_BASE_URL` - `https://dashscope.aliyuncs.com/compatible-mode/v1`
- [ ] `OPENAI_MODEL` - `qwen-turbo`
- [ ] `STOCK_LIST` - `600519,300750,002594`

### WebUI 配置
- [ ] `WEBUI_ENABLED` - `true`
- [ ] `WEBUI_HOST` - `0.0.0.0`
- [ ] `WEBUI_PORT` - `8000`（容器内部端口，不要改）

### Telegram 通知（可选）
- [ ] `TELEGRAM_BOT_TOKEN` - 你的 Bot Token
- [ ] `TELEGRAM_CHAT_ID` - 你的 Chat ID

### 端口确认
- [ ] Zeabur 显示端口为 `8080`

---

## 🧪 测试步骤

### 1. 测试网页访问

访问：`https://mystock.zeabur.app/`

**预期结果：** 能看到网页界面

### 2. 测试健康检查

访问：`https://mystock.zeabur.app/health`

**预期返回：**
```json
{"status": "ok"}
```

### 3. 测试分析功能

1. 在网页输入股票代码：`600519`
2. 点击 "🚀 分析"
3. 等待 30 秒左右
4. 检查 Telegram 是否收到通知

---

## 🆘 故障排查

### 问题 1：网页无法访问

**检查：**
1. Zeabur 部署状态是否成功
2. 环境变量是否全部配置
3. 查看服务日志是否有错误

**解决：**
- 查看日志：Zeabur 控制台 → 服务 → 日志
- 重新部署：点击「重新部署」按钮

### 问题 2：Telegram 没有通知

**检查：**
1. Bot Token 是否正确
2. Chat ID 是否正确
3. 是否向 Bot 发送过 `/start`

**测试：**
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=<CHAT_ID>&text=测试"
```

### 问题 3：环境变量配置后不生效

**解决：**
1. 确认点击了「保存更改」
2. 在 Zeabur 触发重新部署
3. 等待 1-2 分钟部署完成

---

## 📊 配置示例截图

### Zeabur 环境变量配置示例

```
环境变量列表（13个）：

OPENAI_API_KEY          sk-xxxxxxxxxxxxxx
OPENAI_BASE_URL         https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL            qwen-turbo
OPENAI_TEMPERATURE      0.7
STOCK_LIST              600519,300750,002594
WEBUI_ENABLED           true
WEBUI_HOST              0.0.0.0
WEBUI_PORT              8000
LOG_LEVEL               INFO
LOG_DIR                 /app/logs
GEMINI_REQUEST_DELAY    2.0
GEMINI_MAX_RETRIES      5
TELEGRAM_BOT_TOKEN      123456789:ABCxxx
TELEGRAM_CHAT_ID        123456789
```

---

## 📚 相关文档

| 文档 | 路径 |
|------|------|
| Telegram 配置指南 | `docs/telegram-guide.md` |
| 云端模型配置指南 | `docs/cloud-models-guide.md` |
| 环境变量配置清单 | `ENV_CONFIG_GUIDE.md` |

---

## ⚠️ 重要提示

1. **端口配置**
   - Zeabur 端口：`8080`（自动配置，无需修改）
   - 容器端口：`8000`（环境变量中配置）
   - 不要把 `WEBUI_PORT` 改成 8080

2. **环境变量格式**
   - 每个变量单独添加
   - 不要有多余空格
   - API Key 不要有引号

3. **部署后等待**
   - 配置完成后需要重新部署
   - 等待 1-2 分钟部署完成
   - 完成后再测试访问

---

## 🎉 配置完成！

配置完成后：
1. ✅ 访问 `https://mystock.zeabur.app/`
2. ✅ 输入股票代码测试
3. ✅ 检查 Telegram 通知
4. ✅ 查看历史记录

**如有问题，查看 Zeabur 日志或联系我！**
