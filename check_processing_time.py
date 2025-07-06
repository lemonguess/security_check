from models.database import Contents, AuditStats, db
from models.enums import AuditStatus
import json

def check_processing_time():
    """检查处理时间数据"""
    try:
        db.connect(reuse_if_open=True)
        
        print("=== 检查AuditStats表中的处理时间 ===")
        for stats in AuditStats.select():
            print(f"日期: {stats.date}, 总审核: {stats.total_audits}, 总处理时间: {stats.total_processing_time}")
        
        print("\n=== 检查Contents表中的processing_content字段 ===")
        audited_contents = Contents.select().where(
            (Contents.audit_status == AuditStatus.APPROVED.value) |
            (Contents.audit_status == AuditStatus.REJECTED.value)
        ).limit(10)
        
        for content in audited_contents:
            print(f"ID: {content.id}, Status: {content.audit_status}, Processing: {content.processing_content}")
            if content.processing_content:
                try:
                    processing_data = json.loads(content.processing_content)
                    print(f"  解析后的处理数据: {processing_data}")
                    if 'processing_time' in processing_data:
                        print(f"  处理时间: {processing_data['processing_time']}")
                except Exception as e:
                    print(f"  解析processing_content失败: {e}")
            print()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    check_processing_time()