"""
配置管理工具
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from utils.exceptions import ConfigurationError


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config_cache = {}
        self._load_env()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        current_dir = Path(__file__).parent.parent
        return str(current_dir / "config" / "default.yaml")
    
    def _load_env(self):
        """加载环境变量"""
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """加载配置文件"""
        if not force_reload and self.config_cache:
            return self.config_cache
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 环境变量替换
            config = self._resolve_env_vars(config)
            
            # 加载其他配置文件
            config = self._load_additional_configs(config)
            
            self.config_cache = config
            return config
            
        except FileNotFoundError:
            raise ConfigurationError(f"配置文件未找到: {self.config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"配置文件格式错误: {e}")
    
    def _resolve_env_vars(self, config: Any) -> Any:
        """解析环境变量"""
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            default_value = None
            if ":" in env_var:
                env_var, default_value = env_var.split(":", 1)
            return os.getenv(env_var, default_value)
        else:
            return config
    
    def _load_additional_configs(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """加载额外的配置文件"""
        config_dir = Path(self.config_path).parent
        
        # 加载敏感词配置
        sensitive_words_path = config_dir / "sensitive_words.yaml"
        if sensitive_words_path.exists():
            with open(sensitive_words_path, 'r', encoding='utf-8') as f:
                config['sensitive_words'] = yaml.safe_load(f)
        
        # 加载正则规则配置
        regex_patterns_path = config_dir / "regex_patterns.yaml"
        if regex_patterns_path.exists():
            with open(regex_patterns_path, 'r', encoding='utf-8') as f:
                config['regex_patterns'] = yaml.safe_load(f)
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套key"""
        config = self.load_config()
        
        keys = key.split('.')
        value = config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """设置配置值（运行时）"""
        if not self.config_cache:
            self.load_config()
        
        keys = key.split('.')
        config = self.config_cache
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def reload(self):
        """重新加载配置"""
        self.config_cache.clear()
        return self.load_config(force_reload=True)


# 全局配置管理器实例
_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载配置的便捷函数"""
    if config_path:
        manager = ConfigManager(config_path)
    else:
        manager = get_config_manager()
    return manager.load_config()


def get_config(key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    return get_config_manager().get(key, default)