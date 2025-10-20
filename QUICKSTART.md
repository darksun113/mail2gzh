# 快速开始指南

本文档帮助您快速启动并运行 Mail2GZH 服务。

## 前置条件检查

在开始之前，请确保您已准备好以下内容：

- [ ] Python 3.13.3 或更高版本
- [ ] MySQL 5.7+ 数据库
- [ ] Gmail API 凭据文件 (`credentials.json`)
- [ ] OpenAI API Key
- [ ] 微信公众号 AppID 和 AppSecret

## 快速安装步骤

### 1. 安装依赖（已完成）

虚拟环境和依赖已经安装完成。如果需要重新安装：

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑 .env 文件，填写您的配置
nano .env  # 或使用您喜欢的编辑器
```

**必填配置项**：

```ini
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mail2gzh
DB_USER=your_username
DB_PASSWORD=your_password

# OpenAI API
OPENAI_API_KEY=sk-xxxxxxxxxxxx

# 微信公众号
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
```

### 3. 配置 Gmail API

#### 3.1 获取 Gmail API 凭据

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 Gmail API
4. 创建 OAuth 2.0 凭据（桌面应用）
5. 下载凭据文件，重命名为 `credentials.json`
6. 将 `credentials.json` 放在项目根目录

#### 3.2 首次授权

首次运行时，系统会自动打开浏览器进行 Gmail 授权，授权成功后会生成 `token.json` 文件。

### 4. 创建数据库

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE mail2gzh CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 退出
exit;
```

### 5. 启动服务

#### 方式一：使用启动脚本（推荐）

```bash
./run.sh
```

#### 方式二：手动启动

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 方式三：Python 直接运行

```bash
source venv/bin/activate
python -m app.main
```

### 6. 验证服务

服务启动后，访问以下地址：

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health

## 快速测试

### 测试 Gmail 连接

```bash
curl -X POST "http://localhost:8000/api/v1/test/gmail"
```

### 测试微信公众号连接

```bash
curl -X POST "http://localhost:8000/api/v1/test/wechat"
```

### 同步邮件

```bash
curl -X POST "http://localhost:8000/api/v1/emails/sync?max_results=5"
```

### 查看邮件列表

```bash
curl "http://localhost:8000/api/v1/emails"
```

### 翻译邮件

```bash
curl -X POST "http://localhost:8000/api/v1/emails/1/translate"
```

### 发布到微信公众号

```bash
curl -X POST "http://localhost:8000/api/v1/emails/1/publish"
```

### 自动处理工作流

一键完成同步、翻译和发布：

```bash
curl -X POST "http://localhost:8000/api/v1/workflow/auto-process?max_emails=3"
```

## 使用 Web 界面

启动服务后，打开浏览器访问 http://localhost:8000/docs

这是 FastAPI 自动生成的 Swagger UI 界面，您可以：

1. 查看所有 API 端点
2. 直接在网页上测试 API
3. 查看请求和响应的数据结构

## 常见问题

### Q1: 服务启动失败？

检查：
- 虚拟环境是否激活
- 环境变量是否正确配置
- MySQL 服务是否运行
- 端口 8000 是否被占用

### Q2: Gmail API 认证失败？

检查：
- `credentials.json` 是否存在
- Gmail API 是否在 Google Cloud Console 中启用
- OAuth 2.0 凭据类型是否为"桌面应用"

### Q3: 数据库连接失败？

检查：
- MySQL 服务是否运行：`mysql.server status`
- 数据库名称、用户名、密码是否正确
- 数据库是否已创建

### Q4: OpenAI API 调用失败？

检查：
- API Key 是否有效
- 账户是否有余额
- 网络连接是否正常

## 下一步

1. 查看完整文档：[README.md](README.md)
2. 了解 API 详情：http://localhost:8000/docs
3. 查看变更日志：[CHANGELOG.md](CHANGELOG.md)
4. 配置定时任务以自动处理邮件

## 获取帮助

如遇到问题，请：

1. 检查日志文件：`logs/app.log`
2. 查看 API 响应的错误信息
3. 提交 Issue 到项目仓库

---

祝使用愉快！🎉
