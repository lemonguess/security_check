import os
import sys

# 将项目根目录添加到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.database import db, Contents, Task, AuditStatus, ColumnType
from peewee import *

def query_contents():
    """查询所有待审核的内容"""
    return Contents.select().where(Contents.audit_status == AuditStatus.PENDING.value)

def add_content(title, url, content, column_type):
    """新增一条内容"""
    return Contents.create(
        title=title,
        url=url,
        content=content,
        column_type=column_type
    )

if __name__ == '__main__':
    # 示例：新增一条内容
    # new_content = add_content(
    #     title="示例标题",
    #     url="http://example.com/sample",
    #     content="这是一条示例内容。",
    #     column_type=ColumnType.COMPANY_DYNAMIC.value
    # )
    # print(f"新增内容成功，ID: {new_content.id}")

    # 示例：查询待审核的内容
    pending_contents = query_contents()
    print("\n待审核的内容：")
    for content in pending_contents:
        print(f"- ID: {content.id}, 标题: {content.title}, 状态: {content.audit_status}")