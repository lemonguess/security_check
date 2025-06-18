from pydantic_settings import BaseSettings
import configparser
from pathlib import Path

class Settings(BaseSettings):
    PLATFORM: str
    class Config:
        env_file = "config/conf.ini"  # 更新路径
        env_file_encoding = "utf-8"
        extra = 'allow'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._load_default_config()
        self._load_platform_config()


    def _load_platform_config(self):
        """根据 PLATFORM 动态加载配置"""
        platform_config = {
            "aliyun": self._load_aliyun_config,
            "wangyiyun": self._load_wangyiyun_config,
        }
        loader = platform_config.get(self.PLATFORM.lower())
        if not loader:
            raise ValueError(f"Unsupported PLATFORM: {self.PLATFORM}")
        loader()

    def _load_aliyun_config(self):
        """加载阿里云配置"""
        self.ALIYUN_ACCESS_KEY_ID = self._get_config_value("aliyun", "ALIYUN_ACCESS_KEY_ID")
        self.ALIYUN_ACCESS_KEY_SECRET = self._get_config_value("aliyun", "ALIYUN_ACCESS_KEY_SECRET")
        self.aliyun_region = self._get_config_value("aliyun", "ALIYUN_REGION")

    def _load_wangyiyun_config(self):
        """加载网易云配置"""
        self.WANGYIYUN_SECRET_ID = self._get_config_value("wangyiyun", "WANGYIYUN_SECRET_ID")
        self.WANGYIYUN_SECRET_KEY = self._get_config_value("wangyiyun", "WANGYIYUN_SECRET_KEY")
        self.IMAGE_BUSINESS_ID = self._get_config_value("wangyiyun", "IMAGE_BUSINESS_ID")
        self.AUDIO_BUSINESS_ID = self._get_config_value("wangyiyun", "AUDIO_BUSINESS_ID")
        self.VIDEO_BUSINESS_ID = self._get_config_value("wangyiyun", "VIDEO_BUSINESS_ID")

    def _load_default_config(self):
        """加载 DEFAULT 部分的配置"""
        config = configparser.ConfigParser()
        config_path = Path(self.Config.env_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        try:
            config.read(config_path, encoding=self.Config.env_file_encoding)
            default_section = config["DEFAULT"]
            for key, value in default_section.items():
                setattr(self, key, value)
        except Exception as e:
            raise RuntimeError(f"Failed to load default config: {e}")

    def _get_config_value(self, section, key, default=None):
        """从配置文件中获取指定 section 和 key 的值"""
        config = configparser.ConfigParser()
        config_path = Path(self.Config.env_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        try:
            config.read(config_path, encoding=self.Config.env_file_encoding)
            return config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if default is not None:
                return default
            raise KeyError(f"Key '{key}' not found in section '{section}'")
