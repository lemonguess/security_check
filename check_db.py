import sqlite3

db_path = '/Users/lixincheng/workspace/security_check/security_check.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看 contents 表的 audit_status 字段值分布
print('audit_status 字段值分布:')
cursor.execute("SELECT audit_status, COUNT(*) FROM contents GROUP BY audit_status;")
status_counts = cursor.fetchall()
for status, count in status_counts:
    print(f'  {status}: {count} 条')

print('\n前10条记录的 id, title, audit_status:')
cursor.execute("SELECT id, title, audit_status FROM contents LIMIT 10;")
rows = cursor.fetchall()
for row in rows:
    print(f'  ID: {row[0]}, Title: {row[1][:50]}..., Status: {row[2]}')

conn.close()