"""
OpenAI 翻译服务
"""

import json
import re
from typing import Dict, List, Optional, Any
from openai import OpenAI
from loguru import logger
from ..config import settings


class TranslationService:
    """OpenAI 翻译服务类"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.max_content_length = settings.max_content_length

    def translate_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        翻译邮件内容
        
        Args:
            email_data: 邮件数据字典，包含 subject, sender, html_content 等
            
        Returns:
            翻译结果字典
        """
        try:
            logger.info(f"开始翻译邮件: {email_data.get('subject', 'Unknown')}")
            
            # 调用 OpenAI API
            result = self._call_openai_api(email_data)
            
            # 验证内容
            validated_result = self._validate_content(result)
            
            # 如果内容过长，进行智能截断
            if validated_result.get('content_length', 0) > self.max_content_length:
                validated_result = self._truncate_content(validated_result)
            
            logger.info(f"邮件翻译完成: {validated_result.get('translated_title', 'Unknown')}")
            return validated_result
            
        except Exception as e:
            logger.error(f"翻译邮件失败: {str(e)}")
            return {
                "translated_title": email_data.get('subject', '翻译失败'),
                "news_source": email_data.get('sender', 'Unknown'),
                "translated_summary": "翻译失败",
                "translated_html": "<p>翻译失败，请稍后重试。</p>",
                "images_info": [],
                "content_length": 0,
                "publish_ready": False,
                "error": str(e)
            }

    def _call_openai_api(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用 OpenAI API 进行翻译"""
        
        # 构建提示词
        prompt = self._build_prompt(email_data)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的学术邮件翻译专家，专门处理学术期刊、研究论文相关的邮件内容。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            )
            
            content = response.choices[0].message.content.strip()
            
            # 尝试解析 JSON 响应
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # 如果不是 JSON 格式，尝试提取 JSON 部分
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result
                else:
                    raise ValueError("无法解析 OpenAI 响应为 JSON 格式")
                    
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {str(e)}")
            raise

    def _build_prompt(self, email_data: Dict[str, Any]) -> str:
        """构建翻译提示词"""
        
        subject = email_data.get('subject', 'No Subject')
        sender = email_data.get('sender', 'Unknown Sender')
        html_content = email_data.get('html_content', '')
        
        # 如果 HTML 内容为空，使用纯文本内容
        if not html_content:
            html_content = email_data.get('content', '')
        
        prompt = f"""你是一个专业的学术邮件翻译专家。请按照以下要求处理：

输入：
- 邮件主题：{subject}
- 发件人：{sender}  
- 邮件HTML内容：{html_content[:5000]}...

要求：
1. 翻译成流畅中文
2. 生成符合微信公众号规范的HTML（<{self.max_content_length}字符）
3. 提取新闻来源（从内容推测或使用发件人）
4. 识别所有图片并使用{{IMAGE_PLACEHOLDER_N}}占位
5. 生成摘要（100-200字）
6. 保持学术严谨性，专业术语准确

输出JSON格式：
{{
  "translated_title": "翻译后的标题",
  "news_source": "新闻来源",
  "translated_summary": "翻译摘要",
  "translated_html": "微信公众号格式HTML内容",
  "images_info": [{{"original_url": "...", "alt_text": "...", "placeholder": "{{IMAGE_PLACEHOLDER_0}}"}}],
  "content_length": 数字,
  "publish_ready": true/false
}}"""
        
        return prompt

    def _validate_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证翻译结果"""
        
        # 检查必要字段
        required_fields = ['translated_title', 'news_source', 'translated_summary', 'translated_html']
        for field in required_fields:
            if field not in result or not result[field]:
                logger.warning(f"翻译结果缺少必要字段: {field}")
                result[field] = result.get(field, "未知")
        
        # 确保 images_info 是列表
        if 'images_info' not in result or not isinstance(result['images_info'], list):
            result['images_info'] = []
        
        # 计算内容长度
        html_content = result.get('translated_html', '')
        result['content_length'] = len(html_content)
        
        # 检查内容长度
        if result['content_length'] > self.max_content_length:
            logger.warning(f"翻译内容过长: {result['content_length']} > {self.max_content_length}")
            result['publish_ready'] = False
        else:
            result['publish_ready'] = True
        
        # 验证 HTML 基本结构
        if not self._validate_html_structure(html_content):
            logger.warning("HTML 结构验证失败")
            result['publish_ready'] = False
        
        return result

    def _validate_html_structure(self, html_content: str) -> bool:
        """验证 HTML 基本结构"""
        try:
            # 检查是否包含基本的 HTML 标签
            if not re.search(r'<[^>]+>', html_content):
                return False
            
            # 检查是否有未闭合的标签（简单检查）
            open_tags = re.findall(r'<([^/][^>]*)>', html_content)
            close_tags = re.findall(r'</([^>]*)>', html_content)
            
            # 简单验证：开放标签数量应该大于等于闭合标签数量
            return len(open_tags) >= len(close_tags)
            
        except Exception as e:
            logger.error(f"HTML 结构验证失败: {str(e)}")
            return False

    def _truncate_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """智能截断内容"""
        
        html_content = result.get('translated_html', '')
        if len(html_content) <= self.max_content_length:
            return result
        
        logger.info(f"内容截断: {len(html_content)} -> {self.max_content_length}")
        
        # 尝试在段落边界截断
        truncated_html = self._smart_truncate_html(html_content, self.max_content_length)
        
        result['translated_html'] = truncated_html
        result['content_length'] = len(truncated_html)
        result['publish_ready'] = True
        
        return result

    def _smart_truncate_html(self, html_content: str, max_length: int) -> str:
        """智能截断 HTML 内容"""
        
        if len(html_content) <= max_length:
            return html_content
        
        # 在段落边界截断
        paragraphs = re.split(r'(</p>|</div>|</section>)', html_content)
        
        truncated = ""
        for i in range(0, len(paragraphs), 2):
            if i + 1 < len(paragraphs):
                paragraph = paragraphs[i] + paragraphs[i + 1]
            else:
                paragraph = paragraphs[i]
            
            if len(truncated + paragraph) > max_length - 100:  # 留出空间添加截断提示
                truncated += "<p>...（内容已截断）</p>"
                break
            else:
                truncated += paragraph
        
        return truncated

    def _extract_images(self, html_content: str) -> List[Dict[str, str]]:
        """从 HTML 中提取图片信息"""
        
        images = []
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*>'
        
        matches = re.finditer(img_pattern, html_content)
        for i, match in enumerate(matches):
            images.append({
                "original_url": match.group(1),
                "alt_text": match.group(2),
                "placeholder": f"{{IMAGE_PLACEHOLDER_{i}}}"
            })
        
        return images