"""
检测引擎基类
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Union

from models.models import RuleResult, AIResult
from models.enums import EngineType
from utils.logger import get_logger
from utils.metrics import get_metrics_collector


class BaseEngine(ABC):
    """检测引擎基类"""
    
    def __init__(
        self,
        name: str = "base_engine",
        config: Dict[str, Any] = None,
        timeout: float = 30.0
    ):
        self.name = name
        self.config = config or {}
        self.timeout = timeout
        self.logger = get_logger(f"engine.{name}")
        self.metrics = get_metrics_collector()
        
        # 统计信息
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
    
    @abstractmethod
    async def analyze(self, text: str, **kwargs) -> Union[AIResult, RuleResult]:
        """分析文本内容，子类需要实现"""
        pass
    
    def _validate_input(self, content: str):
        """验证输入内容"""
        if not content or not content.strip():
            raise ValueError("内容不能为空")
        
        if len(content) > self.config.get("max_content_length", 10000):
            raise ValueError("内容长度超过限制")
    
    def _record_metrics(self, processing_time: float, status: str = "success"):
        """记录指标"""
        self.request_count += 1
        self.total_processing_time += processing_time
        
        if status == "success":
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        avg_time = (self.total_processing_time / self.request_count 
                   if self.request_count > 0 else 0.0)
        success_rate = (self.success_count / self.request_count 
                       if self.request_count > 0 else 0.0)
        
        return {
            "name": self.name,
            "request_count": self.request_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "average_processing_time": avg_time,
            "total_processing_time": self.total_processing_time
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            start_time = time.time()
            test_result = await self.analyze("测试内容")
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "name": self.name,
                "response_time": duration,
                "test_success": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "name": self.name,
                "error": str(e),
                "test_success": False
            }
    
    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name})" 