"""
微信公众号 API 服务
"""

import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from ..config import settings
from ..schemas.email import WeChatPublishRequest, WeChatPublishResponse
from loguru import logger


class WeChatService:
    """微信公众号 API 服务类"""
    
    def __init__(self):
        self.app_id = settings.wechat_app_id
        self.app_secret = settings.wechat_app_secret
        self.access_token = None
        self.token_expires_at = None
    
    def get_access_token(self) -> Optional[str]:
        """获取微信公众号访问令牌"""
        try:
            # 检查令牌是否仍然有效
            if (self.access_token and self.token_expires_at and 
                datetime.now() < self.token_expires_at):
                return self.access_token
            
            # 请求新的访问令牌
            url = settings.wechat_access_token_url
            params = {
                'grant_type': 'client_credential',
                'appid': self.app_id,
                'secret': self.app_secret
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'access_token' in data:
                self.access_token = data['access_token']
                # 设置令牌过期时间（提前5分钟过期）
                expires_in = data.get('expires_in', 7200)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
                
                logger.info("微信公众号访问令牌获取成功")
                return self.access_token
            else:
                logger.error(f"获取访问令牌失败: {data}")
                return None
                
        except Exception as e:
            logger.error(f"获取微信公众号访问令牌失败: {str(e)}")
            return None
    
    def upload_news_material(self, title: str, content: str, author: str = "邮件转发") -> Optional[str]:
        """上传图文素材到微信公众号"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return None
            
            url = f"{settings.wechat_material_upload_url}?access_token={access_token}"
            
            # 构建图文消息数据
            articles = [{
                "title": title,
                "author": author,
                "digest": content[:120] + "..." if len(content) > 120 else content,
                "content": self._format_content_for_wechat(content),
                "content_source_url": "",
                "thumb_media_id": "",  # 需要先上传缩略图
                "show_cover_pic": 0,
                "need_open_comment": 0,
                "only_fans_can_comment": 0
            }]
            
            data = {
                "articles": articles
            }
            
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'media_id' in result:
                logger.info(f"图文素材上传成功，media_id: {result['media_id']}")
                return result['media_id']
            else:
                logger.error(f"上传图文素材失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"上传图文素材失败: {str(e)}")
            return None
    
    def send_mass_message(self, media_id: str, is_to_all: bool = True) -> bool:
        """群发消息"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return False
            
            url = f"{settings.wechat_message_send_url}?access_token={access_token}"
            
            data = {
                "filter": {
                    "is_to_all": is_to_all
                },
                "mpnews": {
                    "media_id": media_id
                },
                "msgtype": "mpnews",
                "send_ignore_reprint": 0
            }
            
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info("群发消息成功")
                return True
            else:
                logger.error(f"群发消息失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"群发消息失败: {str(e)}")
            return False
    
    def publish_email(self, request: WeChatPublishRequest) -> WeChatPublishResponse:
        """发布邮件到微信公众号"""
        try:
            # 上传图文素材
            media_id = self.upload_news_material(
                title=request.title,
                content=request.content,
                author=request.author
            )
            
            if not media_id:
                return WeChatPublishResponse(
                    success=False,
                    message="上传图文素材失败",
                    error_code=-1
                )
            
            # 群发消息
            if self.send_mass_message(media_id):
                return WeChatPublishResponse(
                    success=True,
                    message="发布成功",
                    media_id=media_id
                )
            else:
                return WeChatPublishResponse(
                    success=False,
                    message="群发消息失败",
                    media_id=media_id,
                    error_code=-2
                )
                
        except Exception as e:
            logger.error(f"发布邮件到微信公众号失败: {str(e)}")
            return WeChatPublishResponse(
                success=False,
                message=f"发布失败: {str(e)}",
                error_code=-3
            )
    
    def _format_content_for_wechat(self, content: str) -> str:
        """格式化内容为微信公众号格式"""
        # 简单的HTML格式化，可以根据需要改进
        formatted_content = content.replace('\n', '<br/>')
        
        # 添加基本的HTML结构
        wechat_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            {formatted_content}
        </div>
        """
        
        return wechat_html
    
    def test_connection(self) -> bool:
        """测试微信公众号连接"""
        try:
            access_token = self.get_access_token()
            return access_token is not None
        except Exception as e:
            logger.error(f"测试微信公众号连接失败: {str(e)}")
            return False
