"""
FastAPI 应用入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import sys

from .config import settings
from .database import create_tables
from .routes import router
from .scheduler import scheduler


# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)

if settings.log_file:
    import os
    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger.add(
        settings.log_file,
        rotation="500 MB",
        retention="10 days",
        level=settings.log_level,
        encoding="utf-8"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info(f"启动 {settings.app_name} v{settings.app_version}")
    
    # 创建数据库表
    try:
        create_tables()
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库表创建失败: {str(e)}")
    
    # 启动定时任务调度器
    try:
        scheduler.start()
        logger.info("定时任务调度器启动成功")
    except Exception as e:
        logger.error(f"定时任务调度器启动失败: {str(e)}")
    
    yield
    
    # 关闭时
    logger.info("正在关闭服务...")
    
    # 停止定时任务调度器
    try:
        scheduler.stop()
        logger.info("定时任务调度器已停止")
    except Exception as e:
        logger.error(f"停止定时任务调度器失败: {str(e)}")
    
    logger.info(f"关闭 {settings.app_name}")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Gmail 到微信公众号邮件转发服务",
    lifespan=lifespan
)


# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
