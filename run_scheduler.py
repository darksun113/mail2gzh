#!/usr/bin/env python3
"""
Mail2GZH 定时任务服务启动脚本
独立运行定时任务，不启动 Web 服务
"""

import asyncio
import signal
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.scheduler import scheduler
from app.database import create_tables
from loguru import logger


def setup_logging():
    """设置日志配置"""
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


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"接收到信号 {signum}，正在停止定时任务服务...")
    scheduler.stop()
    sys.exit(0)


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("    Mail2GZH 定时任务服务")
    logger.info("=" * 50)
    
    try:
        # 创建数据库表
        logger.info("初始化数据库...")
        create_tables()
        logger.success("数据库初始化完成")
        
        # 启动定时任务调度器
        logger.info("启动定时任务调度器...")
        scheduler.start()
        logger.success("定时任务调度器启动成功")
        
        # 显示已添加的任务
        jobs = scheduler.scheduler.get_jobs()
        logger.info(f"已添加 {len(jobs)} 个定时任务:")
        for job in jobs:
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S UTC') if job.next_run_time else "未计划"
            logger.info(f"  - {job.name} (ID: {job.id}) - 下次运行: {next_run}")
        
        logger.info("定时任务服务运行中...")
        logger.info("按 Ctrl+C 停止服务")
        
        # 保持服务运行
        while True:
            await asyncio.sleep(60)  # 每分钟检查一次
            
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在停止服务...")
    except Exception as e:
        logger.error(f"定时任务服务运行失败: {str(e)}")
        raise
    finally:
        scheduler.stop()
        logger.info("定时任务服务已停止")


if __name__ == "__main__":
    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 设置日志
    setup_logging()
    
    # 运行主函数
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务已停止")
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        sys.exit(1)
