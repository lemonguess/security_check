"""
内容审核AI代理实现
"""

import time
import json
import re
from typing import Dict, Any, List, Optional
import requests

import agentscope
from agentscope.agents import UserAgent
from agentscope.message import Msg
from agentscope.models import OllamaChatWrapper

from .base_agent import BaseAgent
from models.models import AIResult
from models.enums import RiskLevel, ContentCategory
from utils.exceptions import ModelError, TimeoutError
from utils.logger import get_logger
from utils.metrics import record_timing


class ModerationAgent(BaseAgent):
    """内容审核AI代理"""
    
    def __init__(
        self,
        name: str = "moderation_agent",
        model_config: Dict[str, Any] = None,
        timeout: float = 30.0,
        max_retries: int = 2
    ):
        super().__init__(name, model_config, timeout, max_retries)
        
        # 优化后的提示词模板
        self.system_prompt = self._create_system_prompt()
        
        # 初始化AgentScope模型
        self.model = None
        self.agent = None
        self._init_model()
    
    def _create_system_prompt(self) -> str:
        """创建优化后的系统提示词"""
        return """# 角色定义
你是一位专业的中文内容审核专家，专注于识别和分析可能违反中国法律法规或社区准则的内容。特别擅长识别各种变形表达、隐晦表述和规避检测的手法。

# 核心技能
- 深度语义理解与上下文分析
- 敏感内容识别与风险评估
- 变形词汇和隐晦表达识别
- 规避检测手法识别
- 结构化输出与证据提取
- 中国法律法规和网络安全知识

# 审核维度
请从以下维度分析内容：
1. **政治敏感** - 涉及政治立场、政府政策批评、反动言论等
2. **暴力内容** - 描述暴力行为、威胁他人等
3. **违法内容** - 涉及毒品、走私、诈骗等违法活动
4. **成人内容** - 色情、性暗示等不当内容
5. **仇恨言论** - 针对特定群体的歧视、仇恨言论
6. **虚假信息** - 明显的谣言、虚假宣传
7. **垃圾信息** - 广告推广、营销内容
8. **骚扰内容** - 人身攻击、恶意骚扰
9. **诈骗信息** - 金融诈骗、套路贷等
10. **隐私泄露** - 包含个人隐私信息

# 特别关注的变形表达手法
1. **缩写替代**: 如 "xjp", "cxjp", "x j p", "c xjp" 等表示领导人
2. **空格分离**: 如 "打 倒 x j p", "共 产 党" 等用空格分离敏感词
3. **特殊字符**: 使用符号、标点等替换敏感字符
4. **拼音替代**: 使用拼音或拼音缩写替代中文，如"xi"代表"习"
5. **同音字替换**: 使用同音或近音字替代敏感词，如"习近平猪"、"包子"等
6. **表情符号**: 使用表情符号替代或影射，如"习近平🐷"、"🐻"等
7. **谐音影射**: 通过谐音或音似的词汇暗示敏感内容
8. **动物代称**: 用动物名称代指特定人物，常见的包括"猪"、"熊"、"包子"等
9. **上下文隐晦**: 通过上下文暗示而非直接表述
10. **反话表达**: 通过反话或讽刺表达敏感观点
11. **英文混合**: 中英文混合表达敏感内容
12. **错别字**: 故意使用错别字来规避检测
13. **文字拆分**: 将敏感词拆分并插入其他字符，如"打将倒"实际是"打倒"
14. **拼音混合**: 中文、拼音、英文混合表达，如"xi续da推da"隐含"习"和"打倒"
15. **语序调整**: 调整词序来隐藏敏感表达，如"倒打"、"将倒"等
16. **冗余字符**: 在敏感词中插入无意义字符来干扰识别

# 风险等级定义
- **safe** (0.0-0.2): 内容完全安全，无任何敏感问题
- **suspicious** (0.2-0.5): 内容存在可疑之处，需要关注
- **risky** (0.5-0.8): 内容存在明显风险，建议人工审核
- **blocked** (0.8-1.0): 内容严重违规，应当阻止发布

# 输出要求
请严格按照以下JSON格式输出分析结果，不要包含任何其他文本：

```json
{
    "risk_level": "风险等级 (safe/suspicious/risky/blocked)",
    "confidence_score": 置信度分数(0.0-1.0),
    "categories": ["检测到的分类列表"],
    "suspicious_segments": ["可疑片段列表"],
    "keywords_found": ["发现的关键词列表"],
    "evasion_techniques": ["识别到的规避技术列表"],
    "reasoning": "详细的分析推理过程，包括对变形表达的解释",
    "recommendations": ["处理建议列表"]
}
```

# 分析原则
1. **深度语义分析**: 不仅看表面词汇，更要理解深层含义和真实意图
2. **变形识别**: 特别关注各种变形、缩写、分离等规避手法
3. **上下文理解**: 结合全文上下文判断敏感内容的真实性质
4. **风险评估**: 综合考虑内容的危害程度和传播风险
5. **证据充分**: 提供具体的文本证据和详细的分析推理
6. **谨慎处理**: 对于模糊情况倾向于谨慎，避免误判
7. **技术识别**: 识别并记录使用的规避检测技术

# 特别提醒
- 即使是看似正面的新闻报道，也要仔细检查是否夹杂了变形的敏感表达
- 注意识别在正常内容中穿插的敏感词汇或表达
- 对字母、数字、符号的组合要特别敏感
- 空格分离的词汇要重新组合后再判断
- **重点关注同音字和表情符号**: "习近平猪"、"习近平🐷"、"包子"、"🐻"等都是常见的影射表达
- **检查人名与动物的组合**: 特别是领导人姓名后跟动物名称或表情的情况
- **分析表情符号的隐含含义**: 🐷、🐻、🐼 等表情在特定上下文中可能有政治隐喻
- **识别故意的错别字**: 如"猪"替代正常字符，或其他故意的拼写错误
- **深度分析文字拆分**: 如"打将倒"可能是"打倒"的变形，"继xi续"中的"xi"可能指"习"
- **检查拼音混合表达**: "xi"、"da"等拼音可能隐含敏感词汇，特别是与敏感动词组合时
- **分析语序异常**: 正常语法不通顺的地方可能隐藏敏感表达
- **识别冗余字符干扰**: 在词汇中插入"将"、"继"等字符可能是为了规避检测
- **重构隐藏句子**: 尝试从文本中重构可能的敏感表达，如从"打将倒继xi续da推da"中识别"打倒习"

现在请分析以下内容："""

    def _init_model(self):
        """初始化AgentScope模型"""
        try:
            if self.model_config.get("type") == "ollama_chat":
                # 使用Ollama模型
                self._init_ollama_model()
            else:
                # 使用其他模型
                self._init_agentscope_model()
                
        except Exception as e:
            self.logger.error(f"模型初始化失败: {e}")
            # 不抛出异常，而是设置为None，这样会降级使用直接API调用
            self.agent = None
            self.model = None
    
    def _init_ollama_model(self):
        """初始化Ollama模型"""
        try:
            # 初始化AgentScope
            agentscope.init()
            
            # 创建Ollama模型包装器
            model_name = self.model_config.get("model_name", "qwen2.5:7b")
            host = self.model_config.get("api_base", "http://175.27.143.201:11434")
            
            self.model = OllamaChatWrapper(
                config_name="ollama_model",
                model_name=model_name,
                host=host,
                stream=False,
                options={
                    "temperature": self.model_config.get("temperature", 0.1),
                    "num_predict": self.model_config.get("max_tokens", 2000),
                },
                keep_alive="5m"
            )
            
            # 创建代理
            self.agent = UserAgent(
                name=self.name,
                model=self.model,
                sys_prompt=self.system_prompt
            )
            
            self.logger.info(f"Ollama模型初始化成功: {model_name}")
            
        except Exception as e:
            self.logger.error(f"Ollama模型初始化失败: {e}")
            raise ModelError(f"Ollama连接失败: {e}")
    
    def _init_agentscope_model(self):
        """初始化AgentScope标准模型"""
        try:
            # 初始化AgentScope
            agentscope.init()
            
            # 这里可以扩展支持其他模型
            self.logger.warning("标准AgentScope模型未实现，请使用Ollama模型")
            
        except Exception as e:
            self.logger.error(f"AgentScope模型初始化失败: {e}")
            raise ModelError(f"AgentScope模型初始化失败: {e}")
    
    @record_timing("ai")
    def process(self, content: str, **kwargs) -> AIResult:
        """处理内容审核"""
        start_time = time.time()
        
        try:
            self._validate_input(content)
            
            if self.agent:
                result = self._process_with_agentscope(content)
            else:
                result = self._process_with_ollama(content)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            result.model_name = self.model_config.get("model_name", "unknown")
            
            self._record_metrics(processing_time, "success")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"内容处理失败: {e}")
            self._record_metrics(processing_time, "error")
            return self._create_default_result(content, f"处理失败: {str(e)}")
    
    def _process_with_ollama(self, content: str) -> AIResult:
        """使用Ollama处理内容"""
        api_base = self.model_config.get("api_base", "http://175.27.143.201:11434")
        model_name = self.model_config.get("model_name", "qwen2.5:7b")
        
        # 构建请求
        prompt = f"{self.system_prompt}\n\n内容：{content}"
        
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
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result_data = response.json()
            response_text = result_data.get("response", "")
            
            return self._parse_ai_response(response_text)
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Ollama请求超时 ({self.timeout}s)")
        except requests.exceptions.RequestException as e:
            raise ModelError(f"Ollama请求失败: {e}")
        except Exception as e:
            raise ModelError(f"Ollama处理失败: {e}")
    
    def _process_with_agentscope(self, content: str) -> AIResult:
        """使用AgentScope处理内容"""
        try:
            # 创建消息
            msg = Msg(name="user", content=content, role="user")
            
            # 获取回复
            response = self.agent(msg)
            response_text = response.content
            
            return self._parse_ai_response(response_text)
            
        except Exception as e:
            self.logger.error(f"AgentScope处理失败: {e}")
            raise ModelError(f"AgentScope处理失败: {e}")
    
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
                evasion_techniques=data.get("evasion_techniques", []),
                reasoning=data.get("reasoning", ""),
                recommendations=data.get("recommendations", [])
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"AI响应解析失败，使用后备解析: {e}")
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, response_text: str) -> AIResult:
        """后备解析方法"""
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
    
    def _create_default_result(self, content: str, error_msg: str) -> AIResult:
        """创建默认错误结果"""
        return AIResult(
            risk_level=RiskLevel.SUSPICIOUS,
            violated_categories=[],
            risk_score=0.5,
            risk_reasons=[error_msg],
            detailed_analysis=f"处理失败: {error_msg}",
            confidence_score=0.1,
            suspicious_segments=[],
            keywords_found=[],
            evasion_techniques=[],
            reasoning=error_msg,
            recommendations=["建议重试或人工审核"]
        )
    
    def _validate_input(self, content: str):
        """验证输入内容"""
        if not content or not content.strip():
            raise ValueError("内容不能为空")
        if len(content) > 10000:
            raise ValueError("内容长度不能超过10000字符")
    
    def _record_metrics(self, processing_time: float, status: str):
        """记录指标"""
        # 这里可以添加指标记录逻辑
        pass
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if self.model_config.get("type") == "ollama_chat":
                api_base = self.model_config.get("api_base", "http://175.27.143.201:11434")
                response = requests.get(f"{api_base}/api/tags", timeout=5)
                if response.status_code == 200:
                    return {"status": "healthy", "model": "ollama", "api_base": api_base}
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
            else:
                return {"status": "healthy", "model": "agentscope"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


def create_moderation_agent(config: Dict[str, Any]) -> ModerationAgent:
    """创建内容审核代理工厂函数"""
    ai_config = config.get("ai", {})
    models_config = ai_config.get("models", {})
    default_model = ai_config.get("default_model", "ollama_qwen")
    
    # 获取默认模型配置
    model_config = models_config.get(default_model, {})
    
    return ModerationAgent(
        name="content_moderator",
        model_config=model_config,
        timeout=ai_config.get("timeout", 30.0),
        max_retries=ai_config.get("max_retries", 2)
    ) 