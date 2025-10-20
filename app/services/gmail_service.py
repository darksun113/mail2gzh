"""
Gmail API 服务
"""

import os
import base64
from typing import List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ..config import settings
from ..schemas.email import EmailCreate
from loguru import logger


class GmailService:
    """Gmail API 服务类"""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.scopes = [settings.gmail_scopes]
    
    def authenticate(self) -> bool:
        """Gmail API 认证"""
        try:
            # 检查是否存在已保存的凭据
            if os.path.exists(settings.gmail_token_file):
                self.credentials = Credentials.from_authorized_user_file(
                    settings.gmail_token_file, self.scopes
                )
            
            # 如果没有有效凭据，则进行授权流程
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    if not os.path.exists(settings.gmail_credentials_file):
                        logger.error(f"Gmail 凭据文件不存在: {settings.gmail_credentials_file}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        settings.gmail_credentials_file, self.scopes
                    )
                    self.credentials = flow.run_local_server(port=0)
                
                # 保存凭据供下次使用
                with open(settings.gmail_token_file, 'w') as token:
                    token.write(self.credentials.to_json())
            
            # 构建 Gmail API 服务
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("Gmail API 认证成功")
            return True
            
        except Exception as e:
            logger.error(f"Gmail API 认证失败: {str(e)}")
            return False
    
    def get_unread_emails(self, query: str = None, max_results: int = 10) -> List[dict]:
        """获取未读邮件列表"""
        try:
            if not self.service:
                if not self.authenticate():
                    return []
            
            query = query or settings.gmail_query
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"找到 {len(messages)} 封未读邮件")
            return messages
            
        except HttpError as error:
            logger.error(f"获取邮件列表失败: {error}")
            return []
        except Exception as e:
            logger.error(f"获取邮件列表时发生错误: {str(e)}")
            return []
    
    def get_email_details(self, message_id: str) -> Optional[dict]:
        """获取邮件详细信息"""
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            
            return self._parse_email_message(message)
            
        except HttpError as error:
            logger.error(f"获取邮件详情失败 (ID: {message_id}): {error}")
            return None
        except Exception as e:
            logger.error(f"获取邮件详情时发生错误: {str(e)}")
            return None
    
    def _parse_email_message(self, message: dict) -> dict:
        """解析邮件消息"""
        try:
            payload = message['payload']
            headers = payload.get('headers', [])
            
            # 提取邮件头信息
            email_data = {
                'gmail_id': message['id'],
                'subject': '',
                'sender': '',
                'recipient': '',
                'received_at': '',
                'content': '',
                'html_content': ''
            }
            
            # 解析邮件头
            for header in headers:
                name = header['name'].lower()
                value = header['value']
                
                if name == 'subject':
                    email_data['subject'] = value
                elif name == 'from':
                    email_data['sender'] = value
                elif name == 'to':
                    email_data['recipient'] = value
                elif name == 'date':
                    email_data['received_at'] = value
            
            # 解析邮件内容
            email_data.update(self._extract_email_content(payload))
            
            return email_data
            
        except Exception as e:
            logger.error(f"解析邮件消息失败: {str(e)}")
            return {}
    
    def _extract_email_content(self, payload: dict) -> dict:
        """提取邮件内容"""
        content = {
            'content': '',
            'html_content': ''
        }
        
        try:
            # 处理多部分邮件
            if 'parts' in payload:
                for part in payload['parts']:
                    mime_type = part.get('mimeType', '')
                    body = part.get('body', {})
                    
                    if mime_type == 'text/plain' and 'data' in body:
                        content['content'] = base64.urlsafe_b64decode(
                            body['data']
                        ).decode('utf-8')
                    elif mime_type == 'text/html' and 'data' in body:
                        content['html_content'] = base64.urlsafe_b64decode(
                            body['data']
                        ).decode('utf-8')
            else:
                # 处理单部分邮件
                mime_type = payload.get('mimeType', '')
                body = payload.get('body', {})
                
                if 'data' in body:
                    decoded_content = base64.urlsafe_b64decode(
                        body['data']
                    ).decode('utf-8')
                    
                    if mime_type == 'text/plain':
                        content['content'] = decoded_content
                    elif mime_type == 'text/html':
                        content['html_content'] = decoded_content
            
            return content
            
        except Exception as e:
            logger.error(f"提取邮件内容失败: {str(e)}")
            return content
