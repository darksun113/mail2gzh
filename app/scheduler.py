"""
定时任务调度器
"""

import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from loguru import logger

from .config import settings
from .services.gmail_service import GmailService
from .services.translation_service import TranslationService
from .services.wechat_service import WeChatService
from .database import SessionLocal
from .models.email import Email


class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone='UTC')
        self.gmail_service = GmailService()
        self.translation_service = TranslationService()
        self.wechat_service = WeChatService()
        
        # 添加事件监听器
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
    
    def start(self):
        """启动调度器"""
        try:
            # 添加每日 UTC 0 时执行的任务
            self.scheduler.add_job(
                func=self.daily_email_processing,
                trigger=CronTrigger(hour=0, minute=0, timezone='UTC'),
                id='daily_email_processing',
                name='每日邮件处理任务',
                replace_existing=True
            )
            
            # 添加每 5 分钟检查一次的任务（可选）
            self.scheduler.add_job(
                func=self.check_pending_emails,
                trigger=CronTrigger(minute='*/5', timezone='UTC'),
                id='check_pending_emails',
                name='检查待处理邮件',
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("定时任务调度器启动成功")
            
            # 打印已添加的任务
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                logger.info(f"已添加任务: {job.name} (ID: {job.id})")
                
        except Exception as e:
            logger.error(f"启动定时任务调度器失败: {str(e)}")
            raise
    
    def stop(self):
        """停止调度器"""
        try:
            self.scheduler.shutdown()
            logger.info("定时任务调度器已停止")
        except Exception as e:
            logger.error(f"停止定时任务调度器失败: {str(e)}")
    
    async def daily_email_processing(self):
        """每日邮件处理任务"""
        logger.info("开始执行每日邮件处理任务")
        
        try:
            # 1. 同步 Gmail 邮件
            await self._sync_emails()
            
            # 2. 翻译未翻译的邮件
            await self._translate_emails()
            
            # 3. 发布到微信公众号
            await self._publish_emails()
            
            logger.success("每日邮件处理任务完成")
            
        except Exception as e:
            logger.error(f"每日邮件处理任务执行失败: {str(e)}")
            raise
    
    async def check_pending_emails(self):
        """检查待处理邮件"""
        try:
            db = SessionLocal()
            
            # 统计待处理邮件数量
            pending_translation = db.query(Email).filter(
                Email.translated_content.is_(None),
                Email.is_published == False
            ).count()
            
            pending_publish = db.query(Email).filter(
                Email.translated_content.isnot(None),
                Email.is_published == False
            ).count()
            
            if pending_translation > 0 or pending_publish > 0:
                logger.info(f"待处理邮件统计 - 待翻译: {pending_translation}, 待发布: {pending_publish}")
            
            db.close()
            
        except Exception as e:
            logger.error(f"检查待处理邮件失败: {str(e)}")
    
    async def _sync_emails(self):
        """同步 Gmail 邮件"""
        logger.info("开始同步 Gmail 邮件")
        
        try:
            # 获取未读邮件
            messages = self.gmail_service.get_unread_emails(max_results=settings.email_batch_size)
            
            if not messages:
                logger.info("没有新的未读邮件")
                return
            
            db = SessionLocal()
            synced_count = 0
            
            for message in messages:
                try:
                    # 检查邮件是否已存在
                    existing_email = db.query(Email).filter(
                        Email.gmail_id == message['id']
                    ).first()
                    
                    if existing_email:
                        continue
                    
                    # 获取邮件详情
                    email_data = self.gmail_service.get_email_details(message['id'])
                    
                    if email_data:
                        # 创建邮件记录
                        new_email = Email(
                            gmail_id=email_data['gmail_id'],
                            subject=email_data['subject'],
                            sender=email_data['sender'],
                            recipient=email_data['recipient'],
                            content=email_data['content'],
                            html_content=email_data['html_content'],
                            received_at=datetime.now(timezone.utc)
                        )
                        
                        db.add(new_email)
                        synced_count += 1
                        
                except Exception as e:
                    logger.error(f"同步邮件 {message['id']} 失败: {str(e)}")
                    continue
            
            db.commit()
            db.close()
            
            logger.success(f"成功同步 {synced_count} 封邮件")
            
        except Exception as e:
            logger.error(f"同步 Gmail 邮件失败: {str(e)}")
            raise
    
    async def _translate_emails(self):
        """翻译邮件内容"""
        logger.info("开始翻译邮件内容")
        
        try:
            db = SessionLocal()
            
            # 获取未翻译的邮件
            untranslated_emails = db.query(Email).filter(
                Email.translated_content.is_(None),
                Email.is_published == False
            ).limit(settings.email_batch_size).all()
            
            if not untranslated_emails:
                logger.info("没有需要翻译的邮件")
                db.close()
                return
            
            translated_count = 0
            
            for email in untranslated_emails:
                try:
                    # 翻译纯文本内容
                    if email.content:
                        text_result = self.translation_service.translate_text(email.content)
                        if text_result.success:
                            email.translated_content = text_result.translated_content
                            translated_count += 1
                        else:
                            logger.warning(f"翻译邮件 {email.id} 文本内容失败: {text_result.error_message}")
                    
                    # 翻译 HTML 内容
                    if email.html_content:
                        html_result = self.translation_service.translate_html(email.html_content)
                        if html_result.success:
                            email.translated_html_content = html_result.translated_content
                        else:
                            logger.warning(f"翻译邮件 {email.id} HTML 内容失败: {html_result.error_message}")
                    
                except Exception as e:
                    logger.error(f"翻译邮件 {email.id} 失败: {str(e)}")
                    continue
            
            db.commit()
            db.close()
            
            logger.success(f"成功翻译 {translated_count} 封邮件")
            
        except Exception as e:
            logger.error(f"翻译邮件内容失败: {str(e)}")
            raise
    
    async def _publish_emails(self):
        """发布邮件到微信公众号"""
        logger.info("开始发布邮件到微信公众号")
        
        try:
            db = SessionLocal()
            
            # 获取已翻译但未发布的邮件
            ready_emails = db.query(Email).filter(
                Email.translated_content.isnot(None),
                Email.is_published == False
            ).limit(settings.email_batch_size).all()
            
            if not ready_emails:
                logger.info("没有需要发布的邮件")
                db.close()
                return
            
            published_count = 0
            
            for email in ready_emails:
                try:
                    # 发布到微信公众号
                    from .schemas.email import WeChatPublishRequest
                    
                    publish_request = WeChatPublishRequest(
                        email_id=email.id,
                        title=email.subject,
                        content=email.translated_html_content or email.translated_content,
                        author="邮件转发"
                    )
                    
                    result = self.wechat_service.publish_email(publish_request)
                    
                    if result.success:
                        email.is_published = True
                        email.published_at = datetime.now(timezone.utc)
                        published_count += 1
                        logger.success(f"成功发布邮件 {email.id}: {email.subject}")
                    else:
                        logger.warning(f"发布邮件 {email.id} 失败: {result.message}")
                    
                except Exception as e:
                    logger.error(f"发布邮件 {email.id} 失败: {str(e)}")
                    continue
            
            db.commit()
            db.close()
            
            logger.success(f"成功发布 {published_count} 封邮件到微信公众号")
            
        except Exception as e:
            logger.error(f"发布邮件到微信公众号失败: {str(e)}")
            raise
    
    def _job_executed(self, event):
        """任务执行完成事件"""
        logger.info(f"任务执行完成: {event.job_id} - {event.job}")
    
    def _job_error(self, event):
        """任务执行错误事件"""
        logger.error(f"任务执行失败: {event.job_id} - {event.exception}")


# 全局调度器实例
scheduler = TaskScheduler()
