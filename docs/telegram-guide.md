# 📱 Telegram 通知配置指南

本指南将帮助你配置 Telegram Bot 来接收股票分析通知。

## 🎯 功能概述

Telegram Bot 通知功能可以让你：
- 接收股票分析结果的实时推送
- 查看决策仪表盘和详细分析
- 支持完整的 Markdown 格式消息
- 长消息自动分片发送

## 📋 准备工作

### 第一步：创建 Telegram Bot

1. 在 Telegram 中搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 命令
3. 按提示输入你的机器人名称（例如：`MyStockBot`）
4. 按提示输入用户名（必须以 `bot` 结尾，例如：`mystock_analysis_bot`）
5. 保存返回的 **Bot Token**（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

**示例：**
```
BotFather: Congratulations! Your bot is created.
Bot Token: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 第二步：获取 Chat ID

有两种方式获取 Chat ID：

#### 方法 1：使用 getidsbot（推荐）

1. 在 Telegram 中搜索 [@getidsbot](https://t.me/getidsbot)
2. 发送 `/start` 命令
3. 机器人会返回你的 **Chat ID**（纯数字，例如：`123456789`）

#### 方法 2：通过 API 测试

1. 在浏览器中访问：
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   将 `<YOUR_BOT_TOKEN>` 替换为你的 Bot Token

2. 向你的 Bot 发送任意消息（如 `/start`）

3. 刷新浏览器页面，会看到类似以下内容：
   ```json
   {
     "message": {
       "chat": {
         "id": 123456789,
         "first_name": "Your Name"
       }
     }
   }
   ```
   这里的 `id` 就是你的 **Chat ID**

## ⚙️ 配置方式

### 方式 1：环境变量配置（推荐）

在 `.env` 文件中添加：

```bash
# Telegram Bot 配置
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### 方式 2：Zeabur 部署配置

在 Zeabur 控制台的「环境变量」中添加：

| 变量名 | 值 | 说明 |
|--------|----|----- |
| `TELEGRAM_BOT_TOKEN` | `你的Bot Token` | 从 @BotFather 获取 |
| `TELEGRAM_CHAT_ID` | `你的Chat ID` | 纯数字 |

### 方式 3：GitHub Actions 配置

在 GitHub 仓库的 Settings → Secrets and variables → Actions 中添加：

| Secret 名称 | 值 | 必填 |
|------------|----|:----:|
| `TELEGRAM_BOT_TOKEN` | 你的 Bot Token | ✅ |
| `TELEGRAM_CHAT_ID` | 你的 Chat ID | ✅ |

## 🧪 测试配置

### 方法 1：使用 Python 脚本测试

创建测试脚本 `test_telegram.py`：

```python
import requests

# 配置信息
BOT_TOKEN = "你的Bot Token"
CHAT_ID = "你的Chat ID"
MESSAGE = "📊 测试消息：股票分析系统已连接！"

# 发送消息
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
data = {
    "chat_id": CHAT_ID,
    "text": MESSAGE,
    "parse_mode": "Markdown"
}

response = requests.post(url, json=data)
print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}")
```

运行测试：
```bash
python test_telegram.py
```

如果配置正确，你的 Telegram 会收到测试消息。

### 方法 2：使用 curl 测试

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "<YOUR_CHAT_ID>",
    "text": "📊 测试消息：股票分析系统已连接！",
    "parse_mode": "Markdown"
  }'
```

## 📨 消息格式示例

配置完成后，你将收到类似以下格式的分析报告：

```
📊 2026-01-10 决策仪表盘
3只股票 | 🟢买入:1 🟡观望:2 🔴卖出:0

🟢 买入 | 贵州茅台(600519)
📌 缩量回踩MA5支撑，乖离率1.2%处于最佳买点
💰 狙击: 买入1800 | 止损1750 | 目标1900
✅多头排列 ✅乖离安全 ✅量能配合
```

## 🔧 常见问题

### 问题 1：没有收到消息

**可能原因：**
- Chat ID 填写错误
- Bot Token 填写错误
- 网络连接问题

**解决方法：**
1. 检查 `.env` 文件中的配置是否正确
2. 使用测试脚本验证配置
3. 查看日志文件确认错误信息

### 问题 2：Chat ID 获取失败

**解决方法：**
1. 确保已向 Bot 发送过 `/start` 命令
2. 使用 getidsbot 获取 Chat ID（最简单）
3. 检查 API 请求的返回值

### 问题 3：消息格式显示异常

**解决方法：**
- 系统会自动处理 Markdown 格式
- 长消息会自动分片发送
- 如果仍有问题，请查看日志

## 📚 相关链接

- [BotFather](https://t.me/BotFather) - 创建和管理 Bot
- [getidsbot](https://t.me/getidsbot) - 获取 Chat ID
- [Telegram Bot API](https://core.telegram.org/bots/api) - 官方文档
- [Telegram Bot 消息格式](https://core.telegram.org/bots/api#formatting-options) - Markdown 格式说明

## ⚠️ 安全提示

1. **不要泄露 Bot Token 和 Chat ID**
   - 这些信息相当于你的密码
   - 不要提交到公开的 Git 仓库

2. **使用环境变量**
   - 始终使用 `.env` 文件或环境变量存储敏感信息
   - 确保 `.env` 文件已添加到 `.gitignore`

3. **定期更换 Bot Token**
   - 如果怀疑 Token 泄露，立即在 BotFather 中撤销并重新生成

## 🎉 配置完成！

完成以上配置后，你的股票分析系统就可以通过 Telegram Bot 发送通知了！

每次分析完成后，系统会自动推送：
- 📊 决策仪表盘
- 📈 大盘复盘
- 🎯 操作建议
- ⚠️ 风险提示

---

如有问题，请查看：
- 项目 GitHub Issues
- 日志文件：`./logs/stock_analysis_*.log`
