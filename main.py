import os
from contextlib import asynccontextmanager


from services.moderation_service import ModerationService
from utils.config import load_config
from utils.logger import logger
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
from apps.checks import check_router
from apps.moderation import router as moderation_router
from apps.scraper import router as scraper_router
from task import start_task_loop
import threading

from utils.metrics import get_metrics_collector

# 全局变量
config = None
service = None
# logger = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global config, service, logger

    # 启动时初始化
    try:
        # 启动异步任务
        # threading.Thread(target=start_task_loop, daemon=True).start()
        ...
        # logger = get_logger("api")
        logger.info("API服务启动中...")

        # 加载配置
        config = load_config()

        # 初始化审核服务
        service = ModerationService(config)

        # 设置到app状态中
        app.state.config = config
        app.state.service = service
        app.state.logger = logger

        logger.info("API服务启动完成")
        yield

    except Exception as e:
        logger.error(f"API服务启动失败: {e}")
        raise
    finally:
        # 关闭时清理
        if service:
            await service.__aexit__(None, None, None)
        logger.info("API服务已关闭")
# 创建FastAPI应用
app = FastAPI(
    title="AI内容审核系统",
    description="基于AgentScope的智能内容审核平台",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(scraper_router, prefix="/api/v1")
app.include_router(check_router, prefix="/api/v1/check")
app.include_router(moderation_router, prefix="/api/v1/moderate")



@app.get("/index.html", response_class=HTMLResponse)
async def read_index():
    with open(os.path.join("static", "index.html")) as f:
        return f.read()


@app.get("/health", summary="健康检查")
async def health_check():
    """健康检查接口"""
    try:
        service = app.state.service
        health_status = await service.health_check()

        return {
            "status": health_status.get("status", "unknown"),
            "timestamp": health_status.get("timestamp"),
            "engines": health_status.get("engines", {}),
            "statistics": health_status.get("statistics", {})
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"服务不可用: {str(e)}")

@app.get("/stats", summary="服务统计")
async def get_stats():
    """获取服务统计信息"""
    try:
        service = app.state.service
        stats = service.get_statistics()

        metrics_collector = get_metrics_collector()
        stats_summary = metrics_collector.get_stats_summary()

        return {
            "service_stats": stats,
            "metrics_summary": stats_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计信息获取失败: {str(e)}")


if __name__ == '__main__':
    ...