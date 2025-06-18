"""
融合引擎 - 整合AI和规则引擎的检测结果
"""

import time
from typing import Dict, Any, List, Optional
from enum import Enum

from .base_engine import BaseEngine
from models.models import AIResult, RuleResult, FusionResult
from models.enums import RiskLevel, ContentCategory, EngineType
from utils.exceptions import EngineError
from utils.logger import get_logger
from utils.metrics import record_timing


class FusionStrategy(Enum):
    """融合策略"""
    MAX_RISK = "max_risk"  # 取最高风险
    WEIGHTED = "weighted"  # 加权平均
    CONSERVATIVE = "conservative"  # 保守策略


class FusionEngine(BaseEngine):
    """融合引擎 - 整合多个检测引擎的结果"""
    
    def __init__(
        self,
        ai_weight: float = 0.7,
        rule_weight: float = 0.3,
        strategy: FusionStrategy = FusionStrategy.WEIGHTED,
        confidence_threshold: float = 0.6
    ):
        super().__init__()
        self.ai_weight = ai_weight
        self.rule_weight = rule_weight
        self.strategy = strategy
        self.confidence_threshold = confidence_threshold
        self.logger = get_logger(__name__)
        
        # 验证权重
        if abs((ai_weight + rule_weight) - 1.0) > 0.01:
            raise ValueError("AI权重和规则权重之和必须等于1.0")
    
    @record_timing("fusion")
    def process(self, content: str, **kwargs) -> FusionResult:
        """融合处理结果"""
        start_time = time.time()
        
        try:
            # 获取各引擎结果
            ai_result = kwargs.get("ai_result")
            rule_result = kwargs.get("rule_result")
            
            if not ai_result and not rule_result:
                raise EngineError("至少需要一个引擎结果")
            
            # 执行融合
            if self.strategy == FusionStrategy.MAX_RISK:
                result = self._max_risk_fusion(ai_result, rule_result)
            elif self.strategy == FusionStrategy.WEIGHTED:
                result = self._weighted_fusion(ai_result, rule_result)
            elif self.strategy == FusionStrategy.CONSERVATIVE:
                result = self._conservative_fusion(ai_result, rule_result)
            else:
                raise EngineError(f"未知的融合策略: {self.strategy}")
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            self.logger.info(f"融合完成，最终风险等级: {result.risk_level.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"融合处理失败: {e}")
            raise EngineError(f"融合处理失败: {e}")
    
    async def analyze(self, content: str, **kwargs) -> FusionResult:
        """实现BaseEngine的抽象方法，用于符合接口要求"""
        return self.process(content, **kwargs)
    
    def _max_risk_fusion(
        self,
        ai_result: Optional[AIResult],
        rule_result: Optional[RuleResult]
    ) -> FusionResult:
        """最大风险策略"""
        results = [r for r in [ai_result, rule_result] if r is not None]
        
        # 找到最高风险等级
        max_risk_level = max(r.risk_level for r in results)
        
        # 合并所有分类
        all_categories = set()
        for result in results:
            if hasattr(result, 'violated_categories'):
                all_categories.update(result.violated_categories)
        
        # 合并风险原因
        all_reasons = []
        for result in results:
            if hasattr(result, 'risk_reasons'):
                all_reasons.extend(result.risk_reasons)
        
        # 计算综合置信度
        confidence = max(r.confidence_score for r in results)
        
        return FusionResult(
            risk_level=max_risk_level,
            violated_categories=list(all_categories),
            risk_score=self._risk_level_to_score(max_risk_level),
            risk_reasons=all_reasons,
            detailed_analysis=self._merge_analysis(results),
            confidence_score=confidence,
            ai_result=ai_result,
            rule_result=rule_result,
            fusion_strategy=self.strategy.value,
            engines_used=[EngineType.AI, EngineType.RULE] if ai_result and rule_result 
                         else [EngineType.AI] if ai_result else [EngineType.RULE]
        )
    
    def _weighted_fusion(
        self,
        ai_result: Optional[AIResult],
        rule_result: Optional[RuleResult]
    ) -> FusionResult:
        """加权融合策略"""
        if ai_result and rule_result:
            # 两种结果都存在，进行加权
            ai_score = self._risk_level_to_score(ai_result.risk_level)
            rule_score = self._risk_level_to_score(rule_result.risk_level)
            
            # 加权平均
            weighted_score = (ai_score * self.ai_weight + 
                            rule_score * self.rule_weight)
            
            final_risk_level = self._score_to_risk_level(weighted_score)
            
            # 合并分类
            all_categories = set()
            all_categories.update(ai_result.violated_categories)
            all_categories.update(rule_result.violated_categories)
            
            # 合并原因
            all_reasons = []
            all_reasons.extend(ai_result.risk_reasons)
            all_reasons.extend(rule_result.risk_reasons)
            
            # 加权置信度
            confidence = (ai_result.confidence_score * self.ai_weight + 
                         rule_result.confidence_score * self.rule_weight)
            
        elif ai_result:
            # 只有AI结果
            final_risk_level = ai_result.risk_level
            weighted_score = self._risk_level_to_score(final_risk_level)
            all_categories = set(ai_result.violated_categories)
            all_reasons = ai_result.risk_reasons
            confidence = ai_result.confidence_score
            
        else:
            # 只有规则结果
            final_risk_level = rule_result.risk_level
            weighted_score = self._risk_level_to_score(final_risk_level)
            all_categories = set(rule_result.violated_categories)
            all_reasons = rule_result.risk_reasons
            confidence = rule_result.confidence_score
        
        return FusionResult(
            risk_level=final_risk_level,
            violated_categories=list(all_categories),
            risk_score=weighted_score,
            risk_reasons=all_reasons,
            detailed_analysis=self._merge_analysis([r for r in [ai_result, rule_result] if r]),
            confidence_score=confidence,
            ai_result=ai_result,
            rule_result=rule_result,
            fusion_strategy=self.strategy.value,
            engines_used=[EngineType.AI, EngineType.RULE] if ai_result and rule_result 
                         else [EngineType.AI] if ai_result else [EngineType.RULE]
        )
    
    def _conservative_fusion(
        self,
        ai_result: Optional[AIResult],
        rule_result: Optional[RuleResult]
    ) -> FusionResult:
        """保守策略 - 倾向于更严格的判断"""
        results = [r for r in [ai_result, rule_result] if r is not None]
        
        # 如果任一引擎判断为高风险，则采用高风险
        risk_levels = [r.risk_level for r in results]
        
        if RiskLevel.BLOCKED in risk_levels:
            final_risk_level = RiskLevel.BLOCKED
        elif RiskLevel.RISKY in risk_levels:
            final_risk_level = RiskLevel.RISKY
        elif RiskLevel.SUSPICIOUS in risk_levels:
            final_risk_level = RiskLevel.SUSPICIOUS
        else:
            final_risk_level = RiskLevel.SAFE
        
        # 合并所有检测到的分类
        all_categories = set()
        for result in results:
            if hasattr(result, 'violated_categories'):
                all_categories.update(result.violated_categories)
        
        # 合并风险原因
        all_reasons = []
        for result in results:
            if hasattr(result, 'risk_reasons'):
                all_reasons.extend(result.risk_reasons)
        
        # 保守的置信度计算
        confidence = min(r.confidence_score for r in results) if len(results) > 1 else results[0].confidence_score
        
        return FusionResult(
            risk_level=final_risk_level,
            violated_categories=list(all_categories),
            risk_score=self._risk_level_to_score(final_risk_level),
            risk_reasons=all_reasons,
            detailed_analysis=self._merge_analysis(results),
            confidence_score=confidence,
            ai_result=ai_result,
            rule_result=rule_result,
            fusion_strategy=self.strategy.value,
            engines_used=[EngineType.AI, EngineType.RULE] if ai_result and rule_result 
                         else [EngineType.AI] if ai_result else [EngineType.RULE]
        )
    
    def _risk_level_to_score(self, risk_level: RiskLevel) -> float:
        """风险等级转换为分数"""
        mapping = {
            RiskLevel.SAFE: 0.1,
            RiskLevel.SUSPICIOUS: 0.4,
            RiskLevel.RISKY: 0.7,
            RiskLevel.BLOCKED: 0.9
        }
        return mapping.get(risk_level, 0.5)
    
    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """分数转换为风险等级"""
        if score >= 0.8:
            return RiskLevel.BLOCKED
        elif score >= 0.5:
            return RiskLevel.RISKY
        elif score >= 0.2:
            return RiskLevel.SUSPICIOUS
        else:
            return RiskLevel.SAFE
    
    def _merge_analysis(self, results: List) -> str:
        """合并分析结果"""
        analyses = []
        
        for i, result in enumerate(results):
            engine_name = "AI引擎" if isinstance(result, AIResult) else "规则引擎"
            analysis = getattr(result, 'detailed_analysis', '')
            if analysis:
                analyses.append(f"[{engine_name}] {analysis}")
        
        return "\n".join(analyses) if analyses else "无详细分析"
    
    def get_engine_type(self) -> EngineType:
        """获取引擎类型"""
        return EngineType.FUSION
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        try:
            ai_weight = config.get("ai_weight", 0.7)
            rule_weight = config.get("rule_weight", 0.3)
            
            if not isinstance(ai_weight, (int, float)) or not isinstance(rule_weight, (int, float)):
                return False
            
            if abs((ai_weight + rule_weight) - 1.0) > 0.01:
                return False
            
            strategy = config.get("strategy", "weighted")
            if strategy not in [s.value for s in FusionStrategy]:
                return False
            
            return True
            
        except Exception:
            return False


def create_fusion_engine(config: Dict[str, Any]) -> FusionEngine:
    """创建融合引擎工厂函数"""
    fusion_config = config.get("fusion", {})
    
    return FusionEngine(
        ai_weight=fusion_config.get("ai_weight", 0.7),
        rule_weight=fusion_config.get("rule_weight", 0.3),
        strategy=FusionStrategy(fusion_config.get("strategy", "weighted")),
        confidence_threshold=fusion_config.get("confidence_threshold", 0.6)
    ) 