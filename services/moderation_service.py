"""
内容审核服务
"""

import time
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

import json
from peewee import DoesNotExist
from models.database import Contents, db
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
        content_id: int,
        db_session: Optional[Any] = None  # 数据库会话
    ) -> dict:
        """审核单条内容"""
        start_time = time.time()
        self.total_requests += 1
        
        # 1. 根据 content_id 查询内容
        content_obj = Contents.get_or_none(Contents.id == content_id)
        if not content_obj:
            raise ModerationError(f"内容不存在: {content_id}")
        
        try:
            self.logger.info(f"开始审核内容: {content_id}")
            
            # 2. 准备待审核数据
            content_to_moderate = {
                "text": content_obj.content,
                "images": json.loads(content_obj.images) if content_obj.images else [],
                "audios": json.loads(content_obj.audios) if content_obj.audios else [],
                "videos": json.loads(content_obj.videos) if content_obj.videos else [],
            }

            # 3. 并行执行所有类型的审核
            all_results = await self._run_all_moderations(content_to_moderate)

            # 4. 综合判断最终结果
            final_decision, final_score = self._get_final_decision(all_results)

            # 5. 保存审核结果到Contents表
            updated_content = self._save_audit_result(
                content_obj, final_decision, all_results
            )

            # 记录指标
            # self._record_success_metrics(result) # 可根据需要调整

            
            self.logger.info(
                f"内容审核完成: {content_id}, 最终决策: {final_decision.value}"
            )

            return {
                "content_id": content_id,
                "final_decision": final_decision.value,
                "risk_level": final_decision.value,
                "processing_status": ProcessingStatus.COMPLETED.value,
                "details": all_results
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.failed_requests += 1
            
            self.logger.error(f"内容审核失败: {content_id}, 错误: {e}")
            
            # 返回错误结果
            return {"error": f"审核失败: {e}"}
    
    async def _run_all_moderations(self, content_data: dict) -> dict:
        """并行执行文本、图片、音频、视频的审核"""
        tasks = {}
        if content_data.get("text"):
            tasks["text"] = asyncio.create_task(self._run_detection_engines(content_data["text"]))
        # 此处添加图片、音频、视频的审核逻辑
        # for image_url in content_data.get("images", []):
        #     tasks[f"image:{image_url}"] = asyncio.create_task(self.image_moderation_service.moderate(image_url))

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        final_results = {}
        for task_name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                self.logger.error(f"{task_name} 审核失败: {result}")
                final_results[task_name] = self._get_default_error_result(str(result))
            else:
                final_results[task_name] = result
        return final_results

    def _get_final_decision(self, all_results: dict) -> tuple[RiskLevel, float]:
        """根据所有审核结果综合判断"""
        highest_risk = RiskLevel.SAFE
        highest_score = 0.0

        for result_group in all_results.values():
            # 假设每个result_group是(ai_result, rule_result)
            if isinstance(result_group, tuple):
                 ai_res, rule_res = result_group
                 fusion_res = self.fusion_engine.process(
                    content="", ai_result=ai_res, rule_result=rule_res
                )
                 if fusion_res.risk_level.value > highest_risk.value:
                    highest_risk = fusion_res.risk_level
                 if fusion_res.risk_score > highest_score:
                    highest_score = fusion_res.risk_score
            # 可扩展处理其他类型结果

        # 只要有一个不安全，整体就为不安全
        if highest_risk != RiskLevel.SAFE:
            return highest_risk, highest_score

        return RiskLevel.SAFE, 0.0

    def _save_audit_result(self, content_obj: Contents, final_decision: RiskLevel, all_results: dict) -> Contents:
        """保存审核结果到Contents表"""
        from models.enums import AuditStatus
        # Peewee操作是同步的，不需要在异步方法中特别处理
        with db.atomic():
            # 更新内容表的审核状态和处理结果
            if final_decision == RiskLevel.SAFE:
                content_obj.audit_status = AuditStatus.APPROVED.value
            else:
                content_obj.audit_status = AuditStatus.REJECTED.value
            content_obj.risk_level = final_decision.value
            content_obj.processing_status = ProcessingStatus.COMPLETED.value
            content_obj.processing_content = json.dumps(all_results, default=str, ensure_ascii=False)
            content_obj.save()
        return content_obj

    def _get_default_error_result(self, error_msg: str):
        return {
            "risk_level": RiskLevel.SUSPICIOUS.value,
            "risk_score": 0.5,
            "error": error_msg
        }

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
            if self.ai_agent:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self.executor, 
                    self.ai_agent.process, 
                    content
                )
            raise ModerationError("AI agent is not enabled")
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
                processing_time=0.0,
                detailed_analysis="",
                confidence_score=0.5,
                reasoning="Error processing",
                model_name="default_error_model"
            )
        else:  # rule
            return RuleResult(
                risk_level=RiskLevel.SAFE,
                risk_score=0.0,
                risk_reasons=[error_msg],
                violated_categories=[],
                sensitive_matches=[],
                processing_time=0.0,
                confidence_score=0.0
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
            content_id=request.content_id or "",
            original_content=request.content,
            masked_content=request.content, # Placeholder
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
        content_id: Optional[str], 
        content: str, 
        error_msg: str, 
        processing_time: float
    ) -> ModerationResult:
        """构建错误结果"""
        ai_res = self._get_default_result("ai", error_msg)
        rule_res = self._get_default_result("rule", error_msg)
        return ModerationResult(
            content_id=content_id or "unknown",
            original_content=content,
            masked_content=content, # Placeholder
            status=ProcessingStatus.FAILED,
            ai_result=ai_res if isinstance(ai_res, AIResult) else None,
            rule_result=rule_res if isinstance(rule_res, RuleResult) else None,
            fusion_result=FusionResult(
                risk_level=RiskLevel.RISKY, 
                risk_score=0.7, 
                violated_categories=[], 
                risk_reasons=["Error"], 
                confidence_score=0.0
            ),
            final_decision=RiskLevel.RISKY,  # 出错时采用保守策略
            final_score=0.7,
            processing_time=processing_time,
            engines_used=[],
            total_matches=0,
            categories_detected=[],
            detailed_analysis="Error occurred during processing"
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
                self.moderate(int(content_id), **kwargs)
                for content_id in content_ids
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
            for content_id in content_ids:
                try:
                    result = await self.moderate(int(content_id), **kwargs)
                    results.append(result)
                except Exception as e:
                    errors.append({
                        "content_id": content_id,
                        "error": str(e),
                        "content": contents[i][:100] + "..." if len(contents[i]) > 100 else contents[i]
                    })
                    results.append(self._build_error_result(content_id, "", str(e), 0.0))
        
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
        self.fusion_engine.ai_weight = ai_weight
        self.fusion_engine.rule_weight = rule_weight
        self.logger.info(f"融合引擎权重已更新: AI={ai_weight}, 规则={rule_weight}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        self.executor.shutdown(wait=True)