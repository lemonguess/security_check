from models.database import AuditStats, db

def clear_audit_stats():
    """清空审核统计表"""
    try:
        db.connect(reuse_if_open=True)
        
        # 删除所有统计记录
        deleted_count = AuditStats.delete().execute()
        print(f"已删除 {deleted_count} 条统计记录")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    clear_audit_stats()