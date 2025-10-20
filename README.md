# Mail2GZH - Gmail 到微信公众号邮件转发服务

这是一个基于 FastAPI 的 Web 服务，用于自动读取 Gmail 邮件、使用 OpenAI 翻译成中文，并发布到微信公众号平台。

## 功能特性

- 📧 **Gmail 集成**: 自动读取 Gmail 指定收件箱的订阅邮件，支持高级搜索过滤
- 🤖 **AI 智能翻译**: 使用 GPT-5 模型将邮件翻译成中文，生成符合微信公众号规范的 HTML
- 🖼️ **图片处理**: 自动下载并重新上传图片到微信公众号平台
- 📱 **微信发布**: 自动发布翻译后的内容到微信公众号
- 💾 **数据缓存**: 使用 MySQL 数据库缓存邮件和翻译内容
- 🔄 **自动化工作流**: 支持自动同步、翻译和发布的完整流程
- ⏰ **定时任务**: 每日 UTC 0 时自动处理邮件，支持手动触发
- 🛡️ **RESTful API**: 提供完整的 API 接口，易于集成和扩展
- 🐳 **容器化部署**: 支持 Docker 和 Docker Compose 部署
- 📊 **日志系统**: 完整的日志记录和监控
- 🔍 **内容验证**: 自动验证翻译内容长度和格式，确保符合微信规范

## 技术栈

- **Web 框架**: FastAPI + Uvicorn
- **数据库**: MySQL + SQLAlchemy (同步模式)
- **Gmail API**: google-api-python-client
- **翻译服务**: OpenAI API
- **微信公众号**: HTTP API
- **日志**: Loguru
- **环境变量**: python-dotenv

## 系统要求

- Python 3.13.3+
- MySQL 5.7+
- Gmail API 凭据
- OpenAI API Key
- 微信公众号账号

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd mail2gzh
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `env.example` 到 `.env` 并填写配置：

```bash
cp env.example .env
```

编辑 `.env` 文件，填写以下关键配置：

```ini
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mail2gzh
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password

# Gmail API 配置
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json

# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key

# 微信公众号配置
WECHAT_APP_ID=your_wechat_app_id
WECHAT_APP_SECRET=your_wechat_app_secret
```

### 5. 配置 Gmail API（服务账号）

#### 5.1 创建服务账号

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 Gmail API
4. 进入 "IAM 和管理" > "服务账号"
5. 点击 "创建服务账号"
6. 填写服务账号名称和描述
7. 点击 "创建并继续"

#### 5.2 配置域范围委派（重要）

1. 在服务账号列表中，点击刚创建的服务账号
2. 切换到 "详细信息" 标签
3. 点击 "显示域范围委派"
4. 点击 "添加密钥" > "创建新密钥"
5. 选择 "JSON" 格式，下载密钥文件
6. 将密钥文件重命名为 `service-account-key.json` 并放在项目根目录

#### 5.3 启用域范围委派

1. 在服务账号的 "详细信息" 页面
2. 点击 "显示域范围委派"
3. 点击 "添加域范围委派"
4. 填写以下信息：
   - **产品名称**: `Mail2GZH`
   - **主域**: 您的 Gmail 域名（如 `gmail.com`）
   - **范围**: `https://www.googleapis.com/auth/gmail.readonly`
5. 点击 "授权"

#### 5.4 配置环境变量

在 `.env` 文件中设置：

```bash
# Gmail 服务账号配置
GMAIL_CREDENTIALS_FILE=service-account-key.json
GMAIL_SUBJECT_EMAIL=your-email@gmail.com  # 要访问的邮箱地址
GMAIL_QUERY=is:unread label:inbox
```

**注意**：
- 服务账号只能访问自己的 Gmail 数据
- 如果使用 G Suite/Google Workspace，可以访问组织内的任何邮箱
- 个人 Gmail 账户需要特殊配置才能使用服务账号

#### Gmail 查询条件配置

在 `.env` 文件中配置 `GMAIL_QUERY` 参数来筛选邮件：

```bash
# 基本查询示例
GMAIL_QUERY=is:unread label:inbox

# 按主题筛选
GMAIL_QUERY=is:unread subject:newsletter

# 按发件人筛选
GMAIL_QUERY=is:unread from:example@gmail.com

# 按标签筛选
GMAIL_QUERY=is:unread label:important

# 按时间筛选
GMAIL_QUERY=is:unread newer_than:7d

# 组合条件
GMAIL_QUERY=is:unread label:inbox subject:newsletter from:example@gmail.com

# 排除特定邮件
GMAIL_QUERY=is:unread -from:noreply@example.com

# 搜索特定文件夹（标签）
GMAIL_QUERY=is:unread label:inbox OR label:important
```

**常用查询操作符：**
- `is:unread` - 未读邮件
- `is:read` - 已读邮件
- `from:email@example.com` - 特定发件人
- `to:email@example.com` - 特定收件人
- `subject:关键词` - 主题包含关键词
- `label:标签名` - 特定标签/文件夹
- `newer_than:7d` - 7天内的邮件
- `older_than:30d` - 30天前的邮件
- `has:attachment` - 包含附件
- `-关键词` - 排除包含关键词的邮件

