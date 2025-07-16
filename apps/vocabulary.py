"""词库管理API"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

from models.database import ViolationWord, db
from utils.logger import get_logger

router = APIRouter(tags=["词库管理"])
logger = get_logger("vocabulary_api")


class ViolationWordCreate(BaseModel):
    """创建违规词请求模型"""
    wrong_input: str = Field(..., min_length=1, max_length=255, description="错误输入")
    correct_input: str = Field(..., min_length=1, max_length=255, description="正确输入")
    violation_score: int = Field(..., ge=1, le=100, description="违规分数(1-100)")
    is_active: bool = Field(True, description="是否启用")
    
    @validator('wrong_input', 'correct_input')
    def validate_inputs(cls, v):
        if not v.strip():
            raise ValueError('输入不能为空或只包含空格')
        return v.strip()


class ViolationWordUpdate(BaseModel):
    """更新违规词请求模型"""
    wrong_input: Optional[str] = Field(None, min_length=1, max_length=255, description="错误输入")
    correct_input: Optional[str] = Field(None, min_length=1, max_length=255, description="正确输入")
    violation_score: Optional[int] = Field(None, ge=1, le=100, description="违规分数(1-100)")
    is_active: Optional[bool] = Field(None, description="是否启用")
    
    @validator('wrong_input', 'correct_input')
    def validate_inputs(cls, v):
        if v is not None and not v.strip():
            raise ValueError('输入不能为空或只包含空格')
        return v.strip() if v else v


class ViolationWordResponse(BaseModel):
    """违规词响应模型"""
    id: int
    wrong_input: str
    correct_input: str
    violation_score: int
    is_active: bool
    created_at: str
    updated_at: str


class ViolationWordListResponse(BaseModel):
    """违规词列表响应模型"""
    total: int
    items: List[ViolationWordResponse]
    page: int
    page_size: int
    total_pages: int


@router.post("/words", response_model=ViolationWordResponse, summary="创建违规词")
async def create_violation_word(word_data: ViolationWordCreate):
    """创建新的违规词"""
    try:
        # 检查是否已存在相同的错误输入
        existing = ViolationWord.select().where(
            ViolationWord.wrong_input == word_data.wrong_input
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"错误输入 '{word_data.wrong_input}' 已存在"
            )
        
        # 创建新记录
        with db.atomic():
            violation_word = ViolationWord.create(
                wrong_input=word_data.wrong_input,
                correct_input=word_data.correct_input,
                violation_score=word_data.violation_score,
                is_active=word_data.is_active
            )
        
        # 重新从数据库读取以确保日期字段格式正确
        violation_word = ViolationWord.get_by_id(violation_word.id)
        
        logger.info(f"创建违规词成功: {word_data.wrong_input} -> {word_data.correct_input}")
        
        return ViolationWordResponse(
            id=violation_word.id,
            wrong_input=violation_word.wrong_input,
            correct_input=violation_word.correct_input,
            violation_score=violation_word.violation_score,
            is_active=violation_word.is_active,
            created_at=violation_word.created_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(violation_word.created_at, datetime) else violation_word.created_at,
            updated_at=violation_word.updated_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(violation_word.updated_at, datetime) else violation_word.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建违规词失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/words", response_model=ViolationWordListResponse, summary="获取违规词列表")
async def get_violation_words(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否启用")
):
    """获取违规词列表"""
    try:
        # 构建查询
        query = ViolationWord.select()
        
        # 添加搜索条件
        if search:
            query = query.where(
                (ViolationWord.wrong_input.contains(search)) |
                (ViolationWord.correct_input.contains(search))
            )
        
        if is_active is not None:
            query = query.where(ViolationWord.is_active == is_active)
        
        # 计算总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        items = query.order_by(ViolationWord.created_at.desc()).offset(offset).limit(page_size)
        
        # 转换为响应模型
        violation_words = []
        for item in items:
            violation_words.append(ViolationWordResponse(
                id=item.id,
                wrong_input=item.wrong_input,
                correct_input=item.correct_input,
                violation_score=item.violation_score,
                is_active=item.is_active,
                created_at=item.created_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(item.created_at, datetime) else item.created_at,
                updated_at=item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(item.updated_at, datetime) else item.updated_at
            ))
        
        total_pages = (total + page_size - 1) // page_size
        
        return ViolationWordListResponse(
            total=total,
            items=violation_words,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"获取违规词列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.get("/words/{word_id}", response_model=ViolationWordResponse, summary="获取违规词详情")
async def get_violation_word(word_id: int):
    """获取单个违规词详情"""
    try:
        violation_word = ViolationWord.get_or_none(ViolationWord.id == word_id)
        
        if not violation_word:
            raise HTTPException(status_code=404, detail="违规词不存在")
        
        return ViolationWordResponse(
            id=violation_word.id,
            wrong_input=violation_word.wrong_input,
            correct_input=violation_word.correct_input,
            violation_score=violation_word.violation_score,
            is_active=violation_word.is_active,
            created_at=violation_word.created_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(violation_word.created_at, datetime) else violation_word.created_at,
            updated_at=violation_word.updated_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(violation_word.updated_at, datetime) else violation_word.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取违规词详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")


@router.put("/words/{word_id}", response_model=ViolationWordResponse, summary="更新违规词")
async def update_violation_word(word_id: int, word_data: ViolationWordUpdate):
    """更新违规词"""
    try:
        violation_word = ViolationWord.get_or_none(ViolationWord.id == word_id)
        
        if not violation_word:
            raise HTTPException(status_code=404, detail="违规词不存在")
        
        # 检查是否有其他记录使用相同的错误输入
        if word_data.wrong_input:
            existing = ViolationWord.select().where(
                (ViolationWord.wrong_input == word_data.wrong_input) &
                (ViolationWord.id != word_id)
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"错误输入 '{word_data.wrong_input}' 已被其他记录使用"
                )
        
        # 更新字段
        with db.atomic():
            if word_data.wrong_input is not None:
                violation_word.wrong_input = word_data.wrong_input
            if word_data.correct_input is not None:
                violation_word.correct_input = word_data.correct_input
            if word_data.violation_score is not None:
                violation_word.violation_score = word_data.violation_score
            if word_data.is_active is not None:
                violation_word.is_active = word_data.is_active
            
            violation_word.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            violation_word.save()
        
        logger.info(f"更新违规词成功: ID={word_id}")
        
        return ViolationWordResponse(
            id=violation_word.id,
            wrong_input=violation_word.wrong_input,
            correct_input=violation_word.correct_input,
            violation_score=violation_word.violation_score,
            is_active=violation_word.is_active,
            created_at=violation_word.created_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(violation_word.created_at, datetime) else violation_word.created_at,
            updated_at=violation_word.updated_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(violation_word.updated_at, datetime) else violation_word.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新违规词失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/words/{word_id}", summary="删除违规词")
async def delete_violation_word(word_id: int):
    """删除违规词"""
    try:
        violation_word = ViolationWord.get_or_none(ViolationWord.id == word_id)
        
        if not violation_word:
            raise HTTPException(status_code=404, detail="违规词不存在")
        
        with db.atomic():
            violation_word.delete_instance()
        
        logger.info(f"删除违规词成功: ID={word_id}")
        
        return {"message": "删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除违规词失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/words/batch", summary="批量导入违规词")
async def batch_import_violation_words(words: List[ViolationWordCreate]):
    """批量导入违规词"""
    try:
        if len(words) > 1000:
            raise HTTPException(status_code=400, detail="单次最多导入1000条记录")
        
        success_count = 0
        error_count = 0
        errors = []
        
        with db.atomic():
            for i, word_data in enumerate(words):
                try:
                    # 检查是否已存在
                    existing = ViolationWord.select().where(
                        ViolationWord.wrong_input == word_data.wrong_input
                    ).first()
                    
                    if existing:
                        errors.append(f"第{i+1}行: 错误输入 '{word_data.wrong_input}' 已存在")
                        error_count += 1
                        continue
                    
                    # 创建记录
                    ViolationWord.create(
                        wrong_input=word_data.wrong_input,
                        correct_input=word_data.correct_input,
                        violation_score=word_data.violation_score,
                        is_active=word_data.is_active
                    )
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"第{i+1}行: {str(e)}")
                    error_count += 1
        
        logger.info(f"批量导入完成: 成功={success_count}, 失败={error_count}")
        
        return {
            "message": "批量导入完成",
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[:10]  # 只返回前10个错误
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量导入失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量导入失败: {str(e)}")


@router.post("/words/refresh-cache", summary="刷新违规词缓存")
async def refresh_violation_words_cache():
    """刷新违规词缓存"""
    try:
        # 这里可以通知所有服务实例刷新缓存
        # 目前简单返回成功消息
        logger.info("违规词缓存刷新请求")
        
        return {"message": "缓存刷新请求已发送"}
        
    except Exception as e:
        logger.error(f"刷新缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"刷新缓存失败: {str(e)}")


@router.get("/words/stats", summary="获取违规词统计")
async def get_violation_words_stats():
    """获取违规词统计信息"""
    try:
        total_count = ViolationWord.select().count()
        active_count = ViolationWord.select().where(ViolationWord.is_active == True).count()
        inactive_count = total_count - active_count
        
        # 按分数区间统计
        high_risk_count = ViolationWord.select().where(
            (ViolationWord.violation_score >= 80) & (ViolationWord.is_active == True)
        ).count()
        
        medium_risk_count = ViolationWord.select().where(
            (ViolationWord.violation_score >= 50) & 
            (ViolationWord.violation_score < 80) & 
            (ViolationWord.is_active == True)
        ).count()
        
        low_risk_count = ViolationWord.select().where(
            (ViolationWord.violation_score < 50) & (ViolationWord.is_active == True)
        ).count()
        
        return {
            "total_count": total_count,
            "active_count": active_count,
            "inactive_count": inactive_count,
            "risk_distribution": {
                "high_risk": high_risk_count,  # 80-100分
                "medium_risk": medium_risk_count,  # 50-79分
                "low_risk": low_risk_count  # 1-49分
            }
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")