"""
邮件数据模型
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.sql import func
from ..database import Base


class Email(Base):
    """邮件模型"""
    
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String(255), unique=True, index=True, nullable=False, comment="Gmail 邮件ID")
    subject = Column(String(500), nullable=False, comment="邮件主题")
    sender = Column(String(255), nullable=False, comment="发件人")
    recipient = Column(String(255), nullable=False, comment="收件人")
    content = Column(LONGTEXT, comment="原始邮件内容")
    translated_content = Column(LONGTEXT, comment="翻译后的中文内容")
    html_content = Column(LONGTEXT, comment="HTML格式内容")
    translated_html_content = Column(LONGTEXT, comment="翻译后的HTML内容")
    
    # 翻译相关字段
    news_source = Column(String(255), comment="新闻来源")
    translated_summary = Column(Text, comment="翻译摘要")
    wechat_html_content = Column(LONGTEXT, comment="微信公众号格式HTML")
    content_length = Column(Integer, comment="内容长度")
    images_processed = Column(Boolean, default=False, comment="图片是否已处理")
    publish_ready = Column(Boolean, default=False, comment="是否可发布")
    images_info = Column(Text, comment="图片信息(JSON)")
    
    received_at = Column(DateTime, nullable=False, comment="邮件接收时间")
    is_published = Column(Boolean, default=False, comment="是否已发布到微信公众号")
    published_at = Column(DateTime, comment="发布时间")
    created_at = Column(DateTime, default=func.now(), comment="记录创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="记录更新时间")
    
    # 创建索引
    __table_args__ = (
        Index('idx_gmail_id', 'gmail_id'),
        Index('idx_received_at', 'received_at'),
        Index('idx_is_published', 'is_published'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Email(id={self.id}, subject='{self.subject}', sender='{self.sender}')>"
