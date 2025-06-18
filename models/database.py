import os
import sys

from peewee import Model, CharField, DateTimeField, IntegerField, TextField, BooleanField
from peewee import SqliteDatabase
from enum import Enum
import datetime

# 数据库连接
db = SqliteDatabase('security_check.db')

# 枚举类型：任务状态
class TaskStatus(Enum):
    CREATED = 0  # 任务创建
    SUCCESS = 1  # 任务成功
    FAILED = 2   # 任务失败

# 枚举类型：任务类型
class TaskType(Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
class CustomDateTimeField(DateTimeField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.format = '%Y-%m-%d %H:%M:%S'
    def python_value(self, value):
        value = super().python_value(value)
        if value is not None and type(value) is datetime.datetime:
            return value.strftime(self.format)
        return value
# 任务表
class Task(Model):
    id = CharField(primary_key=True)  # 唯一标识
    task_id = CharField(null=True)
    type = CharField(choices=[(t.value, t.name) for t in TaskType])  # 任务类型
    status = IntegerField(choices=[(s.value, s.name) for s in TaskStatus])  # 任务状态
    callback_url = CharField(null=True)  # 回调地址
    content = CharField(null=True)  # 存储任务内容，一般为http链接
    is_compliant = BooleanField(null=True)
    result_text = TextField(null=True)
    create_time = CustomDateTimeField(default=datetime.datetime.now, help_text="创建时间")
    update_time = CustomDateTimeField(default=datetime.datetime.now, help_text="更新时间")

    class Meta:
        database = db

# 创建表
def create_tables():
    # 判断数据库文件是否存在
    if not os.path.exists('security_check.db'):
        with db:
            db.create_tables([Task])

if __name__ == "__main__":
    create_tables()