"""
性能指标收集工具
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from threading import Lock
import threading

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from models.enums import RiskLevel, ContentCategory, EngineType


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._lock = Lock()
        
        # 初始化指标
        self._init_metrics()
        
        # 内存中的统计数据
        self._request_times = deque(maxlen=1000)  # 保留最近1000次请求的时间
        self._hourly_stats = defaultdict(lambda: defaultdict(int))
        self._cleanup_thread = None
        self._start_cleanup_thread()
    
    def _init_metrics(self):
        """初始化Prometheus指标"""
        
        # 计数器
        self.requests_total = Counter(
            'moderation_requests_total',
            '审核请求总数',
            ['risk_level', 'status'],
            registry=self.registry
        )
        
        self.engine_requests_total = Counter(
            'moderation_engine_requests_total', 
            '各引擎请求总数',
            ['engine_type', 'status'],
            registry=self.registry
        )
        
        self.categories_detected_total = Counter(
            'moderation_categories_detected_total',
            '检测到的分类总数',
            ['category'],
            registry=self.registry
        )
        
        # 直方图
        self.request_duration = Histogram(
            'moderation_request_duration_seconds',
            '审核请求处理时间',
            ['engine_type'],
            registry=self.registry
        )
        
        self.ai_model_duration = Histogram(
            'moderation_ai_model_duration_seconds',
            'AI模型处理时间',
            ['model_name'],
            registry=self.registry
        )
        
        # 仪表盘
        self.active_requests = Gauge(
            'moderation_active_requests',
            '当前活跃请求数',
            registry=self.registry
        )
        
        self.queue_size = Gauge(
            'moderation_queue_size',
            '队列大小',
            registry=self.registry
        )
        
        # 信息指标
        self.system_info = Info(
            'moderation_system_info',
            '系统信息',
            registry=self.registry
        )
        
        # 设置系统信息
        self.system_info.info({
            'version': '1.0.0',
            'started_at': datetime.now().isoformat()
        })
    
    def record_request(
        self,
        risk_level: RiskLevel,
        processing_time: float,
        status: str = "success",
        categories: Optional[list] = None,
        engines_used: Optional[list] = None
    ):
        """记录请求指标"""
        with self._lock:
            # 记录基本指标
            self.requests_total.labels(
                risk_level=risk_level.value,
                status=status
            ).inc()
            
            # 记录处理时间
            self.request_duration.labels(engine_type="total").observe(processing_time)
            
            # 记录分类检测
            if categories:
                for category in categories:
                    self.categories_detected_total.labels(
                        category=category.value if isinstance(category, ContentCategory) else category
                    ).inc()
            
            # 记录引擎使用情况
            if engines_used:
                for engine in engines_used:
                    self.engine_requests_total.labels(
                        engine_type=engine.value if isinstance(engine, EngineType) else engine,
                        status=status
                    ).inc()
            
            # 内存统计
            current_time = time.time()
            self._request_times.append((current_time, processing_time))
            
            # 按小时统计
            hour_key = datetime.now().strftime("%Y%m%d%H")
            self._hourly_stats[hour_key]['total'] += 1
            self._hourly_stats[hour_key][risk_level.value] += 1
    
    def record_engine_performance(
        self,
        engine_type: EngineType,
        processing_time: float,
        status: str = "success"
    ):
        """记录引擎性能指标"""
        self.request_duration.labels(
            engine_type=engine_type.value
        ).observe(processing_time)
        
        self.engine_requests_total.labels(
            engine_type=engine_type.value,
            status=status
        ).inc()
    
    def record_ai_model_performance(
        self,
        model_name: str,
        processing_time: float
    ):
        """记录AI模型性能"""
        self.ai_model_duration.labels(
            model_name=model_name
        ).observe(processing_time)
    
    def update_active_requests(self, count: int):
        """更新活跃请求数"""
        self.active_requests.set(count)
    
    def update_queue_size(self, size: int):
        """更新队列大小"""
        self.queue_size.set(size)
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        with self._lock:
            now = time.time()
            
            # 计算最近时间窗口的统计
            recent_times = [
                (t, duration) for t, duration in self._request_times
                if now - t <= 3600  # 最近1小时
            ]
            
            if recent_times:
                avg_duration = sum(duration for _, duration in recent_times) / len(recent_times)
                request_rate = len(recent_times) / 3600  # 每秒请求数
            else:
                avg_duration = 0
                request_rate = 0
            
            return {
                "total_requests": len(self._request_times),
                "recent_hour_requests": len(recent_times),
                "average_duration": avg_duration,
                "request_rate_per_second": request_rate,
                "hourly_stats": dict(self._hourly_stats),
                "last_updated": datetime.now().isoformat()
            }
    
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup_old_data():
            while True:
                try:
                    with self._lock:
                        # 清理过期的小时统计（保留24小时）
                        cutoff_time = datetime.now() - timedelta(hours=24)
                        cutoff_key = cutoff_time.strftime("%Y%m%d%H")
                        
                        expired_keys = [
                            key for key in self._hourly_stats.keys()
                            if key < cutoff_key
                        ]
                        
                        for key in expired_keys:
                            del self._hourly_stats[key]
                    
                    # 每小时清理一次
                    time.sleep(3600)
                    
                except Exception as e:
                    print(f"指标清理线程错误: {e}")
                    time.sleep(60)  # 出错后1分钟重试
        
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
            self._cleanup_thread.start()


# 全局指标收集器实例
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# 装饰器：自动记录函数执行时间
def record_timing(engine_type: str = "unknown"):
    """装饰器：记录函数执行时间"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                processing_time = time.time() - start_time
                get_metrics_collector().record_engine_performance(
                    EngineType(engine_type) if engine_type in [e.value for e in EngineType] else EngineType.AI,
                    processing_time,
                    "success"
                )
                return result
            except Exception as e:
                processing_time = time.time() - start_time
                get_metrics_collector().record_engine_performance(
                    EngineType(engine_type) if engine_type in [e.value for e in EngineType] else EngineType.AI,
                    processing_time,
                    "error"
                )
                raise
        return wrapper
    return decorator 