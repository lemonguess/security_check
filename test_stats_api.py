from models.database import Contents, AuditStats, db
from models.enums import AuditStatus
from datetime import date, datetime

def test_stats_logic():
    """测试统计接口逻辑"""
    try:
        db.connect(reuse_if_open=True)
        today = date.today()
        
        print(f"今天日期: {today}")
        
        # 获取总审核量（所有历史数据）
        total_audits_from_stats = AuditStats.select(AuditStats.total_audits).scalar() or 0
        print(f"从AuditStats表获取的第一条记录的total_audits: {total_audits_from_stats}")
        
        if total_audits_from_stats == 0:
            # 如果统计表为空，从Contents表计算
            total_audits = Contents.select().where(
                (Contents.audit_status == AuditStatus.APPROVED.value) |
                (Contents.audit_status == AuditStatus.REJECTED.value)
            ).count()
            print(f"从Contents表计算的总审核量: {total_audits}")
        else:
            # 计算所有日期的总审核量
            total_audits = sum([stats.total_audits for stats in AuditStats.select()])
            print(f"从AuditStats表计算的总审核量: {total_audits}")
        
        # 获取成功审核量
        successful_audits = sum([stats.successful_audits for stats in AuditStats.select()]) or 0
        if successful_audits == 0:
            # 从Contents表计算
            successful_audits = Contents.select().where(
                Contents.audit_status == AuditStatus.APPROVED.value
            ).count()
            print(f"从Contents表计算的成功审核量: {successful_audits}")
        else:
            print(f"从AuditStats表计算的成功审核量: {successful_audits}")
        
        # 计算成功率
        success_rate = (successful_audits / total_audits * 100) if total_audits > 0 else 0.0
        print(f"成功率: {success_rate:.1f}%")
        
        # 计算平均处理时间
        total_processing_time = sum([stats.total_processing_time for stats in AuditStats.select()]) or 0.0
        avg_processing_time = (total_processing_time / total_audits) if total_audits > 0 else 0.0
        print(f"总处理时间: {total_processing_time}, 平均处理时间: {avg_processing_time:.2f}s")
        
        # 获取今日审核量
        today_stats = AuditStats.get_or_none(AuditStats.date == today)
        today_audits = today_stats.total_audits if today_stats else 0
        print(f"今日审核量: {today_audits}")
        
        print("\n最终统计结果:")
        result = {
            "total_audits": total_audits,
            "success_rate": round(success_rate, 1),
            "avg_processing_time": round(avg_processing_time, 2),
            "today_audits": today_audits
        }
        print(result)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    test_stats_logic()