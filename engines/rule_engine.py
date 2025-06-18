import re
import yaml
from typing import List, Dict, Any, Set
from pathlib import Path

from models.enums import RiskLevel, ContentCategory
from models.models import RuleResult, SensitiveMatch
from utils.logger import get_logger
from .base_engine import BaseEngine


class RuleEngine(BaseEngine):
    """规则引擎：敏感词和正则表达式检测"""
    
    def __init__(self, config_path: str = "config"):
        super().__init__(name="rule_engine")
        self.config_path = Path(config_path)
        self.sensitive_words: Dict[str, Set[str]] = {}
        self.whitelist_words: Set[str] = set()
        self.regex_patterns: Dict[str, Dict[str, Any]] = {}
        self.logger = get_logger("rule_engine")
        self._load_rules()
    
    def _load_rules(self):
        """加载规则配置"""
        try:
            # 加载敏感词
            sensitive_file = self.config_path / "sensitive_words.yaml"
            if sensitive_file.exists():
                with open(sensitive_file, 'r', encoding='utf-8') as f:
                    sensitive_config = yaml.safe_load(f)
                    categories = sensitive_config.get('categories', {})
                    for category, config in categories.items():
                        if isinstance(config, dict) and config.get('enabled', True):
                            words = config.get('words', [])
                            self.sensitive_words[category] = set(words) if isinstance(words, list) else set()
                    
                    # 加载白名单
                    whitelist = sensitive_config.get('whitelist', [])
                    self.whitelist_words = set(whitelist) if isinstance(whitelist, list) else set()
                
                self.logger.info(f"加载敏感词库: {len(self.sensitive_words)} 个分类")
                self.logger.info(f"加载白名单: {len(self.whitelist_words)} 个词汇")
            
            # 加载正则表达式
            regex_file = self.config_path / "regex_patterns.yaml"
            if regex_file.exists():
                with open(regex_file, 'r', encoding='utf-8') as f:
                    regex_config = yaml.safe_load(f)
                    patterns = regex_config.get('patterns', {})
                    for pattern_name, pattern_config in patterns.items():
                        if pattern_config.get('enabled', True):
                            self.regex_patterns[pattern_name] = pattern_config
                self.logger.info(f"加载正则规则: {len(self.regex_patterns)} 个模式")
                
        except Exception as e:
            self.logger.error(f"加载规则配置失败: {e}")
            raise
    
    def reload_rules(self):
        """重新加载规则配置"""
        self._load_rules()
        self.logger.info("规则配置已重新加载")
    
    def check_sensitive_words(self, text: str) -> List[SensitiveMatch]:
        """检测敏感词"""
        matches = []
        text_lower = text.lower()
        
        for category, words in self.sensitive_words.items():
            for word in words:
                word_lower = word.lower().strip()
                if len(word_lower) < 2:  # 跳过太短的词
                    continue
                    
                # 使用正则表达式进行更精确的匹配
                # 对于字母数字组合，要求边界匹配
                if re.match(r'^[a-zA-Z0-9\s]+$', word_lower):
                    # 英文数字词汇需要词边界
                    pattern = r'\b' + re.escape(word_lower.replace(' ', r'\s*')) + r'\b'
                else:
                    # 中文词汇或混合词汇
                    if ' ' in word_lower:
                        # 包含空格的词汇，允许空格或其他空白字符
                        pattern = re.escape(word_lower).replace(r'\ ', r'\s*')
                    else:
                        # 普通中文词汇，要求完整匹配
                        pattern = r'(?<![a-zA-Z\u4e00-\u9fa5])' + re.escape(word_lower) + r'(?![a-zA-Z\u4e00-\u9fa5])'
                
                try:
                    regex = re.compile(pattern, re.IGNORECASE)
                    for match in regex.finditer(text_lower):
                        # 提取原文中的匹配文本
                        matched_text = text[match.start():match.end()]
                        
                        # 检查是否在白名单中
                        if not self._is_whitelisted(matched_text, text, match.start()):
                            matches.append(SensitiveMatch(
                                word=matched_text,
                                category=category,
                                position=match.start(),
                                context=text[max(0, match.start()-15):match.end()+15],
                                confidence=self._calculate_word_confidence(word, matched_text)
                            ))
                except re.error as e:
                    self.logger.warning(f"敏感词正则编译失败 '{word}': {e}")
                    # 降级到简单字符串匹配
                    start_pos = 0
                    while True:
                        pos = text_lower.find(word_lower, start_pos)
                        if pos == -1:
                            break
                        
                        # 检查边界和白名单
                        if (self._is_word_boundary(text_lower, pos, len(word_lower)) and
                            not self._is_whitelisted(text[pos:pos+len(word_lower)], text, pos)):
                            matches.append(SensitiveMatch(
                                word=text[pos:pos+len(word_lower)],
                                category=category,
                                position=pos,
                                context=text[max(0, pos-15):pos+len(word_lower)+15],
                                confidence=0.9
                            ))
                        start_pos = pos + 1
        
        return matches
    
    def _calculate_word_confidence(self, original_word: str, matched_text: str) -> float:
        """计算敏感词匹配的置信度"""
        # 完全匹配
        if original_word.lower() == matched_text.lower():
            return 1.0
        
        # 包含空格的变形匹配
        if ' ' in original_word and re.sub(r'\s+', '', original_word.lower()) == re.sub(r'\s+', '', matched_text.lower()):
            return 0.95
        
        # 其他情况
        return 0.8
    
    def _is_word_boundary(self, text: str, pos: int, length: int) -> bool:
        """检查是否为词边界"""
        # 检查前一个字符
        if pos > 0:
            prev_char = text[pos - 1]
            if prev_char.isalnum() or '\u4e00' <= prev_char <= '\u9fff':  # 中文字符
                return False
        
        # 检查后一个字符
        end_pos = pos + length
        if end_pos < len(text):
            next_char = text[end_pos]
            if next_char.isalnum() or '\u4e00' <= next_char <= '\u9fff':  # 中文字符
                return False
        
        return True
    
    def _is_whitelisted(self, matched_text: str, full_text: str, position: int) -> bool:
        """检查匹配的文本是否在白名单中或处于安全上下文"""
        matched_lower = matched_text.lower().strip()
        
        # 直接白名单检查
        if matched_lower in [w.lower() for w in self.whitelist_words]:
            return True
        
        # 上下文白名单检查
        context = full_text[max(0, position-50):position+len(matched_text)+50].lower()
        
        # 如果在新闻报道上下文中，一些政治词汇是安全的
        news_indicators = ['新华社', '报道', '电', '消息', '据悉', '官方', '声明', '贺信']
        if any(indicator in context for indicator in news_indicators):
            safe_in_news = ['党', '领导', '政府', '国家', '民族', '政策']
            if matched_lower in safe_in_news:
                return True
        
        return False
    
    def check_regex_patterns(self, text: str) -> List[SensitiveMatch]:
        """检测正则表达式模式"""
        matches = []
        
        for pattern_name, pattern_config in self.regex_patterns.items():
            try:
                pattern = pattern_config.get('pattern', '')
                category = pattern_config.get('category', 'unknown')
                description = pattern_config.get('description', pattern_name)
                risk_level = pattern_config.get('risk_level', 0.5)
                
                # 跳过一些可能产生大量误报的模式
                if pattern_name in ['separator_interference', 'special_char_replacement']:
                    # 这些模式需要更严格的条件
                    if not self._has_political_context(text):
                        continue
                
                regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for match in regex.finditer(text):
                    matched_text = match.group()
                    
                    # 过滤明显的误报
                    if self._is_false_positive(pattern_name, matched_text, text, match):
                        continue
                    
                    # 计算置信度
                    confidence = self._calculate_pattern_confidence(
                        pattern_name, matched_text, risk_level, text, match
                    )
                    
                    if (confidence > 0.3 and 
                        not self._is_whitelisted(matched_text, text, match.start())):  # 只保留置信度较高且不在白名单的匹配
                        matches.append(SensitiveMatch(
                            word=matched_text,
                            category=category,
                            position=match.start(),
                            context=text[max(0, match.start()-20):match.end()+20],
                            pattern_name=pattern_name,
                            description=description,
                            confidence=confidence
                        ))
            except re.error as e:
                self.logger.warning(f"正则表达式 {pattern_name} 编译失败: {e}")
        
        return matches
    
    def _has_political_context(self, text: str) -> bool:
        """检查文本是否包含政治相关上下文"""
        political_keywords = ['政府', '党', '领导', '政治', '国家', '官员', '政策']
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in political_keywords)
    
    def _is_false_positive(self, pattern_name: str, matched_text: str, full_text: str, match_obj) -> bool:
        """判断是否为误报"""
        
        # 针对不同模式的误报过滤
        if pattern_name == 'separator_interference':
            # 空格分离模式：确保不是正常的词语分离
            words = matched_text.split()
            if len(words) != 3:  # 只关注3个字符的分离
                return True
            # 检查是否为常见的正常组合
            normal_combinations = [
                ('我', '代', '表'), ('向', '大', '会'), ('全', '面', '发'),
                ('新', '时', '代'), ('少', '先', '队'), ('健', '康', '成')
            ]
            if tuple(words) in normal_combinations:
                return True
        
        elif pattern_name == 'leader_variants':
            # 领导人变形：确保真的是敏感表达
            if len(matched_text) < 3:
                return True
            # 确保在政治敏感上下文中
            context = full_text[max(0, match_obj.start()-50):match_obj.end()+50]
            if not any(word in context.lower() for word in ['打倒', '反对', '下台', '推翻']):
                return True
        
        elif pattern_name == 'political_abbreviations':
            # 政治缩写：避免误报常见缩写
            common_abbreviations = ['tv', 'pc', 'qq', 'vip', 'ceo', 'ai']
            if matched_text.lower() in common_abbreviations:
                return True
        
        return False
    
    def _calculate_pattern_confidence(self, pattern_name: str, matched_text: str, 
                                    risk_level: float, full_text: str, match_obj) -> float:
        """计算模式匹配的置信度"""
        base_confidence = risk_level
        
        # 根据模式类型调整置信度
        if pattern_name in ['leader_variants', 'seditious_combinations']:
            # 高敏感度模式
            base_confidence = min(base_confidence + 0.2, 1.0)
        
        elif pattern_name in ['separator_interference', 'special_char_replacement']:
            # 需要上下文确认的模式
            context = full_text[max(0, match_obj.start()-30):match_obj.end()+30]
            if any(word in context.lower() for word in ['打倒', '反对', '推翻', '颠覆']):
                base_confidence = min(base_confidence + 0.3, 1.0)
            else:
                base_confidence = max(base_confidence - 0.3, 0.1)
        
        # 根据匹配文本长度调整
        if len(matched_text) < 3:
            base_confidence *= 0.7
        elif len(matched_text) > 10:
            base_confidence *= 0.8
        
        return min(base_confidence, 1.0)
    
    def calculate_risk_level(self, matches: List[SensitiveMatch]) -> RiskLevel:
        """根据匹配结果计算风险等级"""
        if not matches:
            return RiskLevel.SAFE
        
        # 统计不同分类的匹配数
        category_counts = {}
        for match in matches:
            category_counts[match.category] = category_counts.get(match.category, 0) + 1
        
        # 高风险分类
        high_risk_categories = {'political', 'violence', 'illegal', 'adult'}
        medium_risk_categories = {'fraud', 'privacy', 'hate_speech', 'harassment'}
        
        # 判断风险等级
        for category in high_risk_categories:
            if category_counts.get(category, 0) > 0:
                return RiskLevel.BLOCKED
        
        for category in medium_risk_categories:
            if category_counts.get(category, 0) >= 2:  # 中风险分类出现2次以上
                return RiskLevel.RISKY
            elif category_counts.get(category, 0) > 0:
                return RiskLevel.SUSPICIOUS
        
        # 总匹配数判断
        total_matches = len(matches)
        if total_matches >= 5:
            return RiskLevel.RISKY
        elif total_matches >= 2:
            return RiskLevel.SUSPICIOUS
        else:
            return RiskLevel.SAFE
    
    def get_violated_categories(self, matches: List[SensitiveMatch]) -> List[ContentCategory]:
        """获取违规分类"""
        categories = set()
        category_mapping = {
            'political': ContentCategory.POLITICAL,
            'violence': ContentCategory.VIOLENCE,
            'adult': ContentCategory.ADULT,
            'illegal': ContentCategory.ILLEGAL,
            'fraud': ContentCategory.FRAUD,
            'privacy': ContentCategory.PRIVACY,
            'hate_speech': ContentCategory.HATE_SPEECH,
            'harassment': ContentCategory.HARASSMENT,
            'spam': ContentCategory.SPAM,
            'misinformation': ContentCategory.MISINFORMATION
        }
        
        for match in matches:
            if match.category in category_mapping:
                categories.add(category_mapping[match.category])
        
        return list(categories)
    
    async def analyze(self, text: str, **kwargs) -> RuleResult:
        """分析文本内容"""
        try:
            self.logger.debug(f"规则引擎开始分析，文本长度: {len(text)}")
            
            # 检测敏感词和正则模式
            sensitive_matches = self.check_sensitive_words(text)
            regex_matches = self.check_regex_patterns(text)
            
            all_matches = sensitive_matches + regex_matches
            
            # 计算风险等级和违规分类
            risk_level = self.calculate_risk_level(all_matches)
            violated_categories = self.get_violated_categories(all_matches)
            
            # 生成风险说明
            risk_reasons = []
            if sensitive_matches:
                risk_reasons.append(f"检测到 {len(sensitive_matches)} 个敏感词")
            if regex_matches:
                risk_reasons.append(f"检测到 {len(regex_matches)} 个敏感模式")
            
            # 计算置信度分数（基于匹配数量和类型）
            confidence_score = min(len(all_matches) * 0.3 + 0.1, 1.0) if all_matches else 0.1
            
            result = RuleResult(
                risk_level=risk_level,
                violated_categories=violated_categories,
                risk_score=min(len(all_matches) * 0.2, 1.0),  # 简单评分
                risk_reasons=risk_reasons,
                confidence_score=confidence_score,
                sensitive_matches=all_matches,
                processing_time=0.0  # 规则引擎处理时间很短
            )
            
            self.logger.debug(f"规则引擎分析完成，风险等级: {risk_level.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"规则引擎分析失败: {e}")
            return RuleResult(
                risk_level=RiskLevel.SAFE,
                violated_categories=[],
                risk_score=0.0,
                risk_reasons=[f"规则引擎错误: {str(e)}"],
                confidence_score=0.0,
                sensitive_matches=[]
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            sensitive_categories = len(self.sensitive_words)
            regex_patterns = len(self.regex_patterns)
            
            return {
                "status": "healthy",
                "sensitive_categories": sensitive_categories,
                "regex_patterns": regex_patterns,
                "config_path": str(self.config_path)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

def create_rule_engine(config: Dict[str, Any]) -> RuleEngine:
    """创建规则引擎工厂函数"""
    engine_config = config.get("engines", {})
    rule_config = engine_config.get("rule", {})
    
    config_path = rule_config.get("config_path", "config")
    
    return RuleEngine(config_path=config_path) 