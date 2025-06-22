import json

try:
    from config import settings
except ImportError:
    settings = None

from .image_submit import ImageSubmitAPIDemo
from .audio_submit import AudioSubmitAPIDemo
from .video_submit import VideoSubmitAPIDemo
from .text_submit import TextSubmitAPIDemo
from .image_query import ImageQueryByTaskIdsDemo
from .audio_query import AudioQueryByTaskIdsDemo
from .video_query import VideoQueryByTaskIdsDemo
from .text_query import TextQueryByTaskIdsDemo
from models.database import Task, TaskType, TaskStatus
from datetime import datetime
import uuid
import json

# 初始化 SDK 实例
if settings:
    image_create_api = ImageSubmitAPIDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.IMAGE_BUSINESS_ID)
    audio_create_api = AudioSubmitAPIDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.AUDIO_BUSINESS_ID)
    video_create_api = VideoSubmitAPIDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.VIDEO_BUSINESS_ID)
    text_create_api = TextSubmitAPIDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.TEXT_BUSINESS_ID)
    image_query_api = ImageQueryByTaskIdsDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.IMAGE_BUSINESS_ID)
    audio_query_api = AudioQueryByTaskIdsDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.AUDIO_BUSINESS_ID)
    video_query_api = VideoQueryByTaskIdsDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.VIDEO_BUSINESS_ID)
    text_query_api = TextQueryByTaskIdsDemo(settings.WANGYIYUN_SECRET_ID, settings.WANGYIYUN_SECRET_KEY, settings.TEXT_BUSINESS_ID)
else:
    # 如果没有配置，使用默认值或抛出错误
    image_create_api = None
    audio_create_api = None
    video_create_api = None
    text_create_api = None
    image_query_api = None
    audio_query_api = None
    video_query_api = None
    text_query_api = None

def check_images_service(img_path_list, callback_url=""):
    if image_create_api is None:
        return [{"error": "Image API not initialized"}]
    
    results = []
    for img_path in img_path_list:
        data_id = str(uuid.uuid4())
        params = {
        "images": json.dumps([{"name": data_id, "data": img_path, "level": 2}])
    }

        try:
            res = image_create_api.check(params)
            if res and res.get("result"):
                task_id = res["result"][0]['taskId']
            else:
                raise Exception("Invalid response from image API")
            Task.create(
                id=data_id,
                task_id=task_id,
                type=TaskType.IMAGE.value,
                status=TaskStatus.CREATED.value,
                create_time=datetime.now(),
                update_time=datetime.now(),
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

def check_audios_service(audio_path_list, callback_url=""):
    if audio_create_api is None:
        return [{"error": "Audio API not initialized"}]
    
    results = []
    for audio_path in audio_path_list:
        data_id = str(uuid.uuid4())
        params = {"dataId": data_id, "url": audio_path}
        try:
            res = audio_create_api.check(params)
            if res and res.get("result"):
                task_id = res["result"][0]['taskId']
            else:
                raise Exception("Invalid response from audio API")
            Task.create(
                id=data_id,
                task_id=task_id,
                type=TaskType.AUDIO.value,
                status=TaskStatus.CREATED.value,
                create_time=datetime.now(),
                update_time=datetime.now(),
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

def check_videos_service(video_path_list, callback_url=""):
    if video_create_api is None:
        return [{"error": "Video API not initialized"}]
    
    results = []
    for video_path in video_path_list:
        data_id = str(uuid.uuid4())
        params = {"dataId": data_id, "url": video_path}
        try:
            res = video_create_api.check(params)
            if res and res.get("result"):
                task_id = res["result"][0]['taskId']
            else:
                raise Exception("Invalid response from video API")
            Task.create(
                id=data_id,
                task_id=task_id,
                type=TaskType.VIDEO.value,
                status=TaskStatus.CREATED.value,
                create_time=datetime.now(),
                update_time=datetime.now(),
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
    elif task_type == TaskType.TEXT.value:
        api = text_query_api
    else:
        raise Exception(f"Unsupported task type: {task_type}")
    
    if api is None:
        raise Exception(f"API not initialized for task type: {task_type}")
    
    params = {"taskIds": [task_id]}
    result = api.query(params)
    if result and result.get("code") == 200:
        is_compliant = False
        result_data = result.get("result", [])
        if not result_data:
            return None
        result_item = result_data[0]
        if result_item.get("status") != 0:
            msg = "审核中"
            return None
        labels = result_item.get("labels", [])
        label_dict = {i["label"]: i["rate"] for i in labels if isinstance(i, dict)}
        if label_dict.get(100):
            msg = f"""涉嫌<font color="red">色情</font>，置信度：<font color="red">{label_dict[100]}</font>"""
        # 根据以下内容编写 elif分支 # 100：色情，110：性感低俗，200：广告，210：二维码，260：广告法，300：暴恐，400：违禁，500：涉政，800：恶心类，900：其他，1100：涉价值观
        elif label_dict.get(110):
            msg = f"""涉嫌<font color="red">性感低俗</font>，置信度：<font color="red">{label_dict[110]}</font>"""
        elif label_dict.get(300):
            msg = f"""涉嫌<font color="red">暴恐</font>，置信度：<font color="red">{label_dict[300]}</font>"""
        elif label_dict.get(400):
            msg = f"""涉嫌<font color="red">违禁</font>，置信度：<font color="red">{label_dict[400]}</font>"""
        elif label_dict.get(800):
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
        error_msg = result.get('msg', 'Unknown error') if result else 'No response'
        raise Exception(f"Error querying task: {error_msg}")


def check_text_service(text_content, callback_url=""):
    """文本审核服务"""
    if text_create_api is None:
        return {"error": "Text API not initialized"}
    
    data_id = str(uuid.uuid4())
    _params = {
        "dataId": data_id,
        "content": text_content,
        "action": "0"
    }
    params = {
        "texts": json.dumps([_params])
    }
    try:
        res = text_create_api.check(params)
        if res and res.get("code") == 200:
            task_id = res["result"][0]["taskId"]
            Task.create(
                id=data_id,
                task_id=task_id,
                type=TaskType.TEXT.value,
                status=TaskStatus.CREATED.value,
                create_time=datetime.now(),
                update_time=datetime.now(),
                content=text_content
            )
            return {
                "task_id": task_id,
                "data_id": data_id,
                "msg": "Pending"
            }
        else:
            return {
                "task_id": None,
                "data_id": data_id,
                "msg": f"Error: {res.get('msg', 'Unknown error') if res else 'No response'}"
            }
    except Exception as e:
        return {
            "task_id": None,
            "data_id": data_id,
            "msg": f"Error: {str(e)}"
        }
