"""
内容审核服务
"""

import time
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.models import (
    ModerationRequest, 
    ModerationResult, 
    BatchModerationRequest,
    BatchModerationResult,
    AIResult,
    RuleResult,
    FusionResult
)
from models.enums import RiskLevel, EngineType, ProcessingStatus
from utils.exceptions import ModerationError, TimeoutError as ModerationTimeoutError
from services.agents import create_moderation_agent
from engines import RuleEngine, FusionEngine
from utils.metrics import get_metrics_collector
from utils.logger import get_logger


class ModerationService:
    """内容审核服务"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger("moderation_service")
        self.metrics = get_metrics_collector()
        
        # 初始化各个引擎
        self._init_engines()
        
        # 线程池用于并行处理
        max_workers = config.get("performance", {}).get("max_concurrent_requests", 50)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 统计信息
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
    
    def _init_engines(self):
        """初始化检测引擎"""
        try:
            engines_config = self.config.get("engines", {})
            enabled_engines = engines_config.get("enabled", [])
            
            # 初始化AI代理
            if "ai" in enabled_engines:
                self.ai_agent = create_moderation_agent(self.config)
                self.logger.info("AI代理初始化成功")
            else:
                self.ai_agent = None
                self.logger.info("AI代理未启用")
            
            # 初始化规则引擎
            if "rule" in enabled_engines:
                self.rule_engine = RuleEngine()
                self.logger.info("规则引擎初始化成功")
            else:
                self.rule_engine = None
                self.logger.info("规则引擎未启用")
            
            # 初始化融合引擎
            fusion_config = engines_config.get("fusion", {})
            self.fusion_engine = FusionEngine(
                ai_weight=fusion_config.get("ai_weight", 0.7),
                rule_weight=fusion_config.get("rule_weight", 0.3)
            )
            self.logger.info("融合引擎初始化成功")
            
        except Exception as e:
            self.logger.error(f"引擎初始化失败: {e}")
            raise ModerationError(f"引擎初始化失败: {e}")
    
    async def moderate(
        self, 
        content: str, 
        content_id: Optional[str] = None,
        **kwargs
    ) -> ModerationResult:
        """审核单条内容"""
        start_time = time.time()
        self.total_requests += 1
        
        # 生成内容ID
        if content_id is None:
            content_id = str(uuid.uuid4())
        
        try:
            self.logger.info(f"开始审核内容: {content_id}")
            
            # 创建审核请求
            request = ModerationRequest(
                content=content,
                content_id=content_id,
                **kwargs
            )
            
            # 并行执行AI和规则检测
            ai_result, rule_result = await self._run_detection_engines(content)
            
            # 融合结果
            fusion_result = await self.fusion_engine.analyze(
                content, ai_result=ai_result, rule_result=rule_result
            )
            
            # 构建最终结果
            processing_time = time.time() - start_time
            result = self._build_moderation_result(
                request, ai_result, rule_result, fusion_result, processing_time
            )
            
            # 记录指标
            self._record_success_metrics(result)
            
            self.logger.info(
                f"内容审核完成: {content_id}, 风险等级: {result.final_decision.value}, "
                f"处理时间: {processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.failed_requests += 1
            
            self.logger.error(f"内容审核失败: {content_id}, 错误: {e}")
            
            # 返回保守的错误结果
            return self._build_error_result(content_id, content, str(e), processing_time)
    
    async def _run_detection_engines(self, content: str) -> tuple[AIResult, RuleResult]:
        """并行运行检测引擎"""
        tasks = []
        
        # AI检测任务
        if self.ai_agent:
            ai_task = asyncio.create_task(self._run_ai_detection(content))
            tasks.append(("ai", ai_task))
        
        # 规则检测任务
        if self.rule_engine:
            rule_task = asyncio.create_task(self.rule_engine.analyze(content))
            tasks.append(("rule", rule_task))
        
        # 等待所有任务完成
        results = {}
        for engine_type, task in tasks:
            try:
                results[engine_type] = await task
            except Exception as e:
                self.logger.error(f"{engine_type}引擎检测失败: {e}")
                results[engine_type] = self._get_default_result(engine_type, str(e))
        
        # 获取结果
        ai_result = results.get("ai", self._get_default_result("ai", "AI引擎未启用"))
        rule_result = results.get("rule", self._get_default_result("rule", "规则引擎未启用"))
        
        return ai_result, rule_result
    
    async def _run_ai_detection(self, content: str) -> AIResult:
        """运行AI检测"""
        try:
            # AI代理的process方法可能是同步的，需要在线程池中运行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, 
                self.ai_agent.process, 
                content
            )
        except Exception as e:
            self.logger.error(f"AI检测失败: {e}")
            raise
    
    def _get_default_result(self, engine_type: str, error_msg: str) -> Union[AIResult, RuleResult]:
        """获取默认的错误结果"""
        if engine_type == "ai":
            return AIResult(
                risk_level=RiskLevel.SUSPICIOUS,
                risk_score=0.5,
                risk_reasons=[error_msg],
                violated_categories=[],
                processing_time=0.0
            )
        else:  # rule
            return RuleResult(
                risk_level=RiskLevel.SAFE,
                risk_score=0.0,
                risk_reasons=[error_msg],
                violated_categories=[],
                sensitive_matches=[],
                processing_time=0.0
            )
    
    def _build_moderation_result(
        self,
        request: ModerationRequest,
        ai_result: AIResult,
        rule_result: RuleResult,
        fusion_result: FusionResult,
        processing_time: float
    ) -> ModerationResult:
        """构建审核结果"""
        
        # 计算总匹配数
        total_matches = len(rule_result.sensitive_matches)
        
        # 收集所有检测到的分类
        all_categories = list(set(
            fusion_result.violated_categories + 
            ai_result.violated_categories + 
            rule_result.violated_categories
        ))
        
        # 确定使用的引擎
        engines_used = []
        if self.ai_agent:
            engines_used.append(EngineType.AI)
        if self.rule_engine:
            engines_used.append(EngineType.RULE)
        
        return ModerationResult(
            content_id=request.content_id,
            original_content=request.content,
            status=ProcessingStatus.COMPLETED,
            ai_result=ai_result,
            rule_result=rule_result,
            fusion_result=fusion_result,
            final_decision=fusion_result.risk_level,
            final_score=fusion_result.risk_score,
            processing_time=processing_time,
            engines_used=engines_used,
            total_matches=total_matches,
            categories_detected=all_categories
        )
    
    def _build_error_result(
        self, 
        content_id: str, 
        content: str, 
        error_msg: str, 
        processing_time: float
    ) -> ModerationResult:
        """构建错误结果"""
        return ModerationResult(
            content_id=content_id,
            original_content=content,
            status=ProcessingStatus.FAILED,
            final_decision=RiskLevel.RISKY,  # 出错时采用保守策略
            final_score=0.7,
            processing_time=processing_time,
            engines_used=[],
            total_matches=0,
            categories_detected=[]
        )
    
    def _record_success_metrics(self, result: ModerationResult):
        """记录成功指标"""
        self.successful_requests += 1
        
        self.metrics.record_request(
            risk_level=result.final_decision,
            processing_time=result.processing_time,
            status="success",
            categories=result.categories_detected,
            engines_used=result.engines_used
        )
    
    async def moderate_batch(
        self, 
        contents: List[str], 
        content_ids: Optional[List[str]] = None,
        parallel: bool = True,
        **kwargs
    ) -> BatchModerationResult:
        """批量审核内容"""
        start_time = time.time()
        
        if content_ids is None:
            content_ids = [str(uuid.uuid4()) for _ in contents]
        
        self.logger.info(f"开始批量审核: {len(contents)} 条内容")
        
        results = []
        errors = []
        
        if parallel:
            # 并行处理
            tasks = [
                self.moderate(content, content_id, **kwargs)
                for content, content_id in zip(contents, content_ids)
            ]
            
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(completed_results):
                if isinstance(result, Exception):
                    errors.append({
                        "content_id": content_ids[i],
                        "error": str(result),
                        "content": contents[i][:100] + "..." if len(contents[i]) > 100 else contents[i]
                    })
                    # 添加错误结果
                    results.append(self._build_error_result(
                        content_ids[i], contents[i], str(result), 0.0
                    ))
                else:
                    results.append(result)
        else:
            # 顺序处理
            for content, content_id in zip(contents, content_ids):
                try:
                    result = await self.moderate(content, content_id, **kwargs)
                    results.append(result)
                except Exception as e:
                    errors.append({
                        "content_id": content_id,
                        "error": str(e),
                        "content": content[:100] + "..." if len(content) > 100 else content
                    })
                    results.append(self._build_error_result(content_id, content, str(e), 0.0))
        
        processing_time = time.time() - start_time
        success_count = len([r for r in results if r.status == ProcessingStatus.COMPLETED])
        failed_count = len(results) - success_count
        
        self.logger.info(
            f"批量审核完成: 总数={len(contents)}, 成功={success_count}, "
            f"失败={failed_count}, 处理时间={processing_time:.2f}s"
        )
        
        return BatchModerationResult(
            total_count=len(contents),
            success_count=success_count,
            failed_count=failed_count,
            results=results,
            errors=errors,
            processing_time=processing_time
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "status": "healthy",
            "engines": {},
            "statistics": self.get_statistics()
        }
        
        # 检查各个引擎
        if self.ai_agent:
            try:
                ai_health = self.ai_agent.health_check()
                health_status["engines"]["ai"] = ai_health
            except Exception as e:
                health_status["engines"]["ai"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"
        
        if self.rule_engine:
            try:
                rule_health = await self.rule_engine.health_check()
                health_status["engines"]["rule"] = rule_health
            except Exception as e:
                health_status["engines"]["rule"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"
        
        return health_status
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        success_rate = (self.successful_requests / self.total_requests 
                       if self.total_requests > 0 else 0.0)
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "engines_available": {
                "ai": self.ai_agent is not None,
                "rule": self.rule_engine is not None,
                "fusion": True
            }
        }
    
    def reload_rules(self):
        """重新加载规则配置"""
        if self.rule_engine:
            self.rule_engine.reload_rules()
            self.logger.info("规则配置已重新加载")
    
    def update_fusion_weights(self, ai_weight: float, rule_weight: float):
        """更新融合引擎权重"""
        self.fusion_engine.update_weights(ai_weight, rule_weight)
        self.logger.info(f"融合引擎权重已更新: AI={ai_weight}, 规则={rule_weight}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        self.executor.shutdown(wait=True) 