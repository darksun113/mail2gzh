# 部署指南

本文档介绍如何在不同环境中部署 Mail2GZH 服务。

## 部署方式

### 1. 本地开发部署

#### 使用启动脚本（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd mail2gzh

# 运行启动脚本（自动检查环境、安装依赖、启动服务）
./run.sh
```

#### 手动部署

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
# 编辑 .env 文件

# 创建数据库
mysql -u root -p
CREATE DATABASE mail2gzh CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 启动服务
python -m app.main
```

### 2. Docker 部署

#### 使用 Docker Compose（推荐）

```bash
# 配置环境变量
cp env.example .env
# 编辑 .env 文件

# 启动所有服务（包括 MySQL）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mail2gzh
```

#### 单独使用 Docker

```bash
# 构建镜像
docker build -t mail2gzh .

# 运行容器
docker run -d \
  --name mail2gzh \
  -p 8000:8000 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/token.json:/app/token.json \
  mail2gzh
```

### 3. 生产环境部署

#### 使用 Systemd 服务

1. **安装服务文件**

```bash
# 复制服务文件
sudo cp mail2gzh.service /etc/systemd/system/

# 编辑服务文件，修改路径
sudo nano /etc/systemd/system/mail2gzh.service
```

2. **修改服务配置**

```ini
[Unit]
Description=Mail2GZH Email to WeChat Service
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/mail2gzh  # 修改为实际路径
Environment=PATH=/path/to/your/mail2gzh/venv/bin  # 修改为实际路径
ExecStart=/path/to/your/mail2gzh/venv/bin/python /path/to/your/mail2gzh/run_scheduler.py  # 修改为实际路径
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/path/to/your/mail2gzh/logs  # 修改为实际路径

[Install]
WantedBy=multi-user.target
```

3. **启动服务**

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable mail2gzh

# 启动服务
sudo systemctl start mail2gzh

# 查看状态
sudo systemctl status mail2gzh

# 查看日志
sudo journalctl -u mail2gzh -f
```

#### 使用 Nginx 反向代理

1. **安装 Nginx**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

2. **配置 Nginx**

创建 `/etc/nginx/sites-available/mail2gzh`：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 修改为您的域名

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件缓存
    location /static/ {
        alias /path/to/your/mail2gzh/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

3. **启用站点**

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/mail2gzh /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

#### 使用 SSL 证书（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

### 4. 云服务部署

#### 使用 Docker Swarm

```bash
# 初始化 Swarm
docker swarm init

# 部署服务栈
docker stack deploy -c docker-compose.yml mail2gzh

# 查看服务
docker stack services mail2gzh
```

#### 使用 Kubernetes

创建 `k8s-deployment.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mail2gzh
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mail2gzh
  template:
    metadata:
      labels:
        app: mail2gzh
    spec:
      containers:
      - name: mail2gzh
        image: mail2gzh:latest
        ports:
        - containerPort: 8000
        env:
        - name: DB_HOST
          value: "mysql-service"
        - name: DB_NAME
          value: "mail2gzh"
        - name: DB_USER
          value: "mail2gzh"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mail2gzh-secret
              key: db-password
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: config
          mountPath: /app/.env
      volumes:
      - name: logs
        emptyDir: {}
      - name: config
        configMap:
          name: mail2gzh-config
---
apiVersion: v1
kind: Service
metadata:
  name: mail2gzh-service
spec:
  selector:
    app: mail2gzh
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 环境配置

### 必需的环境变量

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mail2gzh
DB_USER=your_username
DB_PASSWORD=your_password

# Gmail API
GMAIL_CREDENTIALS_FILE=credentials.json

# OpenAI API
OPENAI_API_KEY=sk-xxxxxxxxxxxx

# 微信公众号
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
```

### 可选的环境变量

```bash
# 应用配置
APP_NAME=mail2gzh
DEBUG=False
HOST=0.0.0.0
PORT=8000

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 邮件处理配置
EMAIL_BATCH_SIZE=10
EMAIL_CHECK_INTERVAL=300
```

## 监控和维护

### 日志监控

```bash
# 查看应用日志
tail -f logs/app.log

# 查看系统日志
sudo journalctl -u mail2gzh -f

# 查看 Docker 日志
docker logs -f mail2gzh
```

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/api/v1/health

# 检查定时任务状态
curl http://localhost:8000/api/v1/scheduler/status

# 检查数据库连接
curl http://localhost:8000/api/v1/test/gmail
curl http://localhost:8000/api/v1/test/wechat
```

### 性能监控

```bash
# 查看系统资源使用
htop

# 查看 Docker 资源使用
docker stats

# 查看数据库性能
mysql -u root -p
SHOW PROCESSLIST;
SHOW STATUS LIKE 'Threads_connected';
```

### 备份策略

```bash
# 数据库备份
mysqldump -u root -p mail2gzh > backup_$(date +%Y%m%d_%H%M%S).sql

# 配置文件备份
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz .env credentials.json token.json

# 日志备份
tar -czf logs_backup_$(date +%Y%m%d_%H%M%S).tar.gz logs/
```

## 故障排除

### 常见问题

1. **服务启动失败**
   - 检查 Python 版本
   - 检查依赖安装
   - 检查环境变量配置
   - 查看错误日志

2. **数据库连接失败**
   - 检查 MySQL 服务状态
   - 检查数据库配置
   - 检查网络连接

3. **Gmail API 认证失败**
   - 检查 credentials.json 文件
   - 检查 Gmail API 权限
   - 重新进行 OAuth 授权

4. **微信公众号发布失败**
   - 检查 AppID 和 AppSecret
   - 检查公众号权限
   - 检查网络连接

### 调试模式

```bash
# 启用调试模式
export DEBUG=True
export LOG_LEVEL=DEBUG

# 启动服务
python -m app.main
```

### 日志级别

- `DEBUG`: 详细调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

## 安全建议

1. **环境变量安全**
   - 不要将 .env 文件提交到版本控制
   - 使用强密码
   - 定期轮换 API 密钥

2. **网络安全**
   - 使用 HTTPS
   - 配置防火墙
   - 限制访问 IP

3. **系统安全**
   - 定期更新系统
   - 使用非 root 用户运行服务
   - 配置日志轮转

4. **数据安全**
   - 定期备份数据
   - 加密敏感数据
   - 监控异常访问

## 扩展和优化

### 水平扩展

```bash
# 使用负载均衡器
# 配置多个实例
# 使用 Redis 进行会话共享
```

### 性能优化

```bash
# 数据库优化
# 缓存策略
# 异步处理
# 资源监控
```

### 高可用部署

```bash
# 主从复制
# 故障转移
# 监控告警
# 自动恢复
```

---

更多部署相关问题，请参考项目文档或提交 Issue。
