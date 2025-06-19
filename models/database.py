import os
import sys
from datetime import datetime
from peewee import *
from pydantic import BaseModel

# 添加项目根目录到Python路径
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 直接导入enums模块
    import enums
    TaskType = enums.TaskType
    TaskStatus = enums.TaskStatus
    ColumnType = enums.ColumnType
else:
    from .enums import TaskType, TaskStatus, ColumnType

# 数据库连接
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_root, 'security_check.db')
db = SqliteDatabase(db_path)


class CustomDateTimeField(DateTimeField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.format = '%Y-%m-%d %H:%M:%S'
    def python_value(self, value):
        value = super().python_value(value)
        if value is not None and isinstance(value, datetime):
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
    created_at = CustomDateTimeField(default=datetime.now, help_text="创建时间")
    updated_at = CustomDateTimeField(default=datetime.now, help_text="更新时间")

    class Meta:
        database = db

class Contents(Model):
    id = AutoField()
    title = CharField(null=True)
    url = CharField(null=True)
    html = TextField(null=True)  # 存储原始HTML内容
    content = TextField(null=True)  # 存储去除HTML标签后的纯文本内容
    column_type = CharField(choices=[(t.value, t.name) for t in ColumnType])
    publish_time = CharField(null=True)
    images = TextField(null=True)  # 存储图片URL列表，JSON格式
    audios = TextField(null=True)  # 存储音频URL列表，JSON格式
    videos = TextField(null=True)  # 存储视频URL列表，JSON格式
    created_at = CustomDateTimeField(default=datetime.now, help_text="创建时间")
    updated_at = CustomDateTimeField(default=datetime.now, help_text="更新时间")

    class Meta:
        database = db
        indexes = (
            (('title', 'url'), True),  # 联合唯一键
        )

# 创建表
def create_tables():
    # 强制创建表，包含所有字段
    with db:
        db.create_tables([Task, Contents], safe=True)
        print("数据库表创建成功！")
        print("- Task 表")
        print("- Contents 表 (包含 images, audios, videos 字段)")

if __name__ == "__main__":
    create_tables()