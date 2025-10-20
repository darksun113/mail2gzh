-- 数据库迁移脚本：添加翻译相关字段
-- 执行前请备份数据库！

-- 清空现有数据（可选，根据需求决定是否执行）
-- TRUNCATE TABLE emails;

-- 删除现有表（如果存在）
DROP TABLE IF EXISTS emails;

-- 重新创建表结构
CREATE TABLE `emails` (
  `id` int NOT NULL AUTO_INCREMENT,
  `gmail_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Gmail 邮件ID',
  `subject` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮件主题',
  `sender` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发件人',
  `recipient` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '收件人',
  `content` longtext COLLATE utf8mb4_unicode_ci COMMENT '原始邮件内容',
  `translated_content` longtext COLLATE utf8mb4_unicode_ci COMMENT '翻译后的中文内容',
  `html_content` longtext COLLATE utf8mb4_unicode_ci COMMENT 'HTML格式内容',
  `translated_html_content` longtext COLLATE utf8mb4_unicode_ci COMMENT '翻译后的HTML内容',
  
  -- 翻译相关字段
  `news_source` varchar(255) COLLATE utf8mb4_unicode_ci COMMENT '新闻来源',
  `translated_summary` text COLLATE utf8mb4_unicode_ci COMMENT '翻译摘要',
  `wechat_html_content` longtext COLLATE utf8mb4_unicode_ci COMMENT '微信公众号格式HTML',
  `content_length` int COMMENT '内容长度',
  `images_processed` tinyint(1) DEFAULT '0' COMMENT '图片是否已处理',
  `publish_ready` tinyint(1) DEFAULT '0' COMMENT '是否可发布',
  `images_info` text COLLATE utf8mb4_unicode_ci COMMENT '图片信息(JSON)',
  
  `received_at` datetime NOT NULL COMMENT '邮件接收时间',
  `is_published` tinyint(1) DEFAULT '0' COMMENT '是否已发布到微信公众号',
  `published_at` datetime DEFAULT NULL COMMENT '发布时间',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `gmail_id` (`gmail_id`),
  KEY `idx_gmail_id` (`gmail_id`),
  KEY `idx_received_at` (`received_at`),
  KEY `idx_is_published` (`is_published`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_publish_ready` (`publish_ready`),
  KEY `idx_images_processed` (`images_processed`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='邮件表';

-- 插入测试数据（可选）
-- INSERT INTO emails (gmail_id, subject, sender, recipient, content, html_content, received_at) 
-- VALUES ('test123', 'Test Email', 'test@example.com', 'user@example.com', 'Test content', '<p>Test HTML</p>', NOW());


