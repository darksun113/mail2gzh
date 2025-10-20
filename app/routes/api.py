"""
API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json

from ..database import get_db
from ..models.email import Email
from ..config import settings
from ..schemas.email import (
    EmailCreate, EmailResponse, EmailListResponse, EmailUpdate,
    TranslationRequest, TranslationResponse,
    WeChatPublishRequest, WeChatPublishResponse
)
from ..services.gmail_service import GmailService
from ..services.translation_service import TranslationService
from ..services.wechat_image_service import WeChatImageService
from ..services.wechat_service import WeChatService
from ..scheduler import scheduler
from loguru import logger

router = APIRouter(prefix="/api/v1", tags=["API"])


@router.get("/")
async def root():
    """API 根路径"""
    return {
        "message": "Gmail to WeChat Service API",
        "version": "1.0.0",
        "status": "running"
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@router.post("/emails/sync", response_model=dict)
async def sync_emails(
    max_results: int = Query(default=None, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """同步 Gmail 邮件到数据库"""
    try:
        gmail_service = GmailService()
        if not gmail_service.authenticate():
            raise HTTPException(status_code=500, detail="Gmail API 认证失败")
        
        # 获取未读邮件（如果未指定 max_results，使用配置中的默认值）
        if max_results is None:
            max_results = settings.gmail_max_results
        messages = gmail_service.get_unread_emails(max_results=max_results)
        
        synced_count = 0
        skipped_count = 0
        
        for message in messages:
            # 检查邮件是否已存在
            existing_email = db.query(Email).filter(
                Email.gmail_id == message['gmail_id']
            ).first()
            
            if existing_email:
                skipped_count += 1
                continue
            
            # 创建邮件记录（message 已经包含所有需要的数据）
            new_email = Email(
                gmail_id=message['gmail_id'],
                subject=message['subject'],
                sender=message['sender'],
                recipient=message['recipient'],
                content=message['content'],
                html_content=message['html_content'],
                received_at=datetime.now()  # 需要解析实际时间
            )
            
            db.add(new_email)
            synced_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "synced": synced_count,
            "skipped": skipped_count,
            "total": len(messages)
        }
        
    except Exception as e:
        logger.error(f"同步邮件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"同步邮件失败: {str(e)}")


@router.get("/emails", response_model=EmailListResponse)
async def get_emails(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    is_published: bool = Query(default=None),
    db: Session = Depends(get_db)
):
    """获取邮件列表"""
    try:
        query = db.query(Email)
        
        if is_published is not None:
            query = query.filter(Email.is_published == is_published)
        
        total = query.count()
        
        emails = query.order_by(Email.received_at.desc()).offset(
            (page - 1) * size
        ).limit(size).all()
        
        pages = (total + size - 1) // size
        
        return EmailListResponse(
            emails=emails,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"获取邮件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取邮件列表失败: {str(e)}")


@router.get("/emails/{email_id}", response_model=EmailResponse)
async def get_email(email_id: int, db: Session = Depends(get_db)):
    """获取单个邮件详情"""
    email = db.query(Email).filter(Email.id == email_id).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="邮件不存在")
    
    return email


@router.post("/emails/{email_id}/translate", response_model=dict)
async def translate_email(email_id: int, db: Session = Depends(get_db)):
    """翻译邮件内容"""
    try:
        # 获取邮件
        email = db.query(Email).filter(Email.id == email_id).first()
        
        if not email:
            raise HTTPException(status_code=404, detail="邮件不存在")
        
        if email.translated_content and email.news_source:
            return {
                "success": True,
                "message": "邮件已翻译",
                "email_id": email_id,
                "translated_title": email.subject,
                "news_source": email.news_source
            }
        
        # 翻译服务
        translation_service = TranslationService()
        
        # 准备邮件数据
        email_data = {
            'subject': email.subject,
            'sender': email.sender,
            'html_content': email.html_content or email.content
        }
        
        # 执行翻译
        result = translation_service.translate_email(email_data)
        
        if result.get('error'):
            raise Exception(result['error'])
        
        # 更新邮件记录
        email.translated_content = result.get('translated_html', '')
        email.news_source = result.get('news_source', email.sender)
        email.translated_summary = result.get('translated_summary', '')
        email.wechat_html_content = result.get('translated_html', '')
        email.content_length = result.get('content_length', 0)
        email.images_processed = False
        email.publish_ready = result.get('publish_ready', False)
        email.images_info = json.dumps(result.get('images_info', []))
        
        db.commit()
        db.refresh(email)
        
        return {
            "success": True,
            "message": "邮件翻译完成",
            "email_id": email_id,
            "translated_title": result.get('translated_title', email.subject),
            "news_source": result.get('news_source', email.sender),
            "content_length": result.get('content_length', 0),
            "publish_ready": result.get('publish_ready', False),
            "images_count": len(result.get('images_info', []))
        }
        
    except Exception as e:
        logger.error(f"翻译邮件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"翻译邮件失败: {str(e)}")


@router.post("/emails/{email_id}/process-images", response_model=dict)
async def process_email_images(email_id: int, db: Session = Depends(get_db)):
    """处理邮件图片"""
    try:
        # 获取邮件
        email = db.query(Email).filter(Email.id == email_id).first()
        
        if not email:
            raise HTTPException(status_code=404, detail="邮件不存在")
        
        if email.images_processed:
            return {
                "success": True,
                "message": "图片已处理",
                "email_id": email_id
            }
        
        if not email.images_info:
            return {
                "success": True,
                "message": "邮件中无图片",
                "email_id": email_id
            }
        
        # 图片处理服务
        image_service = WeChatImageService()
        
        # 解析图片信息
        images_info = json.loads(email.images_info) if isinstance(email.images_info, str) else email.images_info
        
        # 处理图片
        result = image_service.process_images(images_info, email.wechat_html_content or email.translated_html_content)
        
        if result['success']:
            # 更新邮件记录
            email.wechat_html_content = result['updated_html']
            email.images_processed = result['images_processed']
            email.publish_ready = True
            
            db.commit()
            db.refresh(email)
        
        return {
            "success": result['success'],
            "message": "图片处理完成" if result['success'] else "图片处理失败",
            "email_id": email_id,
            "processed_images": len(result.get('processed_images', [])),
            "failed_images": len(result.get('failed_images', [])),
            "images_processed": result.get('images_processed', False)
        }
        
    except Exception as e:
        logger.error(f"处理邮件图片失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理邮件图片失败: {str(e)}")


@router.post("/emails/batch-translate", response_model=dict)
async def batch_translate_emails(
    max_emails: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """批量翻译邮件"""
    try:
        # 获取未翻译的邮件
        untranslated_emails = db.query(Email).filter(
            Email.translated_content.is_(None)
        ).limit(max_emails).all()
        
        if not untranslated_emails:
            return {
                "success": True,
                "message": "没有需要翻译的邮件",
                "translated_count": 0
            }
        
        translation_service = TranslationService()
        translated_count = 0
        errors = []
        
        for email in untranslated_emails:
            try:
                # 准备邮件数据
                email_data = {
                    'subject': email.subject,
                    'sender': email.sender,
                    'html_content': email.html_content or email.content
                }
                
                # 执行翻译
                result = translation_service.translate_email(email_data)
                
                if not result.get('error'):
                    # 更新邮件记录
                    email.translated_content = result.get('translated_html', '')
                    email.news_source = result.get('news_source', email.sender)
                    email.translated_summary = result.get('translated_summary', '')
                    email.wechat_html_content = result.get('translated_html', '')
                    email.content_length = result.get('content_length', 0)
                    email.images_processed = False
                    email.publish_ready = result.get('publish_ready', False)
                    email.images_info = json.dumps(result.get('images_info', []))
                    
                    translated_count += 1
                else:
                    errors.append(f"邮件 {email.id} 翻译失败: {result['error']}")
                    
            except Exception as e:
                error_msg = f"邮件 {email.id} 翻译异常: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"批量翻译完成，成功 {translated_count} 封",
            "translated_count": translated_count,
            "total_processed": len(untranslated_emails),
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"批量翻译邮件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量翻译邮件失败: {str(e)}")


@router.get("/emails/{email_id}/preview", response_model=dict)
async def preview_wechat_content(email_id: int, db: Session = Depends(get_db)):
    """预览微信公众号内容"""
    try:
        # 获取邮件
        email = db.query(Email).filter(Email.id == email_id).first()
        
        if not email:
            raise HTTPException(status_code=404, detail="邮件不存在")
        
        if not email.translated_content:
            raise HTTPException(status_code=400, detail="邮件未翻译")
        
        # 解析图片信息
        images_info = []
        if email.images_info:
            try:
                images_info = json.loads(email.images_info) if isinstance(email.images_info, str) else email.images_info
            except:
                images_info = []
        
        return {
            "success": True,
            "email_id": email_id,
            "translated_title": email.subject,
            "news_source": email.news_source,
            "translated_summary": email.translated_summary,
            "wechat_html_content": email.wechat_html_content,
            "content_length": email.content_length,
            "publish_ready": email.publish_ready,
            "images_processed": email.images_processed,
            "images_count": len(images_info),
            "images_info": images_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览微信内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"预览微信内容失败: {str(e)}")


@router.post("/emails/{email_id}/publish", response_model=WeChatPublishResponse)
async def publish_email(email_id: int, db: Session = Depends(get_db)):
    """发布邮件到微信公众号"""
    try:
        # 获取邮件
        email = db.query(Email).filter(Email.id == email_id).first()
        
        if not email:
            raise HTTPException(status_code=404, detail="邮件不存在")
        
        if email.is_published:
            raise HTTPException(status_code=400, detail="邮件已发布")
        
        if not email.translated_content:
            raise HTTPException(status_code=400, detail="邮件未翻译，请先翻译")
        
        # 微信公众号服务
        wechat_service = WeChatService()
        
        # 发布请求
        publish_request = WeChatPublishRequest(
            email_id=email.id,
            title=email.subject,
            content=email.translated_html_content or email.translated_content,
            author="邮件转发"
        )
        
        result = wechat_service.publish_email(publish_request)
        
        if result.success:
            email.is_published = True
            email.published_at = datetime.now()
            db.commit()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发布邮件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发布邮件失败: {str(e)}")


@router.post("/workflow/auto-process", response_model=dict)
async def auto_process_emails(
    max_emails: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """自动处理邮件工作流：同步 -> 翻译 -> 发布"""
    try:
        results = {
            "synced": 0,
            "translated": 0,
            "published": 0,
            "errors": []
        }
        
        # 1. 同步邮件
        gmail_service = GmailService()
        messages = gmail_service.get_unread_emails(max_results=max_emails)
        
        for message in messages:
            try:
                # 检查是否已存在
                existing_email = db.query(Email).filter(
                    Email.gmail_id == message['id']
                ).first()
                
                if existing_email:
                    continue
                
                # 获取邮件详情
                email_data = gmail_service.get_email_details(message['id'])
                
                if not email_data:
                    continue
                
                # 创建邮件记录
                new_email = Email(
                    gmail_id=email_data['gmail_id'],
                    subject=email_data['subject'],
                    sender=email_data['sender'],
                    recipient=email_data['recipient'],
                    content=email_data['content'],
                    html_content=email_data['html_content'],
                    received_at=datetime.now()
                )
                
                db.add(new_email)
                db.flush()
                
                results["synced"] += 1
                
                # 2. 翻译邮件
                translation_service = TranslationService()
                
                if new_email.content:
                    text_result = translation_service.translate_text(new_email.content)
                    if text_result.success:
                        new_email.translated_content = text_result.translated_content
                        results["translated"] += 1
                
                if new_email.html_content:
                    html_result = translation_service.translate_html(new_email.html_content)
                    if html_result.success:
                        new_email.translated_html_content = html_result.translated_content
                
                db.flush()
                
                # 3. 发布到微信公众号
                if new_email.translated_content:
                    wechat_service = WeChatService()
                    
                    publish_request = WeChatPublishRequest(
                        email_id=new_email.id,
                        title=new_email.subject,
                        content=new_email.translated_html_content or new_email.translated_content,
                        author="邮件转发"
                    )
                    
                    publish_result = wechat_service.publish_email(publish_request)
                    
                    if publish_result.success:
                        new_email.is_published = True
                        new_email.published_at = datetime.now()
                        results["published"] += 1
                
            except Exception as e:
                error_msg = f"处理邮件 {message['id']} 失败: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        db.commit()
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"自动处理邮件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"自动处理邮件失败: {str(e)}")


@router.post("/test/gmail", response_model=dict)
async def test_gmail_connection():
    """测试 Gmail API 连接"""
    try:
        gmail_service = GmailService()
        success = gmail_service.authenticate()
        
        return {
            "service": "Gmail",
            "connected": success,
            "message": "Gmail API 连接成功" if success else "Gmail API 连接失败"
        }
    except Exception as e:
        return {
            "service": "Gmail",
            "connected": False,
            "message": str(e)
        }


@router.post("/test/wechat", response_model=dict)
async def test_wechat_connection():
    """测试微信公众号 API 连接"""
    try:
        wechat_service = WeChatService()
        success = wechat_service.test_connection()
        
        return {
            "service": "WeChat",
            "connected": success,
            "message": "微信公众号 API 连接成功" if success else "微信公众号 API 连接失败"
        }
    except Exception as e:
        return {
            "service": "WeChat",
            "connected": False,
            "message": str(e)
        }


@router.get("/scheduler/status", response_model=dict)
async def get_scheduler_status():
    """获取定时任务调度器状态"""
    try:
        jobs = scheduler.scheduler.get_jobs()
        job_list = []
        
        for job in jobs:
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            job_list.append(job_info)
        
        return {
            "scheduler_running": scheduler.scheduler.running,
            "jobs": job_list,
            "total_jobs": len(job_list)
        }
    except Exception as e:
        logger.error(f"获取调度器状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取调度器状态失败: {str(e)}")


@router.post("/scheduler/trigger/daily", response_model=dict)
async def trigger_daily_task():
    """手动触发每日邮件处理任务"""
    try:
        # 在后台运行任务
        import asyncio
        asyncio.create_task(scheduler.daily_email_processing())
        
        return {
            "success": True,
            "message": "每日邮件处理任务已触发"
        }
    except Exception as e:
        logger.error(f"触发每日任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"触发每日任务失败: {str(e)}")


@router.post("/scheduler/trigger/check", response_model=dict)
async def trigger_check_task():
    """手动触发检查待处理邮件任务"""
    try:
        # 在后台运行任务
        import asyncio
        asyncio.create_task(scheduler.check_pending_emails())
        
        return {
            "success": True,
            "message": "检查待处理邮件任务已触发"
        }
    except Exception as e:
        logger.error(f"触发检查任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"触发检查任务失败: {str(e)}")


@router.get("/scheduler/logs", response_model=dict)
async def get_scheduler_logs(lines: int = Query(default=50, ge=1, le=500)):
    """获取调度器日志"""
    try:
        import os
        log_file = settings.log_file
        
        if not log_file or not os.path.exists(log_file):
            return {
                "success": False,
                "message": "日志文件不存在",
                "logs": []
            }
        
        # 读取最后 N 行日志
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # 过滤调度器相关日志
        scheduler_logs = []
        for line in recent_lines:
            if any(keyword in line.lower() for keyword in ['scheduler', '定时任务', 'daily_email_processing', 'check_pending_emails']):
                scheduler_logs.append(line.strip())
        
        return {
            "success": True,
            "total_lines": len(scheduler_logs),
            "logs": scheduler_logs
        }
    except Exception as e:
        logger.error(f"获取调度器日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取调度器日志失败: {str(e)}")
