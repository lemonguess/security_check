from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from utils.logger import get_logger
import json

router = APIRouter(tags=["内容管理"])
logger = get_logger("content")


class ContentItem(BaseModel):
    """内容项模型"""
    id: int
    title: str
    content: Optional[str] = None
    url: str
    images: List[str] = []
    audios: List[str] = []
    videos: List[str] = []
    publish_time: Optional[str] = None
    column_type: str
    audit_status: Optional[str] = None  # 审核状态


class ContentListResponse(BaseModel):
    """内容列表响应模型"""
    success: bool
    data: dict
    message: Optional[str] = None


class ContentListData(BaseModel):
    """内容列表数据模型"""
    items: List[ContentItem]
    total: int
    page: int
    page_size: int


@router.get("/list", response_model=ContentListResponse, summary="获取内容列表")
async def get_content_list(
    column_type: Optional[str] = Query(None, description="栏目类型：时政要闻、行业热点、川烟动态、媒体报道"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量")
):
    """
    获取指定栏目类型的内容列表
    
    支持的栏目类型：
    - 时政要闻
    - 行业热点
    - 川烟动态
    - 媒体报道
    """
    logger.info(f"获取内容列表，栏目类型: {column_type}, 页码: {page}, 每页: {page_size}")
    
    try:
        from models.database import Contents
        
        # 验证栏目类型
        valid_column_types = ["时政要闻", "行业热点", "川烟动态", "媒体报道"]
        if not column_type or column_type.strip() == "":
            raise HTTPException(status_code=400, detail="栏目类型不能为空，请选择有效的栏目类型")
        if column_type not in valid_column_types:
            raise HTTPException(status_code=400, detail=f"不支持的栏目类型: {column_type}，支持的类型: {', '.join(valid_column_types)}")
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 查询数据库
        query = Contents.select().where(
            Contents.column_type == column_type
        ).order_by(Contents.publish_time.desc())
        
        total_count = query.count()
        contents = query.offset(offset).limit(page_size)
        
        # 转换为响应格式
        content_items = []
        for content in contents:
            content_item = ContentItem(
                id=content.id,
                title=content.title or "",
                content=content.content,
                url=content.url or "",
                images=json.loads(content.images) if content.images else [],
                audios=json.loads(content.audios) if content.audios else [],
                videos=json.loads(content.videos) if content.videos else [],
                publish_time=content.publish_time,
                column_type=content.column_type,
                audit_status=getattr(content, 'audit_status', 'pending')
            )
            content_items.append(content_item)
        
        # 构造响应数据
        data = {
            "items": content_items,
            "total": total_count,
            "page": page,
            "page_size": page_size
        }
        
        return ContentListResponse(
            success=True,
            data=data,
            message=f"成功获取{column_type} {len(content_items)} 条内容（共{total_count}条）"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取内容列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取内容列表失败: {str(e)}")