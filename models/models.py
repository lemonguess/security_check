import sys
import os

# 添加项目根目录到Python路径
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from models.enums import RiskLevel, ContentCategory, EngineType, ProcessingStatus
else:
    try:
        from .enums import RiskLevel, ContentCategory, EngineType, ProcessingStatus
    except ImportError:
        from models.enums import RiskLevel, ContentCategory, EngineType, ProcessingStatus

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

class CheckRequest(BaseModel):
    filePathList: list[str]

class CheckResponse(BaseModel):
    file_path: str
    task_id: str
    msg: str

class TaskStatusRequest(BaseModel):
    task_ids: List[str]  # 接口入参为任务 ID 列表

class TaskStatusResponse(BaseModel):
    task_id: str  # 任务 ID
    status: int   # 任务状态


class ModerationRequest(BaseModel):
    """审核请求模型"""
    content: str = Field(..., description="待审核的内容", min_length=1)
    content_id: Optional[str] = Field(None, description="内容唯一标识")
    content_type: str = Field("text", description="内容类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="附加元数据")
    priority: int = Field(0, description="优先级，数值越大优先级越高")
    timeout: Optional[float] = Field(30.0, description="超时时间（秒）")

    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("内容不能为空")
        if len(v) > 10000:  # 限制内容长度
            raise ValueError("内容长度不能超过10000字符")
        return v.strip()


class SensitiveMatch(BaseModel):
    """敏感内容匹配结果"""
    word: str = Field(..., description="匹配的词汇")
    category: str = Field(..., description="分类")
    position: int = Field(..., description="在文本中的位置")
    context: str = Field("", description="上下文")
    pattern_name: Optional[str] = Field(None, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="置信度")


class DetectionMatch(BaseModel):
    """检测匹配结果"""
    type: str = Field(..., description="匹配类型")
    value: str = Field(..., description="匹配的值")
    category: Optional[ContentCategory] = Field(None, description="分类")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    position: Optional[List[int]] = Field(None, description="在文本中的位置")
    context: Optional[str] = Field(None, description="上下文信息")


class AIResult(BaseModel):
    """AI检测结果"""
    risk_level: RiskLevel = Field(..., description="风险等级")
    violated_categories: List[ContentCategory] = Field(default_factory=list, description="违规分类")
    risk_score: float = Field(0.0, ge=0.0, le=1.0, description="风险分数")
    risk_reasons: List[str] = Field(default_factory=list, description="风险原因")
    detailed_analysis: str = Field("", description="详细分析")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="置信度")
    suspicious_segments: List[str] = Field(default_factory=list, description="可疑片段")
    keywords_found: List[str] = Field(default_factory=list, description="发现的关键词")
    evasion_techniques: List[str] = Field(default_factory=list, description="识别到的规避技术")
    reasoning: str = Field("", description="推理过程")
    recommendations: List[str] = Field(default_factory=list, description="处理建议")
    model_name: Optional[str] = Field(None, description="使用的模型")
    processing_time: Optional[float] = Field(None, description="处理时间")


class RuleResult(BaseModel):
    """规则引擎检测结果"""
    risk_level: RiskLevel = Field(..., description="风险等级")
    violated_categories: List[ContentCategory] = Field(default_factory=list, description="违规分类")
    risk_score: float = Field(0.0, ge=0.0, le=1.0, description="风险分数")
    risk_reasons: List[str] = Field(default_factory=list, description="风险原因")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="置信度")
    sensitive_matches: List[SensitiveMatch] = Field(default_factory=list, description="敏感词匹配")
    matches: List[DetectionMatch] = Field(default_factory=list, description="匹配结果")
    sensitive_words: List[str] = Field(default_factory=list, description="敏感词")
    triggered_rules: List[str] = Field(default_factory=list, description="触发的规则")
    processing_time: Optional[float] = Field(None, description="处理时间")


class FusionResult(BaseModel):
    """融合结果"""
    risk_level: RiskLevel = Field(..., description="最终风险等级")
    violated_categories: List[ContentCategory] = Field(default_factory=list, description="违规分类")
    risk_score: float = Field(0.0, ge=0.0, le=1.0, description="最终风险分数")
    risk_reasons: List[str] = Field(default_factory=list, description="风险原因")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="置信度")
    ai_result: Optional[AIResult] = Field(None, description="AI结果")
    rule_result: Optional[RuleResult] = Field(None, description="规则结果")
    fusion_strategy: str = Field("weighted", description="融合策略")
    engines_used: List[EngineType] = Field(default_factory=list, description="使用的引擎")
    detailed_analysis: str = Field("", description="详细分析")
    processing_time: float = Field(0.0, description="处理时间")


class ModerationResult(BaseModel):
    """完整的审核结果"""
    content_id: str = Field(..., description="内容ID")
    original_content: str = Field(..., description="原始内容")
    status: ProcessingStatus = Field(ProcessingStatus.COMPLETED, description="处理状态")

    # 各引擎结果
    ai_result: Optional[AIResult] = Field(None, description="AI检测结果")
    rule_result: Optional[RuleResult] = Field(None, description="规则检测结果")
    fusion_result: Optional[FusionResult] = Field(None, description="融合结果")

    # 最终结果
    final_decision: RiskLevel = Field(..., description="最终决策")
    final_score: float = Field(..., ge=0.0, le=1.0, description="最终分数")
    masked_content: Optional[str] = Field(None, description="脱敏后内容")

    # 元信息
    processing_time: float = Field(..., description="总处理时间")
    timestamp: datetime = Field(default_factory=datetime.now, description="处理时间戳")
    engines_used: List[EngineType] = Field(default_factory=list, description="使用的引擎")

    # 统计信息
    total_matches: int = Field(0, description="总匹配数")
    categories_detected: List[ContentCategory] = Field(default_factory=list, description="检测到的分类")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BatchModerationRequest(BaseModel):
    """批量审核请求"""
    contents: List[str] = Field(..., description="内容列表", min_length=1, max_length=100)
    content_ids: Optional[List[str]] = Field(None, description="内容ID列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="附加元数据")
    parallel: bool = Field(True, description="是否并行处理")

    @validator('content_ids')
    def validate_content_ids(cls, v, values):
        if v is not None and 'contents' in values:
            if len(v) != len(values['contents']):
                raise ValueError("content_ids长度必须与contents长度一致")
        return v


class BatchModerationResult(BaseModel):
    """批量审核结果"""
    total_count: int = Field(..., description="总数量")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    results: List[ModerationResult] = Field(..., description="审核结果列表")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误信息")
    processing_time: float = Field(..., description="总处理时间")
    timestamp: datetime = Field(default_factory=datetime.now, description="处理时间戳")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemMetrics(BaseModel):
    """系统指标"""
    total_requests: int = Field(0, description="总请求数")
    successful_requests: int = Field(0, description="成功请求数")
    failed_requests: int = Field(0, description="失败请求数")
    average_processing_time: float = Field(0.0, description="平均处理时间")
    risk_level_distribution: Dict[RiskLevel, int] = Field(default_factory=dict, description="风险等级分布")
    category_distribution: Dict[ContentCategory, int] = Field(default_factory=dict, description="分类分布")
    engine_performance: Dict[EngineType, Dict[str, float]] = Field(default_factory=dict, description="引擎性能")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }