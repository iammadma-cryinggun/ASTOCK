# 🌟 Zeabur 云端部署指南

## 📋 部署准备清单

✅ **已完成：**
- 代码已推送到 `https://github.com/iammadma-cryinggun/ASTOCK`
- GitHub Actions 自动构建已配置

🔄 **需要你操作：**
- 在 Zeabur 连接 GitHub 仓库
- 配置环境变量
- 设置域名

---

## 🚀 Zeabur 部署步骤

### 第一步：连接 Zeabur

1. **访问 Zeabur**: https://zeabur.com
2. **登录/注册**（建议使用 GitHub 账号登录）
3. **创建新项目** → **从 GitHub 导入**
4. **选择仓库**: `iammadma-cryinggun/ASTOCK`
5. **选择分支**: `main`
6. **点击导入**

### 第二步：配置服务

1. **等待构建**：Zeabur 会自动检测 Dockerfile 并构建镜像
2. **配置启动命令**：
   ```
   python main.py --webui
   ```
3. **配置端口**：`8000`
4. **启动服务**

### 第三步：配置环境变量

在 Zeabur 控制台的「环境变量」中添加：

| 变量名 | 值 | 说明 |
|--------|----|----- |
| `GEMINI_API_KEY` | `AIzaSyDTQw32SgbY-_IZp5CHPieWCQ72fI3ijGk` | Gemini API 密钥 |
| `OPENAI_API_KEY` | `sk-342a63b3a5da48cea6df443341242bac` | OpenAI API 密钥 |
| `OPENAI_BASE_URL` | `https://api.deepseek.com/v1` | DeepSeek API 地址 |
| `OPENAI_MODEL` | `deepseek-chat` | DeepSeek 模型 |
| `STOCK_LIST` | `600519,300750,002594` | 股票列表（可修改） |
| `WEBUI_ENABLED` | `true` | 启用 WebUI |
| `WEBUI_HOST` | `0.0.0.0` | WebUI 监听地址 |
| `WEBUI_PORT` | `8000` | WebUI 端口 |

### 第四步：配置域名

#### 选项1：使用 Zeabur 自动域名
1. 在服务页面点击「访问」标签
2. 复制 Zeabur 提供的域名（如：stock-analyzer.zeabur.app）

#### 选项2：绑定自定义域名（推荐）
1. 在域名提供商添加 CNAME 记录：
   ```
   记录类型: CNAME
   主机记录: stock（或你想要的子域名）
   记录值: stock-analyzer.zeabur.app（或其他 Zeabur 域名）
   ```
2. 在 Zeabur 控制台：
   - 点击「访问」→「添加域名」
   - 输入你的域名（如：stock.yourdomain.com）
   - 等待 SSL 证书自动生成

---

## 🎯 快速部署命令

### 如果你想要不同的运行模式：

| 模式 | 启动命令 | 说明 |
|------|----------|------|
| **WebUI + 定时任务** | `python main.py --webui` | 推荐配置 |
| **仅 WebUI** | `python main.py --webui-only` | 仅管理界面 |
| **仅定时任务** | `python main.py --schedule` | 后台自动运行 |
| **调试模式** | `python main.py --webui --debug` | 开发调试 |

---

## 🌐 域名配置详解

### 推荐域名配置方案：

#### 方案1：子域名部署
```
stock.yourdomain.com  →  股票分析系统
```

#### 方案2：独立域名
```
your-stock-domain.com  →  股票分析系统
```

### 域名解析配置：

1. **登录域名管理后台**
2. **添加 CNAME 记录**：
   ```
   类型: CNAME
   主机记录: stock
   记录值: [Zeabur 提供的域名]
   TTL: 600（或默认值）
   ```

3. **等待解析生效**（通常 1-10 分钟）

---

## 📱 访问测试

部署完成后，你可以：

1. **访问 WebUI**: `https://你的域名`
2. **健康检查**: `https://你的域名/health`
3. **查看任务**: `https://你的域名/tasks`

---

## 🔧 常见问题解决

### 问题1：WebUI 无法访问
- 检查启动命令是否包含 `--webui`
- 检查环境变量 `WEBUI_ENABLED=true`
- 检查端口 8000 是否正确配置

### 问题2：分析功能不工作
- 检查 API 密钥是否正确配置
- 查看服务日志排查错误

### 问题3：域名无法访问
- 检查 DNS 解析是否生效
- 等待 SSL 证书生成
- 检查 Zeabur 域名绑定配置

---

## 🎉 部署完成！

你的股票分析系统现在已经运行在云端，可以通过域名从任何地方访问！

### 下一步建议：
1. **配置通知渠道**（企业微信、邮件等）
2. **自定义股票列表**
3. **设置定时分析时间**
4. **备份数据**（定期下载 `/app/data` 目录）

---

## 📞 技术支持

如果在部署过程中遇到问题：
1. 查看 Zeabur 服务日志
2. 检查 GitHub Actions 构建状态
3. 参考项目文档：`docs/docker/zeabur-deployment.md`