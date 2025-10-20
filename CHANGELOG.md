# 变更日志

本文档记录项目的所有重要变更。

## [1.0.0] - 2025-10-20

### 新增

- ✨ 初始项目框架搭建
- 📧 Gmail API 集成，支持读取指定收件箱邮件
- 🌐 OpenAI API 集成，支持邮件内容翻译（英文到中文）
- 📱 微信公众号 API 集成，支持图文消息发布
- 💾 MySQL 数据库集成，使用 SQLAlchemy ORM
- 🔄 自动化工作流，支持邮件同步、翻译、发布的完整流程
- ⏰ 定时任务调度器，每日 UTC 0 时自动处理邮件
- 🛡️ RESTful API 设计，提供完整的接口文档
- 📝 日志系统，使用 Loguru 进行日志记录
- ⚙️ 环境变量配置管理，使用 pydantic-settings
- 🐳 Docker 容器化支持，包含 Dockerfile 和 docker-compose.yml
- 🔧 系统服务配置，支持 systemd 部署
- 📚 完整的项目文档和部署指南

### API 端点

- `GET /` - 根路径
- `GET /api/v1/` - API 根路径
- `GET /api/v1/health` - 健康检查
- `POST /api/v1/emails/sync` - 同步 Gmail 邮件
- `GET /api/v1/emails` - 获取邮件列表
- `GET /api/v1/emails/{email_id}` - 获取邮件详情
- `POST /api/v1/emails/{email_id}/translate` - 翻译邮件
- `POST /api/v1/emails/{email_id}/publish` - 发布邮件到微信公众号
- `POST /api/v1/workflow/auto-process` - 自动处理邮件工作流
- `POST /api/v1/test/gmail` - 测试 Gmail 连接
- `POST /api/v1/test/wechat` - 测试微信公众号连接
- `GET /api/v1/scheduler/status` - 获取定时任务调度器状态
- `POST /api/v1/scheduler/trigger/daily` - 手动触发每日邮件处理任务
- `POST /api/v1/scheduler/trigger/check` - 手动触发检查待处理邮件任务
- `GET /api/v1/scheduler/logs` - 获取调度器日志

### 数据模型

- Email 模型：存储邮件原始内容和翻译后的内容
  - gmail_id: Gmail 邮件 ID
  - subject: 邮件主题
  - sender: 发件人
  - recipient: 收件人
  - content: 原始邮件内容
  - translated_content: 翻译后的内容
  - html_content: HTML 格式内容
  - translated_html_content: 翻译后的 HTML 内容
  - is_published: 发布状态
  - published_at: 发布时间
  - received_at: 接收时间
  - created_at: 创建时间
  - updated_at: 更新时间

### 技术栈

- FastAPI 0.104.1
- Uvicorn 0.24.0
- SQLAlchemy 2.0.23
- PyMySQL 1.1.0
- Google API Python Client 2.108.0
- OpenAI 1.3.7
- Pydantic 2.10.3
- Loguru 0.7.2
- APScheduler 3.10.4

### 新增文件

- `app/scheduler.py` - 定时任务调度器
- `run_scheduler.py` - 独立定时任务启动脚本
- `Dockerfile` - Docker 容器配置
- `docker-compose.yml` - Docker Compose 配置
- `mail2gzh.service` - Systemd 服务配置
- `DEPLOYMENT.md` - 部署指南

### 文档

- README.md - 项目说明文档
- CHANGELOG.md - 变更日志
- env.example - 环境变量模板
- .gitignore - Git 忽略文件配置

---

## 未来计划

### [1.1.0] - 计划中

- [ ] 添加单元测试和集成测试
- [ ] 添加定时任务支持（使用 APScheduler）
- [ ] 支持多种翻译服务（Google Translate、DeepL 等）
- [ ] 添加邮件过滤规则配置
- [ ] 支持批量处理和重试机制
- [ ] 添加 Web 管理界面
- [ ] 支持 Docker 部署
- [ ] 添加监控和告警功能

### [1.2.0] - 计划中

- [ ] 支持多个 Gmail 账号
- [ ] 支持多个微信公众号
- [ ] 添加邮件模板系统
- [ ] 支持自定义翻译提示词
- [ ] 添加邮件附件处理
- [ ] 支持更多邮件提供商（Outlook、QQ 邮箱等）
- [ ] 添加数据分析和统计功能
- [ ] 性能优化和缓存策略

---

**说明**:
- 版本号遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/)
- 每个版本包含以下类型的变更：
  - **新增**: 新功能
  - **修改**: 现有功能的变更
  - **弃用**: 即将删除的功能
  - **移除**: 已删除的功能
  - **修复**: Bug 修复
  - **安全**: 安全问题修复
