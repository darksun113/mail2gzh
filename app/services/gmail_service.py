import os
import base64
import qrcode
from io import StringIO
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
    """Gmail API 服务类（OAuth 2.0 用户授权 + 控制台二维码）"""

    def __init__(self):
        self.service = None
        self.credentials = None
        self.scopes = [settings.gmail_scopes]

    def authenticate(self) -> bool:
        """Gmail API 认证（OAuth 2.0 用户授权 + 控制台二维码）"""
        try:
            # 检查凭证文件是否存在
            if not os.path.exists(settings.gmail_credentials_file):
                logger.error(f"Gmail 凭证文件不存在: {settings.gmail_credentials_file}")
                logger.info("请从 Google Cloud Console 下载 OAuth 2.0 客户端 ID 凭证文件")
                return False

            # 检查是否已有有效令牌
            if os.path.exists(settings.gmail_token_file):
                try:
                    self.credentials = Credentials.from_authorized_user_file(
                        settings.gmail_token_file, self.scopes
                    )
                    
                    # 检查令牌是否有效
                    if self.credentials and self.credentials.valid:
                        logger.info("使用已保存的 Gmail API 令牌")
                        self.service = build('gmail', 'v1', credentials=self.credentials)
                        return True
                    
                    # 尝试刷新令牌
                    if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                        logger.info("刷新 Gmail API 令牌...")
                        self.credentials.refresh(Request())
                        self._save_token()
                        self.service = build('gmail', 'v1', credentials=self.credentials)
                        logger.info("Gmail API 令牌刷新成功")
                        return True
                        
                except Exception as e:
                    logger.warning(f"加载已保存令牌失败: {str(e)}")
                    # 继续执行新的授权流程

            # 执行新的 OAuth 2.0 授权流程
            logger.info("开始 Gmail API OAuth 2.0 授权流程...")
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.gmail_credentials_file, self.scopes
            )
            
            # 获取授权 URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # 在控制台显示二维码和授权信息
            self._display_qr_code(auth_url)
            
            # 等待用户输入授权码
            auth_code = input("\n请输入授权码: ").strip()
            
            if not auth_code:
                logger.error("未提供授权码，认证失败")
                return False
            
            # 使用授权码获取令牌
            flow.fetch_token(code=auth_code)
            self.credentials = flow.credentials
            
            # 保存令牌
            self._save_token()
            
            # 构建 Gmail API 服务
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("Gmail API OAuth 2.0 授权成功")
            return True

        except Exception as e:
            logger.error(f"Gmail API 认证失败: {str(e)}")
            return False

    def _display_qr_code(self, auth_url: str):
        """在控制台显示二维码和授权信息"""
        print("\n" + "="*60)
        print("🔐 Gmail API 授权")
        print("="*60)
        print(f"授权 URL: {auth_url}")
        print("\n📱 方法一：扫描二维码（推荐）")
        print("-" * 40)
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=2,
            border=1,
        )
        qr.add_data(auth_url)
        qr.make(fit=True)
        
        # 在控制台显示二维码
        qr.print_ascii(invert=True)
        
        print("\n📝 方法二：手动访问")
        print("-" * 40)
        print("1. 在浏览器中打开上述 URL")
        print("2. 登录您的 Google 账户")
        print("3. 授权应用访问 Gmail")
        print("4. 复制授权码并粘贴到下方")
        print("\n" + "="*60)

    def _save_token(self):
        """保存令牌到文件"""
        try:
            with open(settings.gmail_token_file, 'w') as token:
                token.write(self.credentials.to_json())
            logger.info(f"令牌已保存到: {settings.gmail_token_file}")
        except Exception as e:
            logger.error(f"保存令牌失败: {str(e)}")

    def get_unread_emails(self, max_results: int = None) -> List[dict]:
        """获取未读邮件列表"""
        if not self.service:
            logger.error("Gmail API 服务未初始化")
            return []

        try:
            # 使用配置中的默认值或传入的参数
            if max_results is None:
                max_results = settings.gmail_max_results
                
            # 构建查询参数
            query_params = {
                'userId': 'me',
                'q': settings.gmail_query,
                'maxResults': max_results
            }
            
            logger.info(f"查询 Gmail 邮件: {settings.gmail_query}")
            
            # 获取邮件列表
            results = self.service.users().messages().list(**query_params).execute()
            messages = results.get('messages', [])
            
            logger.info(f"找到 {len(messages)} 封邮件")
            
            if not messages:
                return []
            
            # 获取邮件详情
            emails = []
            for message in messages:
                try:
                    msg = self.service.users().messages().get(
                        userId='me', 
                        id=message['id']
                    ).execute()
                    
                    email_data = self._extract_email_data(msg)
                    if email_data:
                        emails.append(email_data)
                        
                except Exception as e:
                    logger.warning(f"获取邮件详情失败 {message['id']}: {str(e)}")
                    continue
            
            return emails

        except HttpError as e:
            logger.error(f"获取邮件列表时发生错误: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"获取邮件列表时发生未知错误: {str(e)}")
            return []

    def _extract_email_data(self, message: dict) -> Optional[dict]:
        """从 Gmail API 消息中提取邮件数据"""
        try:
            headers = message['payload'].get('headers', [])
            
            # 提取邮件头信息
            subject = ""
            sender = ""
            recipient = ""
            received_at = ""
            
            for header in headers:
                name = header['name'].lower()
                value = header['value']
                
                if name == 'subject':
                    subject = value
                elif name == 'from':
                    sender = value
                elif name == 'to':
                    recipient = value
                elif name == 'date':
                    received_at = value
            
            # 提取邮件内容
            content, html_content = self._extract_email_content(message['payload'])
            
            # 限制 HTML 内容长度（避免数据库字段溢出）
            if html_content and len(html_content) > 16777215:  # LONGTEXT 最大长度
                html_content = html_content[:16777210] + "..."
                logger.warning("HTML 内容过长，已截断")
            
            return {
                'gmail_id': message['id'],
                'subject': subject,
                'sender': sender,
                'recipient': recipient,
                'content': content,
                'html_content': html_content,
                'received_at': received_at
            }
            
        except Exception as e:
            logger.error(f"提取邮件数据失败: {str(e)}")
            return None

    def _extract_email_content(self, payload: dict) -> tuple:
        """提取邮件文本和 HTML 内容"""
        content = ""
        html_content = ""
        
        def extract_from_part(part):
            nonlocal content, html_content
            
            if 'text/plain' in part.get('mimeType', ''):
                data = part.get('body', {}).get('data', '')
                if data:
                    try:
                        decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                        content += decoded + "\n"
                    except Exception as e:
                        logger.warning(f"解码文本内容失败: {str(e)}")
            
            elif 'text/html' in part.get('mimeType', ''):
                data = part.get('body', {}).get('data', '')
                if data:
                    try:
                        decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                        html_content += decoded
                    except Exception as e:
                        logger.warning(f"解码 HTML 内容失败: {str(e)}")
            
            # 递归处理多部分邮件
            if 'parts' in part:
                for subpart in part['parts']:
                    extract_from_part(subpart)
        
        extract_from_part(payload)
        
        return content.strip(), html_content.strip()

    def test_connection(self) -> dict:
        """测试 Gmail API 连接"""
        try:
            if not self.authenticate():
                return {
                    "success": False,
                    "message": "Gmail API 认证失败"
                }
            
            # 尝试获取用户信息
            profile = self.service.users().getProfile(userId='me').execute()
            
            return {
                "success": True,
                "message": "Gmail API 连接成功",
                "email_address": profile.get('emailAddress', ''),
                "total_messages": profile.get('messagesTotal', 0),
                "threads_total": profile.get('threadsTotal', 0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Gmail API 连接失败: {str(e)}"
            }