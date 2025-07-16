"""文字审核服务 - 基于AI分析和规则匹配"""

import time
import re
import json
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from models.database import ViolationWord, db
from models.models import AIResult, RuleResult
from models.enums import RiskLevel, ContentCategory
from utils.logger import get_logger
from utils.exceptions import ModerationError


class TextModerationService:
    """文字审核服务"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger("text_moderation_service")
        
        # AI模型配置
        self.ai_config = config.get("ai", {})
        self.models_config = self.ai_config.get("models", {})
        self.default_model = self.ai_config.get("default_model", "ollama_qwen")
        self.model_config = self.models_config.get(self.default_model, {})
        
        # 缓存违规词库
        self._violation_words_cache = None
        self._cache_update_time = None
        self._cache_ttl = 300  # 缓存5分钟
        
        self.logger.info("文字审核服务初始化完成")
    
    def moderate_text(self, content: str) -> Tuple[AIResult, RuleResult]:
        """文字审核主方法"""
        start_time = time.time()
        
        try:
            self.logger.info(f"开始文字审核，内容长度: {len(content)}")
            
            # 1. 规则匹配检测
            rule_result = self._rule_based_check(content)
            
            # 2. AI分析检测
            ai_result = self._ai_based_check(content)
            
            processing_time = time.time() - start_time
            rule_result.processing_time = processing_time
            ai_result.processing_time = processing_time
            
            self.logger.info(
                f"文字审核完成: AI风险等级={ai_result.risk_level.value}, "
                f"规则风险等级={rule_result.risk_level.value}, "
                f"处理时间={processing_time:.2f}s"
            )
            
            return ai_result, rule_result
            
        except Exception as e:
            self.logger.error(f"文字审核失败: {e}")
            processing_time = time.time() - start_time
            
            # 返回默认错误结果
            error_ai_result = AIResult(
                risk_level=RiskLevel.SUSPICIOUS,
                risk_score=0.5,
                risk_reasons=[f"AI检测失败: {str(e)}"],
                violated_categories=[],
                processing_time=processing_time,
                detailed_analysis="AI检测过程中发生错误",
                confidence_score=0.1,
                reasoning=f"错误: {str(e)}",
                model_name=self.model_config.get("model_name", "unknown")
            )
            
            error_rule_result = RuleResult(
                risk_level=RiskLevel.SAFE,
                risk_score=0.0,
                risk_reasons=[f"规则检测失败: {str(e)}"],
                violated_categories=[],
                sensitive_matches=[],
                processing_time=processing_time,
                confidence_score=0.0
            )
            
            return error_ai_result, error_rule_result
    
    def _rule_based_check(self, content: str) -> RuleResult:
        """基于规则的检测"""
        start_time = time.time()
        
        try:
            # 获取违规词库
            violation_words = self._get_violation_words()
            
            sensitive_matches = []
            total_score = 0
            max_score = 0
            violated_categories = []
            
            # 遍历违规词库进行匹配
            for word_data in violation_words:
                wrong_input = word_data['wrong_input']
                correct_input = word_data['correct_input']
                score = word_data['violation_score']
                
                # 检查是否包含违规词
                if self._contains_violation_word(content, wrong_input):
                    sensitive_matches.append({
                        'matched_text': wrong_input,
                        'correct_text': correct_input,
                        'score': score,
                        'positions': self._find_word_positions(content, wrong_input)
                    })
                    total_score += score
                    max_score = max(max_score, score)
            
            # 根据分数确定风险等级
            if max_score >= 80:
                risk_level = RiskLevel.BLOCKED
                risk_score = min(max_score / 100.0, 1.0)
            elif max_score >= 60:
                risk_level = RiskLevel.RISKY
                risk_score = min(max_score / 100.0, 1.0)
            elif max_score >= 30:
                risk_level = RiskLevel.SUSPICIOUS
                risk_score = min(max_score / 100.0, 1.0)
            else:
                risk_level = RiskLevel.SAFE
                risk_score = 0.0
            
            # 生成风险原因
            risk_reasons = []
            if sensitive_matches:
                risk_reasons.append(f"检测到{len(sensitive_matches)}个违规词")
                for match in sensitive_matches[:3]:  # 只显示前3个
                    risk_reasons.append(
                        f"违规词: '{match['matched_text']}' -> '{match['correct_text']}' (分数: {match['score']})"
                    )
            
            processing_time = time.time() - start_time
            
            return RuleResult(
                risk_level=risk_level,
                risk_score=risk_score,
                risk_reasons=risk_reasons,
                violated_categories=violated_categories,
                sensitive_matches=sensitive_matches,
                processing_time=processing_time,
                confidence_score=1.0 if sensitive_matches else 0.0
            )
            
        except Exception as e:
            self.logger.error(f"规则检测失败: {e}")
            processing_time = time.time() - start_time
            
            return RuleResult(
                risk_level=RiskLevel.SAFE,
                risk_score=0.0,
                risk_reasons=[f"规则检测失败: {str(e)}"],
                violated_categories=[],
                sensitive_matches=[],
                processing_time=processing_time,
                confidence_score=0.0
            )
    
    def _ai_based_check(self, content: str) -> AIResult:
        """基于AI的检测"""
        start_time = time.time()
        
        try:
            # 构建AI检测提示词
            system_prompt = self._create_ai_prompt()
            
            # 调用AI模型
            response_text = self._call_ai_model(system_prompt, content)
            
            # 解析AI响应
            ai_result = self._parse_ai_response(response_text)
            
            processing_time = time.time() - start_time
            ai_result.processing_time = processing_time
            ai_result.model_name = self.model_config.get("model_name", "unknown")
            
            return ai_result
            
        except Exception as e:
            self.logger.error(f"AI检测失败: {e}")
            processing_time = time.time() - start_time
            
            return AIResult(
                risk_level=RiskLevel.SUSPICIOUS,
                risk_score=0.5,
                risk_reasons=[f"AI检测失败: {str(e)}"],
                violated_categories=[],
                processing_time=processing_time,
                detailed_analysis="AI检测过程中发生错误",
                confidence_score=0.1,
                reasoning=f"错误: {str(e)}",
                model_name=self.model_config.get("model_name", "unknown")
            )
    
    def _get_violation_words(self) -> List[Dict[str, Any]]:
        """获取违规词库（带缓存）"""
        current_time = time.time()
        
        # 检查缓存是否有效
        if (self._violation_words_cache is not None and 
            self._cache_update_time is not None and 
            current_time - self._cache_update_time < self._cache_ttl):
            return self._violation_words_cache
        
        try:
            # 从数据库获取违规词库
            words = ViolationWord.select().where(ViolationWord.is_active == True)
            
            violation_words = []
            for word in words:
                violation_words.append({
                    'id': word.id,
                    'wrong_input': word.wrong_input,
                    'correct_input': word.correct_input,
                    'violation_score': word.violation_score
                })
            
            # 更新缓存
            self._violation_words_cache = violation_words
            self._cache_update_time = current_time
            
            self.logger.info(f"加载违规词库: {len(violation_words)}个词")
            return violation_words
            
        except Exception as e:
            self.logger.error(f"获取违规词库失败: {e}")
            return []
    
    def _contains_violation_word(self, content: str, wrong_input: str) -> bool:
        """检查内容是否包含违规词"""
        # 简单的包含检查
        return wrong_input.lower() in content.lower()
    
    def _find_word_positions(self, content: str, word: str) -> List[int]:
        """查找违规词在内容中的位置"""
        positions = []
        start = 0
        while True:
            pos = content.lower().find(word.lower(), start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        return positions
    
    def _create_ai_prompt(self) -> str:
        """创建AI检测提示词"""
        return """你是一个专业的中文内容审核专家，请分析以下文本内容是否存在违规问题。

