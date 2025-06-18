"""
系统枚举定义
"""

from enum import Enum
# 枚举类型：任务状态
class TaskStatus(Enum):
    CREATED = 0  # 任务创建
    SUCCESS = 1  # 任务成功
    FAILED = 2   # 任务失败

# 枚举类型：任务类型
class TaskType(Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"

class RiskLevel(str, Enum):
    """内容风险等级"""
    SAFE = "safe"           # 安全
    SUSPICIOUS = "suspicious"  # 可疑
    RISKY = "risky"        # 高风险
    BLOCKED = "blocked"     # 阻止/禁止


class ContentCategory(str, Enum):
    """内容分类"""
    POLITICAL = "political"           # 政治敏感
    VIOLENCE = "violence"            # 暴力内容
    ADULT = "adult"                  # 成人内容
    ILLEGAL = "illegal"              # 违法内容
    HATE_SPEECH = "hate_speech"      # 仇恨言论
    PRIVACY = "privacy"              # 隐私泄露
    SPAM = "spam"                    # 垃圾信息
    MISINFORMATION = "misinformation" # 虚假信息
    HARASSMENT = "harassment"        # 骚扰内容
    FRAUD = "fraud"                  # 诈骗信息
    OTHER = "other"                  # 其他


class EngineType(str, Enum):
    """检测引擎类型"""
    AI = "ai"               # AI代理检测
    RULE = "rule"           # 规则引擎检测
    REGEX = "regex"         # 正则表达式检测
    KEYWORD = "keyword"     # 关键词检测
    ML = "ml"              # 机器学习模型检测


class ProcessingStatus(str, Enum):
    """处理状态"""
    PENDING = "pending"     # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 处理失败
    TIMEOUT = "timeout"        # 超时


class ActionType(str, Enum):
    """处理动作类型"""
    APPROVE = "approve"     # 通过
    REJECT = "reject"       # 拒绝
    REVIEW = "review"       # 人工审核
    MASK = "mask"          # 内容脱敏
    WARNING = "warning"     # 警告