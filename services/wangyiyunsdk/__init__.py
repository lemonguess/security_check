import json

from config import settings
from .image_submit import ImageSubmitAPIDemo
from .audio_submit import AudioSubmitAPIDemo
from .video_submit import VideoSubmitAPIDemo
from .image_query import ImageQueryByTaskIdsDemo
from .audio_query import AudioQueryByTaskIdsDemo
from .video_query import VideoQueryByTaskIdsDemo
from models.database import Task, TaskType, TaskStatus
from datetime import datetime
import uuid

# 初始化 SDK 实例
image_create_api = ImageSubmitAPIDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.IMAGE_BUSINESS_ID)
audio_create_api = AudioSubmitAPIDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.AUDIO_BUSINESS_ID)
video_create_api = VideoSubmitAPIDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.VIDEO_BUSINESS_ID)
image_query_api = ImageQueryByTaskIdsDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.IMAGE_BUSINESS_ID)
audio_query_api = AudioQueryByTaskIdsDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.AUDIO_BUSINESS_ID)
video_query_api = VideoQueryByTaskIdsDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.VIDEO_BUSINESS_ID)

def check_images_service(img_path_list, callback_url):
    results = []
    for img_path in img_path_list:
        data_id = str(uuid.uuid4())
        params = {
        "images": json.dumps([{"name": data_id, "data": img_path, "level": 2}])
    }

        try:
            res = image_create_api.check(params)
            task_id = res["result"][0]['taskId']
            Task.create(
                id=data_id,
                task_id=task_id,
                type=TaskType.IMAGE.value,
                status=TaskStatus.CREATED.value,
                create_time=datetime.now(),
                update_time=datetime.now(),
                callback_url=callback_url,
                content=img_path
            )
            results.append({
                "file_path": img_path,
                "task_id": task_id,
                "msg": "Pending"
            })
        except Exception as e:
            results.append({
                "file_path": img_path,
                "task_id": None,
                "msg": f"Error: {str(e)}"
            })
    return results

def check_audios_service(audio_path_list, callback_url):
    results = []
    for audio_path in audio_path_list:
        data_id = str(uuid.uuid4())
        params = {"dataId": data_id, "url": audio_path}
        try:
            res = audio_create_api.check(params)
            task_id = res["result"][0]['taskId']
            Task.create(
                id=data_id,
                task_id=task_id,
                type=TaskType.AUDIO.value,
                status=TaskStatus.CREATED.value,
                create_time=datetime.now(),
                update_time=datetime.now(),
                callback_url=callback_url,
                content=audio_path
            )
            results.append({
                "file_path": audio_path,
                "task_id": task_id,
                "msg": "Pending"
            })
        except Exception as e:
            results.append({
                "file_path": audio_path,
                "task_id": None,
                "msg": f"Error: {str(e)}"
            })
    return results

def check_videos_service(video_path_list, callback_url):
    results = []
    for video_path in video_path_list:
        data_id = str(uuid.uuid4())
        params = {"dataId": data_id, "url": video_path}
        try:
            res = video_create_api.check(params)
            task_id = res["result"][0]['taskId']
            Task.create(
                id=data_id,
                task_id=task_id,
                type=TaskType.VIDEO.value,
                status=TaskStatus.CREATED.value,
                create_time=datetime.now(),
                update_time=datetime.now(),
                callback_url=callback_url,
                content=video_path
            )
            results.append({
                "file_path": video_path,
                "task_id": task_id,
                "msg": "Pending"
            })
        except Exception as e:
            results.append({
                "file_path": video_path,
                "task_id": None,
                "msg": f"Error: {str(e)}"
            })
    return results

def query_task(task_id, task_type):
    if task_type == TaskType.IMAGE.value:
        api = image_query_api
    elif task_type == TaskType.AUDIO.value:
        api = audio_query_api
    elif task_type == TaskType.VIDEO.value:
        api = video_query_api
    else:
        raise ValueError("Invalid task type")
    msg = ""

    params = {"taskIds": [task_id]}
    result = api.query(params)
    if result["code"] == 200:
        is_compliant = False
        result = result["result"][0]
        if result["status"] != 0:
            msg = "审核中"
            return
        labels = result.get("labels", [])
        label_dict = {i["label"]: i["rate"] for i in labels}
        if label_dict[100]:
            msg = f"""涉嫌<font color="red">色情</font>，置信度：<font color="red">{label_dict[100]}</font>"""
        # 根据以下内容编写 elif分支 # 100：色情，110：性感低俗，200：广告，210：二维码，260：广告法，300：暴恐，400：违禁，500：涉政，800：恶心类，900：其他，1100：涉价值观
        elif label_dict[110]:
            msg = f"""涉嫌<font color="red">性感低俗</font>，置信度：<font color="red">{label_dict[110]}</font>"""
        elif label_dict[300]:
            msg = f"""涉嫌<font color="red">暴恐</font>，置信度：<font color="red">{label_dict[300]}</font>"""
        elif label_dict[400]:
            msg = f"""涉嫌<font color="red">违禁</font>，置信度：<font color="red">{label_dict[400]}</font>"""
        elif label_dict[800]:
            msg = f"""涉嫌<font color="red">恶心</font>，置信度：<font color="red">{label_dict[800]}</font>"""
        else:
            msg = f"""合规"""
            is_compliant = True
        task = Task.get(Task.task_id == task_id)
        task.is_compliant = is_compliant
        task.status = TaskStatus.SUCCESS.value
        task.result_text = msg
        task.update_time = datetime.now()
        task.save()
        return task
    else:
        raise Exception(f"Error querying task: {result['msg']}")