### 6. 创建数据库

```bash
mysql -u root -p
CREATE DATABASE mail2gzh CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 7. 启动服务

#### 方式一：使用启动脚本（推荐）

```bash
# 启动 Web 服务 + 定时任务
./run.sh

# 或仅启动定时任务服务
python run_scheduler.py
```

#### 方式二：手动启动

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动 Web 服务 + 定时任务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或仅启动定时任务服务
python run_scheduler.py
```

#### 方式三：Docker 部署

```bash
# 使用 Docker Compose 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mail2gzh
```

服务将在 `http://localhost:8000` 启动。

## API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 主要 API 端点

### 邮件管理

- `POST /api/v1/emails/sync` - 同步 Gmail 邮件到数据库
- `GET /api/v1/emails` - 获取邮件列表
- `GET /api/v1/emails/{email_id}` - 获取单个邮件详情
- `POST /api/v1/emails/{email_id}/translate` - 翻译邮件内容
- `POST /api/v1/emails/{email_id}/publish` - 发布邮件到微信公众号

### 工作流

- `POST /api/v1/workflow/auto-process` - 自动处理邮件（同步、翻译、发布）

### 测试连接

- `POST /api/v1/test/gmail` - 测试 Gmail API 连接
- `POST /api/v1/test/wechat` - 测试微信公众号 API 连接

### 定时任务管理

- `GET /api/v1/scheduler/status` - 获取定时任务调度器状态
- `POST /api/v1/scheduler/trigger/daily` - 手动触发每日邮件处理任务
- `POST /api/v1/scheduler/trigger/check` - 手动触发检查待处理邮件任务
- `GET /api/v1/scheduler/logs` - 获取调度器日志

## 使用示例

### 1. 同步邮件

```bash
curl -X POST "http://localhost:8000/api/v1/emails/sync?max_results=10"
```

### 2. 翻译邮件

```bash
curl -X POST "http://localhost:8000/api/v1/emails/1/translate"
```

### 3. 批量翻译邮件

```bash
curl -X POST "http://localhost:8000/api/v1/emails/batch-translate?max_emails=5"
```

### 4. 处理邮件图片

```bash
curl -X POST "http://localhost:8000/api/v1/emails/1/process-images"
```

### 5. 预览微信内容

```bash
curl "http://localhost:8000/api/v1/emails/1/preview"
```

### 6. 发布到微信公众号

```bash
curl -X POST "http://localhost:8000/api/v1/emails/1/publish"
```

### 7. 自动处理工作流

```bash
curl -X POST "http://localhost:8000/api/v1/workflow/auto-process?max_emails=5"
```

### 8. 定时任务管理

查看定时任务状态：

```bash
curl "http://localhost:8000/api/v1/scheduler/status"
```

手动触发每日任务：

```bash
curl -X POST "http://localhost:8000/api/v1/scheduler/trigger/daily"
```

查看调度器日志：

```bash
curl "http://localhost:8000/api/v1/scheduler/logs?lines=100"
```

## 项目结构

```
mail2gzh/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── scheduler.py         # 定时任务调度器
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   └── email.py         # 邮件数据模型
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── gmail_service.py      # Gmail API 服务
│   │   ├── translation_service.py # OpenAI 翻译服务
│   │   └── wechat_service.py     # 微信公众号服务
│   ├── routes/              # API 路由
│   │   ├── __init__.py
│   │   └── api.py           # API 端点
│   └── schemas/             # Pydantic schemas
│       ├── __init__.py
│       └── email.py         # 邮件 schema
├── venv/                    # 虚拟环境
├── logs/                    # 日志目录
├── env.example              # 环境变量模板
├── .gitignore              # Git 忽略文件
├── requirements.txt         # Python 依赖
├── run.sh                  # 启动脚本
├── run_scheduler.py        # 定时任务启动脚本
├── Dockerfile              # Docker 配置
├── docker-compose.yml      # Docker Compose 配置
├── mail2gzh.service        # Systemd 服务配置
├── README.md               # 项目说明
├── CHANGELOG.md            # 变更日志
├── QUICKSTART.md           # 快速开始指南
├── PROJECT_SUMMARY.md      # 项目总结
└── LICENSE                 # 开源协议
```

## 开发指南

### 运行测试

```bash
# TODO: 添加测试
pytest
```

### 代码格式化

```bash
# 使用 black 格式化代码
black app/

# 使用 isort 排序导入
isort app/
```

## 常见问题

### Q: Gmail API 认证失败？
A: 确保 `credentials.json` 文件存在且有效，首次运行时会打开浏览器进行授权。

### Q: OpenAI API 限流？
A: 可以调整 `OPENAI_MAX_TOKENS` 和翻译频率，或升级 API 计划。

### Q: 微信公众号发布失败？
A: 检查 AppID 和 AppSecret 是否正确，确认公众号有群发权限。

### Q: 数据库连接失败？
A: 检查 MySQL 服务是否运行，数据库配置是否正确。

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 作者

- 项目维护者：[Your Name]

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [Google Gmail API](https://developers.google.com/gmail/api)
- [OpenAI](https://openai.com/)
- [微信公众平台](https://mp.weixin.qq.com/)

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。
