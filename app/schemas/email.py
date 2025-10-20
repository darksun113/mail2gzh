"""
邮件相关的 Pydantic 数据模式
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class EmailBase(BaseModel):
    """邮件基础模式"""
    gmail_id: str
    subject: str
    sender: str
    recipient: str
    content: Optional[str] = None
    html_content: Optional[str] = None
    received_at: datetime


class EmailCreate(EmailBase):
    """创建邮件模式"""
    pass


class EmailUpdate(BaseModel):
    """更新邮件模式"""
    translated_content: Optional[str] = None
    translated_html_content: Optional[str] = None
    is_published: Optional[bool] = None
    published_at: Optional[datetime] = None


class EmailResponse(EmailBase):
    """邮件响应模式"""
    id: int
    translated_content: Optional[str] = None
    translated_html_content: Optional[str] = None
    is_published: bool = False
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmailListResponse(BaseModel):
    """邮件列表响应模式"""
    emails: list[EmailResponse]
    total: int
    page: int
    size: int
    pages: int


class TranslationRequest(BaseModel):
    """翻译请求模式"""
    content: str
    source_lang: str = "en"
    target_lang: str = "zh"


class TranslationResponse(BaseModel):
    """翻译响应模式"""
    original_content: str
    translated_content: str
    source_lang: str
    target_lang: str
    success: bool
    error_message: Optional[str] = None


class WeChatPublishRequest(BaseModel):
    """微信公众号发布请求模式"""
    email_id: int
    title: str
    content: str
    author: str = "邮件转发"


class WeChatPublishResponse(BaseModel):
    """微信公众号发布响应模式"""
    success: bool
    message: str
    media_id: Optional[str] = None
    error_code: Optional[int] = None
