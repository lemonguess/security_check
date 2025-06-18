import asyncio
from services.wangyiyunsdk import query_task
from models.database import Task
import aiohttp  # 新增: 引入 aiohttp 库用于异步 HTTP 请求
from playhouse.shortcuts import model_to_dict
async def check_tasks():
    while True:
        tasks = Task.select().where(Task.status == 0)  # 查询所有状态为 CREATED 的任务
        for task in tasks:
            try:
                await asyncio.sleep(1)  # 模拟异步操作
                task = query_task(task.task_id, task.type)
                # 新增: 发送任务信息到 callback_url
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        task.callback_url,  # 使用任务的 callback_url
                        json=model_to_dict(task)  # 将任务对象转换为字典
                    ) as response:
                        if response.status != 200:
                            print(f"CallbackUrl: {task.callback_url} \nError sending task {task.id} to callback_url: {response.status}")
            except Exception as e:
                print(f"Error checking task {task.id}: {e}")
        await asyncio.sleep(60)  # 每分钟检查一次

def start_task_loop():
    asyncio.run(check_tasks())