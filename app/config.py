"""
应用配置管理
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用配置
    app_name: str = "mail2gzh"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 数据库配置
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "mail2gzh"
    db_user: str = "root"
    db_password: str = ""
    db_charset: str = "utf8mb4"
    
    # Gmail API 配置（OAuth 2.0 用户授权）
    gmail_credentials_file: str = "credentials.json"
    gmail_token_file: str = "token.json"
    gmail_scopes: str = "https://www.googleapis.com/auth/gmail.readonly"
    gmail_query: str = "is:unread label:inbox"
    gmail_max_results: int = 50  # 每次同步的最大邮件数量
    
    # OpenAI API 配置
    openai_api_key: str = ""
    openai_model: str = "gpt-5-2025-08-07"
    openai_max_tokens: int = 4000
    
    # 内容长度和发布控制
    max_content_length: int = 20000
    daily_publish_limit: int = 1
    batch_publish_limit: int = 5
    openai_temperature: float = 0.3
    
    # 微信公众号配置
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    wechat_access_token_url: str = "https://api.weixin.qq.com/cgi-bin/token"
    wechat_material_upload_url: str = "https://api.weixin.qq.com/cgi-bin/material/add_news"
    wechat_message_send_url: str = "https://api.weixin.qq.com/cgi-bin/message/mass/sendall"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # 翻译配置
    translation_source_lang: str = "en"
    translation_target_lang: str = "zh"
    translation_max_length: int = 2000
    
    # 邮件处理配置
    email_batch_size: int = 10
    email_check_interval: int = 300  # 秒
    
    @property
    def database_url(self) -> str:
        """构建数据库连接URL"""
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset={self.db_charset}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()
