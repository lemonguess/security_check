import os
import sys
from config import settings
PLATFORM = settings.PLATFORM

# 动态导入模块
check_audios_service = check_images_service = check_videos_service = None
if PLATFORM == "wangyiyun":
    from .wangyiyunsdk import (
        check_images_service,
        check_audios_service,
        check_videos_service
    )
elif PLATFORM == "aliyun":
    from aliyunsdkcore import client
    from aliyunsdkgreen.request.v20180509 import (
        ImageSyncScanRequest,
        VoiceAsyncScanRequest,
        VideoAsyncScanRequest
    )
    from aliyunsdkcore.profile import region_provider
else:
    sys.exit("导入检测平台信息失败")

