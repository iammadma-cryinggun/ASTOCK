# Zeabur 部署快速配置指南

## 📋 必须配置的环境变量（最少 6 个）

在 Zeabur 控制台的「环境变量」页面，逐个添加以下变量：

### 1. WebUI 配置（3 个）

```
WEBUI_ENABLED=true
WEBUI_HOST=0.0.0.0
WEBUI_PORT=8000
```

### 2. AI 模型配置（3 个）

```
OPENAI_API_KEY=sk-你的通义千问API密钥
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-turbo
```

---

## 🚀 部署步骤

### 步骤 1: 登录 Zeabur
访问: https://zeabur.com/

### 步骤 2: 选择项目
点击 `ASTOCK` 项目

### 步骤 3: 配置环境变量
1. 点击服务名称
2. 点击「环境变量」标签
3. 点击「添加变量」
4. 逐个添加上面的 6 个变量
5. 点击「保存更改」

### 步骤 4: 重新部署
点击「重新部署」按钮，等待 2-3 分钟

### 步骤 5: 检查状态
- 部署状态应该是绿色 (Running)
- 端口应该显示 8080

### 步骤 6: 访问测试
打开浏览器访问: https://mystock.zeabur.app/

---

## 🔍 故障排查

### 如果网页打不开

**1. 查看日志（在网页上直接看）**
- 在 Zeabur 控制台
- 点击「日志」标签
- 查看最新的输出

**2. 检查环境变量**
确认 6 个变量都已配置并保存

**3. 检查端口**
确认 Zeabur 显示的端口是 `8080`

---

## 📱 如何获取通义千问 API Key

1. 访问: https://dashscope.aliyuncs.com/
2. 登录阿里云账号
3. 进入「API-KEY 管理」
4. 创建新的 API Key
5. 复制 Key（以 sk- 开头）

---

## ✅ 成功的标志

当你访问 https://mystock.zeabur.app/ 时，应该看到：

- 股票代码输入框
- "🚀 分析" 按钮
- "📊 期货监控" 链接
- "📜 历史记录" 链接
- 自选股配置区域
