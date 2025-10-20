"""
OpenAI 翻译服务
"""

import openai
from typing import Optional
from ..config import settings
from ..schemas.email import TranslationRequest, TranslationResponse
from loguru import logger


class TranslationService:
    """OpenAI 翻译服务类"""
    
    def __init__(self):
        openai.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature
    
    def translate_text(self, content: str, source_lang: str = None, target_lang: str = None) -> TranslationResponse:
        """翻译文本内容"""
        try:
            source_lang = source_lang or settings.translation_source_lang
            target_lang = target_lang or settings.translation_target_lang
            
            # 构建翻译提示词
            prompt = self._build_translation_prompt(content, source_lang, target_lang)
            
            # 调用 OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"你是一个专业的翻译助手，负责将{source_lang}翻译成{target_lang}。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            translated_content = response.choices[0].message.content.strip()
            
            return TranslationResponse(
                original_content=content,
                translated_content=translated_content,
                source_lang=source_lang,
                target_lang=target_lang,
                success=True
            )
            
        except Exception as e:
            logger.error(f"翻译失败: {str(e)}")
            return TranslationResponse(
                original_content=content,
                translated_content="",
                source_lang=source_lang or settings.translation_source_lang,
                target_lang=target_lang or settings.translation_target_lang,
                success=False,
                error_message=str(e)
            )
    
    def translate_html(self, html_content: str, source_lang: str = None, target_lang: str = None) -> TranslationResponse:
        """翻译 HTML 内容"""
        try:
            source_lang = source_lang or settings.translation_source_lang
            target_lang = target_lang or settings.translation_target_lang
            
            # 构建 HTML 翻译提示词
            prompt = self._build_html_translation_prompt(html_content, source_lang, target_lang)
            
            # 调用 OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"你是一个专业的翻译助手，负责将{source_lang}的HTML内容翻译成{target_lang}，保持HTML标签结构不变。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            translated_html = response.choices[0].message.content.strip()
            
            return TranslationResponse(
                original_content=html_content,
                translated_content=translated_html,
                source_lang=source_lang,
                target_lang=target_lang,
                success=True
            )
            
        except Exception as e:
            logger.error(f"HTML翻译失败: {str(e)}")
            return TranslationResponse(
                original_content=html_content,
                translated_content="",
                source_lang=source_lang or settings.translation_source_lang,
                target_lang=target_lang or settings.translation_target_lang,
                success=False,
                error_message=str(e)
            )
    
    def _build_translation_prompt(self, content: str, source_lang: str, target_lang: str) -> str:
        """构建翻译提示词"""
        return f"""
请将以下{source_lang}文本翻译成{target_lang}：

{content}

要求：
1. 保持原文的语气和风格
2. 确保翻译准确、自然
3. 如果是邮件内容，保持邮件的正式语调
4. 只返回翻译结果，不要添加其他说明
"""
    
    def _build_html_translation_prompt(self, html_content: str, source_lang: str, target_lang: str) -> str:
        """构建 HTML 翻译提示词"""
        return f"""
请将以下{source_lang}的HTML内容翻译成{target_lang}：

{html_content}

要求：
1. 保持HTML标签结构完全不变
2. 只翻译标签内的文本内容
3. 保持原文的语气和风格
4. 确保翻译准确、自然
5. 只返回翻译后的HTML，不要添加其他说明
"""
    
    def is_translation_needed(self, content: str, target_lang: str = None) -> bool:
        """判断是否需要翻译"""
        target_lang = target_lang or settings.translation_target_lang
        
        # 简单的语言检测（可以根据需要改进）
        if target_lang == "zh":
            # 检查是否包含中文字符
            return not any('\u4e00' <= char <= '\u9fff' for char in content)
        
        return True
