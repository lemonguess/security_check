from typing import List
from pydantic import BaseModel

class CheckRequest(BaseModel):
    filePathList: list[str]
    callBackUrl: str

class CheckResponse(BaseModel):
    file_path: str
    task_id: str
    msg: str

class TaskStatusRequest(BaseModel):
    task_ids: List[str]  # 接口入参为任务 ID 列表

class TaskStatusResponse(BaseModel):
    task_id: str  # 任务 ID
    status: int   # 任务状态
