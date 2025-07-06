from models.database import Contents, AuditStats, db
from models.enums import AuditStatus

db.connect()

print('Contents表中已审核的数据:')
audited = Contents.select().where(
    (Contents.audit_status == AuditStatus.APPROVED.value) |
    (Contents.audit_status == AuditStatus.REJECTED.value)
)
print(f'总数: {audited.count()}')

print('\nContents表中各状态的数据:')
for status in [AuditStatus.PENDING, AuditStatus.APPROVED, AuditStatus.REJECTED, AuditStatus.REVIEWING]:
    count = Contents.select().where(Contents.audit_status == status.value).count()
    print(f'{status.value}: {count}')

print('\nAuditStats表数据:')
stats_count = AuditStats.select().count()
print(f'AuditStats表记录数: {stats_count}')

for stat in AuditStats.select():
    print(f'日期: {stat.date}, 总审核: {stat.total_audits}, 成功: {stat.successful_audits}, 失败: {stat.failed_audits}, 处理时间: {stat.total_processing_time}')

db.close()