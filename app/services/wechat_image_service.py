"""
微信公众号图片处理服务
"""

import requests
import json
from typing import Dict, List, Optional, Any
from loguru import logger
from ..config import settings


class WeChatImageService:
    """微信公众号图片处理服务类"""

    def __init__(self):
        self.app_id = settings.wechat_app_id
        self.app_secret = settings.wechat_app_secret
        self.access_token = None

    def process_images(self, images_info: List[Dict[str, str]], html_content: str) -> Dict[str, Any]:
        """
        处理邮件中的图片
        
        Args:
            images_info: 图片信息列表
            html_content: 包含图片占位符的 HTML 内容
            
        Returns:
            处理结果字典
        """
        try:
            logger.info(f"开始处理 {len(images_info)} 张图片")
            
            # 获取微信访问令牌
            if not self._get_access_token():
                raise Exception("获取微信访问令牌失败")
            
            # 处理每张图片
            processed_images = []
            failed_images = []
            
            for image_info in images_info:
                try:
                    result = self._process_single_image(image_info)
                    if result['success']:
                        processed_images.append(result)
                    else:
                        failed_images.append({
                            'original_url': image_info['original_url'],
                            'error': result['error']
                        })
                except Exception as e:
                    logger.error(f"处理图片失败 {image_info['original_url']}: {str(e)}")
                    failed_images.append({
                        'original_url': image_info['original_url'],
                        'error': str(e)
                    })
            
            # 替换 HTML 中的占位符
            updated_html = self._replace_placeholders(html_content, processed_images)
            
            logger.info(f"图片处理完成: 成功 {len(processed_images)}, 失败 {len(failed_images)}")
            
            return {
                'success': True,
                'processed_images': processed_images,
                'failed_images': failed_images,
                'updated_html': updated_html,
                'images_processed': len(processed_images) > 0
            }
            
        except Exception as e:
            logger.error(f"图片处理失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processed_images': [],
                'failed_images': images_info,
                'updated_html': html_content,
                'images_processed': False
            }

    def _get_access_token(self) -> bool:
        """获取微信访问令牌"""
        try:
            url = "https://api.weixin.qq.com/cgi-bin/token"
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
                logger.info("微信访问令牌获取成功")
                return True
            else:
                logger.error(f"获取微信访问令牌失败: {data}")
                return False
                
        except Exception as e:
            logger.error(f"获取微信访问令牌异常: {str(e)}")
            return False

    def _process_single_image(self, image_info: Dict[str, str]) -> Dict[str, Any]:
        """处理单张图片"""
        
        original_url = image_info['original_url']
        alt_text = image_info.get('alt_text', '')
        placeholder = image_info['placeholder']
        
        try:
            # 下载图片
            image_data = self._download_image(original_url)
            if not image_data:
                return {
                    'success': False,
                    'error': '图片下载失败',
                    'original_url': original_url,
                    'placeholder': placeholder
                }
            
            # 上传到微信
            wechat_media_id = self._upload_to_wechat(image_data, alt_text)
            if not wechat_media_id:
                return {
                    'success': False,
                    'error': '图片上传到微信失败',
                    'original_url': original_url,
                    'placeholder': placeholder
                }
            
            return {
                'success': True,
                'original_url': original_url,
                'wechat_media_id': wechat_media_id,
                'placeholder': placeholder,
                'alt_text': alt_text
            }
            
        except Exception as e:
            logger.error(f"处理图片异常 {original_url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'original_url': original_url,
                'placeholder': placeholder
            }

    def _download_image(self, url: str) -> Optional[bytes]:
        """下载图片"""
        try:
            logger.info(f"下载图片: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"非图片内容类型: {content_type}")
                return None
            
            # 检查文件大小（微信限制 2MB）
            if len(response.content) > 2 * 1024 * 1024:
                logger.warning(f"图片文件过大: {len(response.content)} bytes")
                return None
            
            logger.info(f"图片下载成功: {len(response.content)} bytes")
            return response.content
            
        except Exception as e:
            logger.error(f"下载图片失败 {url}: {str(e)}")
            return None

    def _upload_to_wechat(self, image_data: bytes, alt_text: str = "") -> Optional[str]:
        """上传图片到微信"""
        try:
            if not self.access_token:
                logger.error("微信访问令牌未获取")
                return None
            
            url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={self.access_token}"
            
            files = {
                'media': ('image.jpg', image_data, 'image/jpeg')
            }
            
            response = requests.post(url, files=files, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'url' in data:
                logger.info(f"图片上传成功: {data['url']}")
                return data['url']
            else:
                logger.error(f"图片上传失败: {data}")
                return None
                
        except Exception as e:
            logger.error(f"上传图片到微信异常: {str(e)}")
            return None

    def _replace_placeholders(self, html_content: str, processed_images: List[Dict[str, Any]]) -> str:
        """替换 HTML 中的图片占位符"""
        
        updated_html = html_content
        
        for image in processed_images:
            if image['success']:
                # 替换占位符为微信图片 URL
                placeholder = image['placeholder']
                wechat_url = image['wechat_media_id']
                alt_text = image.get('alt_text', '')
                
                # 创建微信格式的图片标签
                wechat_img_tag = f'<img src="{wechat_url}" alt="{alt_text}" style="max-width: 100%; height: auto;">'
                
                updated_html = updated_html.replace(placeholder, wechat_img_tag)
                logger.info(f"替换占位符: {placeholder} -> {wechat_url}")
        
        return updated_html

