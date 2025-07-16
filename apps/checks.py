from fastapi import HTTPException, APIRouter, File, UploadFile
from models.models import CheckRequest, CheckResponse, TaskStatusResponse, TaskStatusRequest
from utils.logger import logger
from services.wangyiyunsdk import (
    check_images_service,
    check_audios_service,
    check_videos_service
)
from models.database import Task  # 新增导入 Task 模型
from typing import List  # 新增导入 List 类型
import tempfile
import os
import shutil

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

# 新增文件上传接口
@check_router.post("/images")
async def check_uploaded_images(images: List[UploadFile] = File(...)):
    """上传图片文件进行检测"""
    logger.info(f"Starting uploaded image check for {len(images)} files")
    temp_files = []
    try:
        file_paths = []
        for image in images:
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1])
            temp_files.append(temp_file.name)
            
            # 保存上传的文件到临时文件
            with open(temp_file.name, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            file_paths.append(temp_file.name)
        
        # 调用检测服务
        results = check_images_service(file_paths)
        
        return {
            "success": True,
            "data": {
                "final_decision": "SAFE" if all(r.suggestion == "pass" for r in results) else "RISKY",
                "final_score": sum(r.rate for r in results) / len(results) if results else 0,
                "processing_time": 1.0,
                "risk_reasons": [r.label for r in results if r.suggestion != "pass"],
                "violated_categories": list(set(r.label for r in results if r.suggestion != "pass")),
                "results": [{
                    "filename": images[i].filename,
                    "suggestion": r.suggestion,
                    "rate": r.rate,
                    "label": r.label
                } for i, r in enumerate(results)]
            }
        }
    except Exception as e:
        logger.error(f"Error during uploaded image check: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理临时文件
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass

@check_router.post("/audios")
async def check_uploaded_audios(audios: List[UploadFile] = File(...)):
    """上传音频文件进行检测"""
    logger.info(f"Starting uploaded audio check for {len(audios)} files")
    temp_files = []
    try:
        file_paths = []
        for audio in audios:
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1])
            temp_files.append(temp_file.name)
            
            # 保存上传的文件到临时文件
            with open(temp_file.name, "wb") as buffer:
                shutil.copyfileobj(audio.file, buffer)
            
            file_paths.append(temp_file.name)
        
        # 调用检测服务
        results = check_audios_service(file_paths)
        
        return {
            "success": True,
            "data": {
                "final_decision": "SAFE" if all(r.suggestion == "pass" for r in results) else "RISKY",
                "final_score": sum(r.rate for r in results) / len(results) if results else 0,
                "processing_time": 1.0,
                "risk_reasons": [r.label for r in results if r.suggestion != "pass"],
                "violated_categories": list(set(r.label for r in results if r.suggestion != "pass")),
                "results": [{
                    "filename": audios[i].filename,
                    "suggestion": r.suggestion,
                    "rate": r.rate,
                    "label": r.label
                } for i, r in enumerate(results)]
            }
        }
    except Exception as e:
        logger.error(f"Error during uploaded audio check: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理临时文件
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass

@check_router.post("/videos")
async def check_uploaded_videos(videos: List[UploadFile] = File(...)):
    """上传视频文件进行检测"""
    logger.info(f"Starting uploaded video check for {len(videos)} files")
    temp_files = []
    try:
        file_paths = []
        for video in videos:
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video.filename)[1])
            temp_files.append(temp_file.name)
            
            # 保存上传的文件到临时文件
            with open(temp_file.name, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)
            
            file_paths.append(temp_file.name)
        
        # 调用检测服务
        results = check_videos_service(file_paths)
        
        return {
            "success": True,
            "data": {
                "final_decision": "SAFE" if all(r.suggestion == "pass" for r in results) else "RISKY",
                "final_score": sum(r.rate for r in results) / len(results) if results else 0,
                "processing_time": 1.0,
                "risk_reasons": [r.label for r in results if r.suggestion != "pass"],
                "violated_categories": list(set(r.label for r in results if r.suggestion != "pass")),
                "results": [{
                    "filename": videos[i].filename,
                    "suggestion": r.suggestion,
                    "rate": r.rate,
                    "label": r.label
                } for i, r in enumerate(results)]
            }
        }
    except Exception as e:
        logger.error(f"Error during uploaded video check: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理临时文件
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass