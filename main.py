import os
from contextlib import asynccontextmanager

from services.moderation_service import ModerationService
from utils.config import load_config
from utils.logger import logger
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
from apps.checks import check_router
from apps.moderation import router as moderation_router
from apps.scraper import router as scraper_router
from apps.content import router as content_router
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
# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(scraper_router, prefix="/api/v1/scrape")
app.include_router(check_router, prefix="/api/v1/check")
app.include_router(moderation_router, prefix="/api/v1/moderation")
app.include_router(content_router, prefix="/api/v1/content")


@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open(os.path.join("static", "index.html")) as f:
        return f.read()


@app.get("/api/v1/health", summary="健康检查")
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

@app.get("/api/v1/stats", summary="服务统计")
async def get_stats():
    """获取服务统计信息"""
    try:
        service = app.state.service
        stats = service.get_statistics()

        metrics_collector = get_metrics_collector()
        stats_summary = metrics_collector.get_stats_summary()

        # 格式化为前端期望的数据结构
        formatted_stats = {
            "total_requests": stats_summary.get("total_requests", 0),
            "success_rate": stats_summary.get("success_rate", 0.0),
            "avg_processing_time": stats_summary.get("avg_processing_time", 0.0),
            "today_audits": stats_summary.get("today_audits", 0)
        }

        return {
            "success": True,
            "data": formatted_stats,
            "message": "统计数据获取成功"
        }
    except Exception as e:
        return {
            "success": False,
            "data": {
                "total_requests": 0,
                "success_rate": 0.0,
                "avg_processing_time": 0.0,
                "today_audits": 0
            },
            "message": f"统计信息获取失败: {str(e)}"
        }


if __name__ == '__main__':
    import uvicorn
    import os
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=6188,
        reload=True,
        log_level="info"
    )