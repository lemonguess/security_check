"""
系统异常定义
"""


class ModerationError(Exception):
    """内容审核基础异常"""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(ModerationError):
    """配置错误异常"""

    def __init__(self, message: str, config_key: str = None):
        self.config_key = config_key
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            details={"config_key": config_key}
        )


class ModelError(ModerationError):
    """模型相关异常"""

    def __init__(self, message: str, model_name: str = None, provider: str = None):
        self.model_name = model_name
        self.provider = provider
        super().__init__(
            message=message,
            error_code="MODEL_ERROR",
            details={
                "model_name": model_name,
                "provider": provider
            }
        )


class ValidationError(ModerationError):
    """数据验证异常"""

    def __init__(self, message: str, field: str = None, value: str = None):
        self.field = field
        self.value = value
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={
                "field": field,
                "value": value
            }
        )


class EngineError(ModerationError):
    """检测引擎异常"""

    def __init__(self, message: str, engine_type: str = None):
        self.engine_type = engine_type
        super().__init__(
            message=message,
            error_code="ENGINE_ERROR",
            details={"engine_type": engine_type}
        )


class TimeoutError(ModerationError):
    """超时异常"""

    def __init__(self, message: str, timeout_duration: float = None):
        self.timeout_duration = timeout_duration
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            details={"timeout_duration": timeout_duration}
        )


class RateLimitError(ModerationError):
    """限流异常"""

    def __init__(self, message: str, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details={"retry_after": retry_after}
        )