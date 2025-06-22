from fastapi import HTTPException, APIRouter
from models.models import CheckRequest, CheckResponse, TaskStatusResponse, TaskStatusRequest
from utils.logger import logger
from services.wangyiyunsdk import (
    check_images_service,
    check_audios_service,
    check_videos_service
)
from models.database import Task  # 新增导入 Task 模型
from typing import List  # 新增导入 List 类型

check_router = APIRouter(tags=["内容检测sdk"])


@check_router.post("/tasks/status", response_model=List[TaskStatusResponse])
async def get_task_status(request: TaskStatusRequest):
    """
    根据任务 ID 列表查询对应任务的状态
    """
    logger.info("Querying task status")
    try:
        # 查询数据库，获取任务状态
        tasks = Task.select().where(Task.id.in_(request.task_ids))
        # 构造返回值
        return [{"task_id": str(task.id), "status": task.status} for task in tasks]
    except Exception as e:
        logger.error(f"Error during task status query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@check_router.post("/image/check", response_model=list[CheckResponse])
async def check_images(request: CheckRequest):
    logger.info("Starting image check")
    try:
        # 调用服务层函数，构造返回值
        results = check_images_service(request.filePathList)
        return results
    except Exception as e:
        logger.error(f"Error during image check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@check_router.post("/audio/check", response_model=list[CheckResponse])
async def check_audios(request: CheckRequest):
    logger.info("Starting audio check")
    try:
        # 调用服务层函数，构造返回值
        results = check_audios_service(request.filePathList)
        return results
    except Exception as e:
        logger.error(f"Error during audio check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@check_router.post("/video/check", response_model=list[CheckResponse])
async def check_videos(request: CheckRequest):
    logger.info("Starting video check")
    try:
        # 调用服务层函数，构造返回值
        results = check_videos_service(request.filePathList)
        return results
    except Exception as e:
        logger.error(f"Error during video check: {e}")
        raise HTTPException(status_code=500, detail=str(e))