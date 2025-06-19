from utils.config import get_config_manager

# 全局配置管理器实例
config_manager = get_config_manager()

# 为了保持向后兼容，创建一个settings对象
class Settings:
    def __init__(self):
        self.config_manager = config_manager
    
    def __getattr__(self, name):
        # 将属性访问转换为配置键访问
        key_mapping = {
            'PLATFORM': 'platform.current',
            'ALIYUN_ACCESS_KEY_ID': 'platform.aliyun.access_key_id',
            'ALIYUN_ACCESS_KEY_SECRET': 'platform.aliyun.access_key_secret',
            'aliyun_region': 'platform.aliyun.region',
            'WANGYIYUN_SECRET_ID': 'platform.wangyiyun.secret_id',
            'WANGYIYUN_SECRET_KEY': 'platform.wangyiyun.secret_key',
            'IMAGE_BUSINESS_ID': 'platform.wangyiyun.image_business_id',
            'AUDIO_BUSINESS_ID': 'platform.wangyiyun.audio_business_id',
            'VIDEO_BUSINESS_ID': 'platform.wangyiyun.video_business_id'
        }
        
        if name in key_mapping:
            return self.config_manager.get(key_mapping[name])
        
        # 如果没有映射，尝试直接从配置中获取
        return self.config_manager.get(name.lower())
    
    def get_config(self, key, default=None):
        return self.config_manager.get(key, default)
    
    def reload(self):
        return self.config_manager.reload()

settings = Settings()