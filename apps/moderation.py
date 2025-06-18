"""
内容审核API路由
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field

from models.models import ModerationRequest, ModerationResult, BatchModerationRequest, BatchModerationResult
from models.enums import RiskLevel, ContentCategory


router = APIRouter(tags=["内容审核"])


class ModerationRequestAPI(BaseModel):
    """API审核请求模型"""
    content: str = Field(..., description="待审核的内容", min_length=1, max_length=10000)
    content_id: Optional[str] = Field(None, description="内容唯一标识")
    content_type: str = Field("text", description="内容类型")
    priority: int = Field(0, description="优先级，数值越大优先级越高")
    timeout: Optional[float] = Field(30.0, description="超时时间（秒）")


class BatchModerationRequestAPI(BaseModel):
    """API批量审核请求模型"""
    contents: List[str] = Field(..., description="待审核的内容列表", min_items=1, max_items=100)
    content_ids: Optional[List[str]] = Field(None, description="内容标识列表")
    content_type: str = Field("text", description="内容类型")
    parallel: bool = Field(True, description="是否并行处理")
    timeout: Optional[float] = Field(60.0, description="超时时间（秒）")


@router.post("/single", summary="单条内容审核")
async def moderate_single(request: Request, moderation_request: ModerationRequestAPI):
    """审核单条内容"""
    try:
        service = request.app.state.service
        logger = request.app.state.logger
        
        logger.info(f"收到单条审核请求: {moderation_request.content_id}")
        
        # 执行审核
        result = await service.moderate(
            content=moderation_request.content,
            content_id=moderation_request.content_id,
            content_type=moderation_request.content_type,
            priority=moderation_request.priority,
            timeout=moderation_request.timeout
        )
        
        return {
            "success": True,
            "data": result,
            "message": "审核完成"
        }
        
    except Exception as e:
        logger.error(f"单条审核失败: {e}")
        raise HTTPException(status_code=500, detail=f"审核失败: {str(e)}")


@router.post("/batch", summary="批量内容审核")
async def moderate_batch(request: Request, batch_request: BatchModerationRequestAPI):
    """批量审核内容"""
    try:
        service = request.app.state.service
        logger = request.app.state.logger
        
        logger.info(f"收到批量审核请求: {len(batch_request.contents)} 条内容")
        
        # 执行批量审核
        result = await service.moderate_batch(
            contents=batch_request.contents,
            content_ids=batch_request.content_ids,
            parallel=batch_request.parallel,
            content_type=batch_request.content_type,
            timeout=batch_request.timeout
        )
        
        return {
            "success": True,
            "data": result,
            "message": "批量审核完成"
        }
        
    except Exception as e:
        logger.error(f"批量审核失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量审核失败: {str(e)}")


@router.get("/categories", summary="获取内容分类")
async def get_content_categories():
    """获取内容分类列表"""
    categories = []
    for category in ContentCategory:
        categories.append({
            "name": category.name,
            "value": category.value
        })
    
    return {
        "success": True,
        "categories": categories,
        "message": "分类列表获取成功"
    }


@router.get("/risk-levels", summary="获取风险等级")
async def get_risk_levels():
    """获取风险等级列表"""
    levels = []
    for level in RiskLevel:
        levels.append({
            "name": level.name,
            "value": level.value
        })
    
    return {
        "success": True,
        "risk_levels": levels,
        "message": "风险等级列表获取成功"
    } 