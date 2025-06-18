from aliyunsdkcore import client
from aliyunsdkgreen.request.v20180509 import (
    ImageSyncScanRequest,
    VoiceAsyncScanRequest,
    VideoAsyncScanRequest
)
from aliyunsdkcore.profile import region_provider
# from aliyunsdkgreenextension.request.extension import HttpContentHelper
import json
import uuid
from config import settings

def check_images_service(imgPathList):
    clt = client.AcsClient(settings.ALIYUN_ACCESS_KEY_ID, settings.ALIYUN_ACCESS_KEY_SECRET, settings.aliyun_region)
    request = ImageSyncScanRequest.ImageSyncScanRequest()
    request.set_accept_format('JSON')

    results = []
    for img_path in imgPathList:
        task = {
            "dataId": str(uuid.uuid1()),
            "url": img_path
        }
        request.set_content(json.dumps({"tasks": [task], "scenes": ["porn"]}))
        response = clt.do_action_with_exception(request)
        result = json.loads(response)
        if 200 == result["code"]:
            taskResults = result["data"]
            for taskResult in taskResults:
                if 200 == taskResult["code"]:
                    sceneResults = taskResult["results"]
                    for sceneResult in sceneResults:
                        suggestion = sceneResult["suggestion"]
                        compliance = suggestion == "pass"
                        msg = f"图片合规性: {suggestion}"
                        results.append({
                            "file_path": img_path,
                            "compliance": compliance,
                            "msg": msg
                        })
    return results

def check_audios_service(audioPathList):
    clt = client.AcsClient(settings.ALIYUN_ACCESS_KEY_ID, settings.ALIYUN_ACCESS_KEY_SECRET, settings.aliyun_region)
    request = VoiceAsyncScanRequest.VoiceAsyncScanRequest()
    request.set_accept_format('JSON')

    results = []
    for audio_path in audioPathList:
        task = {
            "url": audio_path,
        }
        request.set_content(HttpContentHelper.toValue({"tasks": [task], "scenes": ["antispam"], "live": False}))
        response = clt.do_action_with_exception(request)
        result = json.loads(response)
        if 200 == result["code"]:
            taskResults = result["data"]
            for taskResult in taskResults:
                code = taskResult["code"]
                if 200 == code:
                    taskId = taskResult["taskId"]
                    compliance = True  # 假设任务提交成功即合规
                    msg = f"音频检测任务ID: {taskId}"
                    results.append({
                        "file_path": audio_path,
                        "compliance": compliance,
                        "msg": msg
                    })
    return results

def check_videos_service(videoPathList):
    clt = client.AcsClient(settings.ALIYUN_ACCESS_KEY_ID, settings.ALIYUN_ACCESS_KEY_SECRET, settings.aliyun_region)
    request = VideoAsyncScanRequest.VideoAsyncScanRequest()
    request.set_accept_format('JSON')

    results = []
    for video_path in videoPathList:
        task = {
            "dataId": str(uuid.uuid1()),
            "url": video_path
        }
        request.set_content(HttpContentHelper.toValue({"tasks": [task], "scenes": ["terrorism"]}))
        response = clt.do_action_with_exception(request)
        result = json.loads(response)
        if 200 == result["code"]:
            taskResults = result["data"]
            for taskResult in taskResults:
                code = taskResult["code"]
                if 200 == code:
                    taskId = taskResult["taskId"]
                    compliance = True  # 假设任务提交成功即合规
                    msg = f"视频检测任务ID: {taskId}"
                    results.append({
                        "file_path": video_path,
                        "compliance": compliance,
                        "msg": msg
                    })
    return results