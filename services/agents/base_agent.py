"""
AI代理基类
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from models.models import AIResult
from models.enums import RiskLevel, ContentCategory
from utils.exceptions import ModelError, TimeoutError
from utils.logger import get_logger
from utils.metrics import get_metrics_collector, record_timing


class BaseAgent(ABC):
    """AI代理基类"""
    
    def __init__(
        self, 
        name: str,
        model_config: Dict[str, Any],
        timeout: float = 30.0,
        max_retries: int = 2
    ):
        self.name = name
        self.model_config = model_config
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = get_logger(f"agent.{name}")
        self.metrics = get_metrics_collector()
        
        # 初始化计数器
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        
    @abstractmethod
    def process(self, content: str, **kwargs) -> AIResult:
        """处理内容，返回AI审核结果"""
        pass
    
    def _validate_input(self, content: str) -> None:
        """验证输入内容"""
        if not content or not content.strip():
            raise ValueError("内容不能为空")
        
        if len(content) > 10000:
            raise ValueError("内容长度超过限制")
    
    def _create_default_result(
        self, 
        content: str, 
        error_msg: str = "处理失败"
    ) -> AIResult:
        """创建默认的错误结果"""
        return AIResult(
            risk_level=RiskLevel.SUSPICIOUS,
            confidence_score=0.0,
            categories=[ContentCategory.OTHER],
            suspicious_segments=[],
            keywords_found=[],
            reasoning=error_msg,
            recommendations=["建议人工审核"],
            model_name=self.model_config.get("model_name", "unknown"),
            processing_time=0.0
        )
    
    def _record_metrics(
        self, 
        processing_time: float, 
        status: str = "success"
    ):
        """记录指标"""
        self.metrics.record_ai_model_performance(
            model_name=self.model_config.get("model_name", "unknown"),
            processing_time=processing_time
        )
        
        if status == "success":
            self.success_count += 1
        else:
            self.error_count += 1
            
        self.request_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取代理统计信息"""
        total = self.request_count
        success_rate = (self.success_count / total) if total > 0 else 0
        error_rate = (self.error_count / total) if total > 0 else 0
        
        return {
            "name": self.name,
            "model_config": self.model_config,
            "request_count": total,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "error_rate": error_rate
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 简单的健康检查
            start_time = time.time()
            test_result = self.process("测试内容")
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": duration,
                "model": self.model_config.get("model_name"),
                "test_success": True
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e),
                "model": self.model_config.get("model_name"),
                "test_success": False
            } 