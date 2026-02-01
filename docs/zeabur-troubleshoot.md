# 🔧 Zeabur 完整配置指南

## ⚠️ 问题诊断：网页无法访问

### 常见原因：
1. ❌ 启动命令错误
2. ❌ 端口未暴露
3. ❌ WebUI 未启用
4. ❌ API 配置错误导致程序崩溃

---

## ✅ Zeabur 完整配置清单

### 📋 第一步：在 Zeabur 配置环境变量

在 Zeabur 项目的「环境变量」页面，**逐行添加**以下变量：

#### 必填配置

```
OPENAI_API_KEY=sk-你的通义千问Key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-turbo
STOCK_LIST=600519,300750,002594
```

#### WebUI 配置（重要！）

```
WEBUI_ENABLED=true
WEBUI_HOST=0.0.0.0
WEBUI_PORT=8000
```

#### 日志配置（可选，推荐）

```
LOG_LEVEL=INFO
LOG_DIR=/app/logs
```

#### 完整列表（直接复制）

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

### 🚀 第二步：配置启动命令

**在 Zeabur 的「启动命令」中填入：**

```
python main.py --webui
```

**不要使用：**
- ❌ `python main.py --schedule`（定时任务模式，没有网页）
- ❌ `python main.py --webui-only`（仅WebUI，不分析）
- ❌ `python main.py`（默认是定时任务）

---

### 🌐 第三步：配置端口

**在 Zeabur 的「端口设置」中：**

- **端口**：`8000`
- **协议**：`TCP`

或者如果 Zeabur 自动检测，确保显示的是 `8000`

---

### 🔍 第四步：检查部署状态

#### 1. 查看部署日志

在 Zeabur 控制台：
1. 点击你的服务
2. 查看「日志」标签
3. 检查是否有错误

**正常启动应该看到：**
```
A股自选股智能分析系统 启动
日志系统初始化完成
WebUI running: http://0.0.0.0:8000
```

**如果看到错误：**
```
KeyError: OPENAI_API_KEY
# → 检查环境变量是否正确配置

ModuleNotFoundError: No module named 'xxx'
# → 联系我，需要修复依赖

Error: 401 / 402
# → API Key 无效或余额不足
```

#### 2. 测试访问

访问：`https://mystock.zeabur.app/`

**正常情况：** 看到网页界面，包含：
- 股票代码输入框
- "🚀 分析" 按钮
- 任务列表
- 配置区域

**如果还是无法访问：**

1. **检查启动命令** - 确认是 `python main.py --webui`
2. **检查端口** - 确认暴露了 8000 端口
3. **查看日志** - 确认服务正常启动
4. **重新部署** - 在 Zeabur 点击「重新部署」

---

## 🎯 快速修复清单

### 检查项 1：启动命令

✅ 正确：`python main.py --webui`
❌ 错误：`python main.py --schedule`

### 检查项 2：环境变量

✅ 必须配置：
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `STOCK_LIST`

### 检查项 3：WebUI 配置

✅ 必须配置：
- `WEBUI_ENABLED=true`
- `WEBUI_HOST=0.0.0.0`
- `WEBUI_PORT=8000`

### 检查项 4：端口

✅ 端口：`8000`

---

## 📝 完整配置截图指南

### Zeabur 配置步骤：

1. **打开项目设置**
   - 登录 Zeabur
   - 选择你的项目 `ASTOCK`
   - 点击服务名称

2. **配置环境变量**
   ```
   点击「环境变量」标签
   点击「添加变量」
   逐个添加上面的环境变量
   点击「保存更改」
   ```

3. **配置启动命令**
   ```
   找到「启动命令」或「Command」
   填入：python main.py --webui
   点击「保存」
   ```

4. **配置端口**
   ```
   找到「端口」或「Ports」
   添加：8000
   点击「保存」
   ```

5. **重新部署**
   ```
   点击「重新部署」按钮
   等待部署完成（约1-2分钟）
   ```

6. **测试访问**
   ```
   访问：https://mystock.zeabur.app/
   应该能看到网页界面
   ```

---

## 🆘 如果还是无法访问

### 方案 1：查看实时日志

在 Zeabur 控制台：
1. 点击服务
2. 点击「日志」
3. 查看最新日志
4. 截图发给我

### 方案 2：使用命令行测试

在 Zeabur 的「控制台」中执行：
```bash
curl http://localhost:8000/health
```

**正常返回：**
```json
{"status": "ok", "timestamp": "...", "service": "stock-analysis-webui"}
```

### 方案 3：检查健康检查

访问：`https://mystock.zeabur.app/health`

**正常返回：**
```json
{"status": "ok"}
```

**如果返回 404/502**：
- → 启动命令错误
- → 服务未正常启动

---

## 📞 需要帮助？

如果按照以上配置还是无法访问，请提供：

1. **Zeabur 日志截图**（最近 50 行）
2. **启动命令**（你配置的）
3. **环境变量列表**（可以隐藏 API Key）
4. **端口配置**

我会帮你诊断问题！

---

## ✅ 配置验证清单

部署后，依次访问以下 URL 验证：

- [ ] `https://mystock.zeabur.app/` - 主页
- [ ] `https://mystock.zeabur.app/health` - 健康检查
- [ ] `https://mystock.zeabur.app/history` - 历史记录

全部能访问 = 配置成功！
