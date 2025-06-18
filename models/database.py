import os
import sys

from peewee import Model, CharField, DateTimeField, IntegerField, TextField, BooleanField, FloatField, AutoField
from peewee import SqliteDatabase
import datetime

from pydantic import BaseModel

from models.enums import TaskType, TaskStatus

# 数据库连接
db = SqliteDatabase('security_check.db')


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

#
# class ModerationRequest(Model):
#     id = AutoField(primary_key=True, auto_increment=True)
#     content = CharField(null=False, help_text="待审核的内容", min_length=1)
#     content_id = CharField(null=True, help_text="内容唯一标识")
#     content_type = CharField(default="text", help_text="内容类型")
#     metadata = TextField(null=True, help_text="附加元数据")
#     priority = IntegerField(default=0, help_text="优先级，数值越大优先级越高")
#     timeout = FloatField(default=30.0, help_text="超时时间（秒）")
#
#     class Meta:
#         database = db
#
#
# class SensitiveMatch(Model):
#     id = AutoField(primary_key=True, auto_increment=True)
#     word = CharField(null=False, help_text="匹配的词汇")
#     category = CharField(null=False, help_text="分类")
#     position = IntegerField(null=False, help_text="在文本中的位置")
#     context = CharField(default="", help_text="上下文")
#     pattern_name = CharField(null=True, help_text="规则名称")
#     help_text = CharField(null=True, help_text="规则描述")
#     confidence = FloatField(default=1.0, help_text="置信度")
#
#     class Meta:
#         database = db
#
#
# class DetectionMatch(Model):
#     id = AutoField(primary_key=True, auto_increment=True)
#     type = CharField(null=False, help_text="匹配类型")
#     value = CharField(null=False, help_text="匹配的值")
#     category = CharField(null=True, help_text="分类")
#     confidence = FloatField(null=False, help_text="置信度")
#     position = TextField(null=True, help_text="在文本中的位置")
#     context = CharField(null=True, help_text="上下文信息")
#
#     class Meta:
#         database = db
#
#
# class AIResult(Model):
#     id = AutoField(primary_key=True, auto_increment=True)
#     risk_level = CharField(null=False, help_text="风险等级")
#     violated_categories = TextField(null=False, help_text="违规分类")
#     risk_score = FloatField(default=0.0, help_text="风险分数")
#     risk_reasons = TextField(null=False, help_text="风险原因")
#     detailed_analysis = CharField(default="", help_text="详细分析")
#     confidence_score = FloatField(default=0.0, help_text="置信度")
#     suspicious_segments = TextField(null=False, help_text="可疑片段")
#     keywords_found = TextField(null=False, help_text="发现的关键词")
#     evasion_techniques = TextField(null=False, help_text="识别到的规避技术")
#     reasoning = CharField(default="", help_text="推理过程")
#     recommendations = TextField(null=False, help_text="处理建议")
#     model_name = CharField(null=True, help_text="使用的模型")
#     processing_time = FloatField(null=True, help_text="处理时间")
#
#     class Meta:
#         database = db
#
#
# class RuleResult(Model):
#     id = AutoField(primary_key=True, auto_increment=True)
#     risk_level = CharField(null=False, help_text="风险等级")
#     violated_categories = TextField(null=False, help_text="违规分类")
#     risk_score = FloatField(default=0.0, help_text="风险分数")
#     risk_reasons = TextField(null=False, help_text="风险原因")
#     confidence_score = FloatField(default=0.0, help_text="置信度")
#     sensitive_matches = TextField(null=False, help_text="敏感词匹配")
#     matches = TextField(null=False, help_text="匹配结果")
#     sensitive_words = TextField(null=False, help_text="敏感词")
#     triggered_rules = TextField(null=False, help_text="触发的规则")
#     processing_time = FloatField(null=True, help_text="处理时间")
#
#     class Meta:
#         database = db
#
#
# class FusionResult(Model):
#     id = AutoField(primary_key=True, auto_increment=True)
#     risk_level = CharField(null=False, help_text="最终风险等级")
#     violated_categories = TextField(null=False, help_text="违规分类")
#     risk_score = FloatField(default=0.0, help_text="最终风险分数")
#     risk_reasons = TextField(null=False, help_text="风险原因")
#     confidence_score = FloatField(default=0.0, help_text="置信度")
#     ai_result = TextField(null=True, help_text="AI结果")
#     rule_result = TextField(null=True, help_text="规则结果")
#     fusion_strategy = CharField(default="weighted", help_text="融合策略")
#     engines_used = TextField(null=False, help_text="使用的引擎")
#     detailed_analysis = CharField(default="", help_text="详细分析")
#     processing_time = FloatField(null=False, help_text="处理时间")
#
#     class Meta:
#         database = db
#
#
# class ModerationResult(Model):
#     id = AutoField(primary_key=True, auto_increment=True)
#     content_id = CharField(null=False, help_text="内容ID")
#     original_content = CharField(null=False, help_text="原始内容")
#     status = CharField(null=False, help_text="处理状态")
#     ai_result = TextField(null=True, help_text="AI检测结果")
#     rule_result = TextField(null=True, help_text="规则检测结果")
#     fusion_result = TextField(null=True, help_text="融合结果")
#     final_decision = CharField(null=False, help_text="最终决策")
#     final_score = FloatField(null=False, help_text="最终分数")
#     masked_content = CharField(null=True, help_text="脱敏后内容")
#     processing_time = FloatField(null=False, help_text="总处理时间")
#     timestamp = DateTimeField(default=datetime.datetime.now, help_text="处理时间戳")
#     engines_used = TextField(null=False, help_text="使用的引擎")
#     total_matches = IntegerField(default=0, help_text="总匹配数")
#     categories_detected = TextField(null=False, help_text="检测到的分类")
#
#     class Meta:
#         database = db
#
#
# class BatchModerationRequest(Model):
#     id = AutoField(primary_key=True, auto_increment=True)
#     contents = TextField(null=False, help_text="内容列表", min_length=1, max_length=100)
#     content_ids = TextField(null=True, help_text="内容ID列表")
#     metadata = TextField(null=True, help_text="附加元数据")
#     parallel = BooleanField(default=True, help_text="是否并行处理")
#
#     class Meta:
#         database = db
#
#
# class BatchModerationResult(Model):
#     id = AutoField(primary_key=True, auto_increment=True)
#     total_count = IntegerField(null=False, help_text="总数量")
#     success_count = IntegerField(null=False, help_text="成功数量")
#     failed_count = IntegerField(null=False, help_text="失败数量")
#     results = TextField(null=False, help_text="审核结果列表")
#     errors = TextField(null=False, help_text="错误信息")
#     processing_time = FloatField(null=False, help_text="总处理时间")
#     timestamp = DateTimeField(default=datetime.datetime.now, help_text="处理时间戳")
#
#     class Meta:
#         database = db
#
#
# class SystemMetrics(Model):
#     id = AutoField(primary_key=True, auto_increment=True)
#     total_requests = IntegerField(default=0, help_text="总请求数")
#     successful_requests = IntegerField(default=0, help_text="成功请求数")
#     failed_requests = IntegerField(default=0, help_text="失败请求数")
#     average_processing_time = FloatField(default=0.0, help_text="平均处理时间")
#     risk_level_distribution = TextField(null=False, help_text="风险等级分布")
#     category_distribution = TextField(null=False, help_text="分类分布")
#     engine_performance = TextField(null=False, help_text="引擎性能")
#     last_updated = DateTimeField(default=datetime.datetime.now, help_text="最后更新时间")
#
#     class Meta:
#         database = db

# 创建表
def create_tables():
    # 判断数据库文件是否存在
    if not os.path.exists('security_check.db'):
        with db:
            db.create_tables([Task])

if __name__ == "__main__":
    create_tables()