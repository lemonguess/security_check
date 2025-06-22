import asyncio
from services.wangyiyunsdk import query_task
from models.database import Task
import asyncio

async def check_tasks():
    while True:
        tasks = Task.select().where(Task.status == 0)  # 查询所有状态为 CREATED 的任务
        for task in tasks:
            try:
                await asyncio.sleep(1)  # 模拟异步操作
                task = query_task(task.task_id, task.type)
            except Exception as e:
                print(f"Error checking task {task.id}: {e}")
        await asyncio.sleep(60)  # 每分钟检查一次

def start_task_loop():
    asyncio.run(check_tasks())