请从以下维度分析：
1. 政治敏感内容
2. 暴力内容
3. 色情内容
4. 违法内容
5. 仇恨言论
6. 虚假信息
7. 垃圾信息
8. 骚扰内容

请严格按照以下JSON格式输出分析结果：

```json
{
    "risk_level": "风险等级 (safe/suspicious/risky/blocked)",
    "confidence_score": 置信度分数(0.0-1.0),
    "categories": ["检测到的分类列表"],
    "suspicious_segments": ["可疑片段列表"],
    "keywords_found": ["发现的关键词列表"],
    "reasoning": "详细的分析推理过程",
    "recommendations": ["处理建议列表"]
}
```

现在请分析以下内容："""
    
    def _call_ai_model(self, system_prompt: str, content: str) -> str:
        """调用AI模型"""
        api_base = self.model_config.get("api_base", "http://175.27.143.201:11434")
        model_name = self.model_config.get("model_name", "qwen2.5:7b")
        timeout = self.ai_config.get("timeout", 30.0)
        
        # 构建请求
        prompt = f"{system_prompt}\n\n内容：{content}"
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.model_config.get("temperature", 0.1),
                "num_predict": self.model_config.get("max_tokens", 2000),
            }
        }
        
        try:
            response = requests.post(
                f"{api_base}/api/generate",
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            result_data = response.json()
            response_text = result_data.get("response", "")
            
            return response_text
            
        except requests.exceptions.Timeout:
            raise ModerationError(f"AI模型请求超时 ({timeout}s)")
        except requests.exceptions.RequestException as e:
            raise ModerationError(f"AI模型请求失败: {e}")
        except Exception as e:
            raise ModerationError(f"AI模型调用失败: {e}")
    
    def _parse_ai_response(self, response_text: str) -> AIResult:
        """解析AI响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response_text.strip()
            
            data = json.loads(json_str)
            
            # 映射风险等级
            risk_level_map = {
                "safe": RiskLevel.SAFE,
                "suspicious": RiskLevel.SUSPICIOUS,
                "risky": RiskLevel.RISKY,
                "blocked": RiskLevel.BLOCKED
            }
            
            risk_level = risk_level_map.get(data.get("risk_level", "safe"), RiskLevel.SAFE)
            
            # 映射分类
            category_map = {
                "political": ContentCategory.POLITICAL,
                "violence": ContentCategory.VIOLENCE,
                "adult": ContentCategory.ADULT,
                "illegal": ContentCategory.ILLEGAL,
                "fraud": ContentCategory.FRAUD,
                "privacy": ContentCategory.PRIVACY,
                "hate_speech": ContentCategory.HATE_SPEECH,
                "harassment": ContentCategory.HARASSMENT,
                "spam": ContentCategory.SPAM,
                "misinformation": ContentCategory.MISINFORMATION
            }
            
            categories = [
                category_map.get(cat, ContentCategory.OTHER)
                for cat in data.get("categories", [])
                if cat in category_map
            ]
            
            # 计算风险分数
            confidence = data.get("confidence_score", 0.5)
            risk_score = self._calculate_risk_score(risk_level, confidence)
            
            return AIResult(
                risk_level=risk_level,
                violated_categories=categories,
                risk_score=risk_score,
                risk_reasons=data.get("recommendations", []),
                detailed_analysis=data.get("reasoning", ""),
                confidence_score=confidence,
                suspicious_segments=data.get("suspicious_segments", []),
                keywords_found=data.get("keywords_found", []),
                evasion_techniques=[],
                reasoning=data.get("reasoning", ""),
                recommendations=data.get("recommendations", [])
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"AI响应解析失败，使用后备解析: {e}")
            return self._fallback_parse_ai_response(response_text)
    
    def _fallback_parse_ai_response(self, response_text: str) -> AIResult:
        """AI响应后备解析方法"""
        text_lower = response_text.lower()
        
        # 简单的关键词检测
        if any(keyword in text_lower for keyword in ["blocked", "严重", "违规"]):
            risk_level = RiskLevel.BLOCKED
            risk_score = 0.8
        elif any(keyword in text_lower for keyword in ["risky", "风险", "危险"]):
            risk_level = RiskLevel.RISKY
            risk_score = 0.6
        elif any(keyword in text_lower for keyword in ["suspicious", "可疑", "注意"]):
            risk_level = RiskLevel.SUSPICIOUS
            risk_score = 0.4
        else:
            risk_level = RiskLevel.SAFE
            risk_score = 0.1
        
        return AIResult(
            risk_level=risk_level,
            violated_categories=[],
            risk_score=risk_score,
            risk_reasons=["AI响应解析失败，使用简单分析"],
            detailed_analysis=response_text[:200] + "...",
            confidence_score=0.3,
            suspicious_segments=[],
            keywords_found=[],
            evasion_techniques=[],
            reasoning="后备解析方法",
            recommendations=["建议人工复核"]
        )
    
    def _calculate_risk_score(self, risk_level: RiskLevel, confidence: float) -> float:
        """根据风险等级和置信度计算风险分数"""
        base_scores = {
            RiskLevel.SAFE: 0.1,
            RiskLevel.SUSPICIOUS: 0.4,
            RiskLevel.RISKY: 0.7,
            RiskLevel.BLOCKED: 0.9
        }
        base_score = base_scores.get(risk_level, 0.5)
        # 置信度影响最终分数
        return min(base_score * confidence + 0.1, 1.0)
    
    def refresh_violation_words_cache(self):
        """刷新违规词库缓存"""
        self._violation_words_cache = None
        self._cache_update_time = None
        self.logger.info("违规词库缓存已刷新")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查AI模型
            api_base = self.model_config.get("api_base", "http://175.27.143.201:11434")
            response = requests.get(f"{api_base}/api/tags", timeout=5)
            ai_status = "healthy" if response.status_code == 200 else "unhealthy"
            
            # 检查违规词库
            violation_words = self._get_violation_words()
            rule_status = "healthy" if violation_words else "no_words"
            
            return {
                "status": "healthy" if ai_status == "healthy" and rule_status == "healthy" else "degraded",
                "ai_model": {
                    "status": ai_status,
                    "api_base": api_base,
                    "model_name": self.model_config.get("model_name", "unknown")
                },
                "rule_engine": {
                    "status": rule_status,
                    "violation_words_count": len(violation_words)
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }