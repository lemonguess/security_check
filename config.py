#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置文件
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 网易易盾配置
    WANGYIYUN_SECRET_ID: str = os.getenv("WANGYIYUN_SECRET_ID", "")
    WANGYIYUN_SECRET_KEY: str = os.getenv("WANGYIYUN_SECRET_KEY", "")
    
    # 业务ID配置
    IMAGE_BUSINESS_ID: str = os.getenv("IMAGE_BUSINESS_ID", "")
    AUDIO_BUSINESS_ID: str = os.getenv("AUDIO_BUSINESS_ID", "")
    VIDEO_BUSINESS_ID: str = os.getenv("VIDEO_BUSINESS_ID", "")
    TEXT_BUSINESS_ID: str = os.getenv("TEXT_BUSINESS_ID", "")
    
    # 阿里云配置
    ALIYUN_ACCESS_KEY_ID: str = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
    ALIYUN_ACCESS_KEY_SECRET: str = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
    aliyun_region: str = os.getenv("ALIYUN_REGION", "cn-shanghai")
    
    # 平台配置
    PLATFORM: str = os.getenv("PLATFORM", "wangyiyun")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()