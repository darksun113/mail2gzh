# Gmail 服务账号配置指南

## 概述

本指南将帮助您配置 Gmail 服务账号，以便在纯命令行环境中使用 Mail2GZH 服务。

## 服务账号 vs OAuth 2.0 用户授权

### 服务账号的优势

- ✅ **无需用户交互**：适合服务器环境
- ✅ **长期有效**：不会过期（除非手动撤销）
- ✅ **自动化友好**：无需浏览器授权
- ✅ **安全性高**：可以限制权限范围

### 服务账号的限制

- ❌ **个人 Gmail 限制**：个人 Gmail 账户需要特殊配置
- ❌ **G Suite 推荐**：最适合 G Suite/Google Workspace 环境
- ❌ **权限限制**：只能访问授权的邮箱

## 配置步骤

### 1. 创建 Google Cloud 项目

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 记录项目 ID（稍后会用到）

### 2. 启用 Gmail API

1. 在 Google Cloud Console 中，进入 "API 和服务" > "库"
2. 搜索 "Gmail API"
3. 点击 "Gmail API" 并启用

### 3. 创建服务账号

1. 进入 "IAM 和管理" > "服务账号"
2. 点击 "创建服务账号"
3. 填写信息：
   - **服务账号名称**: `mail2gzh-service`
   - **服务账号 ID**: `mail2gzh-service`（自动生成）
   - **描述**: `Mail2GZH Gmail API 服务账号`
4. 点击 "创建并继续"
5. 跳过角色分配，点击 "完成"

### 4. 创建服务账号密钥

1. 在服务账号列表中，点击刚创建的服务账号
2. 切换到 "密钥" 标签
3. 点击 "添加密钥" > "创建新密钥"
4. 选择 "JSON" 格式
5. 点击 "创建"
6. 下载 JSON 文件并重命名为 `service-account-key.json`
7. 将文件放在项目根目录

### 5. 配置域范围委派（重要）

#### 对于 G Suite/Google Workspace 用户：

1. 在服务账号的 "详细信息" 页面
2. 点击 "显示域范围委派"
3. 点击 "添加域范围委派"
4. 填写信息：
   - **产品名称**: `Mail2GZH`
   - **主域**: 您的域名（如 `yourcompany.com`）
   - **范围**: `https://www.googleapis.com/auth/gmail.readonly`
5. 点击 "授权"

#### 对于个人 Gmail 用户：

个人 Gmail 账户使用服务账号需要特殊配置：

1. 在 Google Cloud Console 中，进入 "OAuth 同意屏幕"
2. 选择 "外部" 用户类型
3. 填写应用信息
4. 在 "测试用户" 部分添加您的 Gmail 地址
5. 发布应用（或保持测试状态）

### 6. 配置环境变量

在 `.env` 文件中设置：

```bash
# Gmail 服务账号配置
GMAIL_CREDENTIALS_FILE=service-account-key.json
GMAIL_SUBJECT_EMAIL=your-email@gmail.com
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly
GMAIL_QUERY=is:unread label:inbox
```

## 测试配置

### 1. 启动服务

```bash
./run.sh
```

### 2. 测试 Gmail 连接

```bash
curl -X POST "http://localhost:8000/api/v1/test/gmail"
```

### 3. 同步邮件

```bash
curl -X POST "http://localhost:8000/api/v1/emails/sync?max_results=5"
```

## 常见问题

### Q: 服务账号无法访问个人 Gmail

**A**: 个人 Gmail 账户使用服务账号需要特殊配置：

1. 确保在 OAuth 同意屏幕中添加了测试用户
2. 确保应用已发布或处于测试状态
3. 确保服务账号有正确的权限

### Q: 域范围委派失败

**A**: 检查以下项目：

1. 确保您有 G Suite/Google Workspace 管理员权限
2. 确保域名正确
3. 确保范围 URL 正确
4. 等待几分钟让配置生效

### Q: 权限被拒绝

**A**: 检查以下项目：

1. 确保 Gmail API 已启用
2. 确保服务账号有正确的权限
3. 确保 JSON 密钥文件正确
4. 确保环境变量配置正确

## 安全建议

1. **保护密钥文件**：不要将 `service-account-key.json` 提交到版本控制
2. **限制权限**：只授予必要的 Gmail 读取权限
3. **定期轮换**：定期更新服务账号密钥
4. **监控使用**：定期检查 API 使用情况

## 故障排除

### 检查服务账号状态

```bash
# 检查密钥文件是否存在
ls -la service-account-key.json

# 检查环境变量
grep GMAIL .env
```

### 查看日志

```bash
# 查看应用日志
tail -f logs/app.log

# 查看特定错误
grep -i "gmail\|error" logs/app.log
```

### 测试 API 连接

```bash
# 使用 gcloud 测试
gcloud auth activate-service-account --key-file=service-account-key.json
gcloud auth list
```

## 下一步

配置完成后，您可以：

1. 测试邮件同步功能
2. 配置 OpenAI 翻译
3. 设置微信公众号发布
4. 配置定时任务

更多信息请参考 [README.md](README.md)。
