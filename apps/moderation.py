#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内容审核API路由 - 重写版本
支持并发审核content、images、audios、videos四个维度
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel, Field
from peewee import DoesNotExist
import uuid
from datetime import datetime, date
import io

from services.moderation_service import ModerationService
from models.models import ModerationRequest, BatchModerationRequest, ModerationResult
from models.database import Contents, AuditStats, db
from models.enums import ContentCategory, RiskLevel, AuditStatus, EngineType, ProcessingStatus
from utils.exceptions import ModerationError
from utils.logger import get_logger

# 全局任务状态存储
task_status_store = {}

async def process_audit_task(task_id: str, content_id: int, service, logger):
    """异步处理审核任务"""
    try:
        # 更新任务状态为处理中
        task_status_store[task_id] = {
            "status": "processing",
            "content_id": content_id,
            "message": "正在审核中...",
            "created_at": datetime.now().isoformat()
        }
        
        # 执行审核
        result = await service.moderate(content_id=content_id)
        
        # 更新任务状态为完成
        task_status_store[task_id] = {
            "status": "completed",
            "content_id": content_id,
            "result": result,
            "message": "审核完成",
            "created_at": task_status_store[task_id]["created_at"],
            "completed_at": datetime.now().isoformat()
        }
        
        logger.info(f"审核任务完成: {task_id}, content_id: {content_id}")
        
    except Exception as e:
        # 更新任务状态为失败
        task_status_store[task_id] = {
            "status": "failed",
            "content_id": content_id,
            "error": str(e),
            "message": f"审核失败: {str(e)}",
            "created_at": task_status_store.get(task_id, {}).get("created_at", datetime.now().isoformat()),
            "failed_at": datetime.now().isoformat()
        }
        
        # 更新数据库状态为待审核
        try:
            with db.atomic():
                content_obj = Contents.get_or_none(Contents.id == content_id)
                if content_obj:
                    content_obj.audit_status = AuditStatus.PENDING.value
                    content_obj.save()
        except Exception as db_error:
            logger.error(f"更新数据库状态失败: {db_error}")
        
        logger.error(f"审核任务失败: {task_id}, content_id: {content_id}, error: {str(e)}")

# 任务状态查询接口将在router定义后添加
from services.wangyiyunsdk import (
    check_text_service, check_images_service, check_audios_service, 
    check_videos_service, query_task
)
from services.agents import create_moderation_agent

service_logger = get_logger(__name__)

router = APIRouter(tags=["内容审核"])


def update_audit_stats(success: bool, processing_time: float = 0.0):
    """更新审核统计数据"""
    try:
        today = date.today()
        db.connect(reuse_if_open=True)
        
        # 获取或创建今日统计记录
        stats, created = AuditStats.get_or_create(
            date=today,
            defaults={
                'total_audits': 0,
                'successful_audits': 0,
                'failed_audits': 0,
                'total_processing_time': 0.0
            }
        )
        
        # 更新统计数据
        stats.total_audits += 1
        if success:
            stats.successful_audits += 1
        else:
            stats.failed_audits += 1
        stats.total_processing_time += processing_time
        stats.updated_at = datetime.now()
        stats.save()
        
    except Exception as e:
        service_logger.error(f"更新审核统计失败: {e}")
    finally:
        if not db.is_closed():
            db.close()


class ModerationRequestAPI(BaseModel):
    """API审核请求模型"""
    content: str = Field(..., description="待审核的内容", min_length=1, max_length=10000)
    content_id: Optional[str] = Field(None, description="内容唯一标识")
    content_type: str = Field("text", description="内容类型")
    priority: int = Field(0, description="优先级，数值越大优先级越高")
    timeout: Optional[float] = Field(30.0, description="超时时间（秒）")


class BatchModerationRequestAPI(BaseModel):
    """API批量审核请求模型"""
    contents: List[str] = Field(..., description="待审核的内容列表", min_length=1, max_length=100)
    content_ids: Optional[List[str]] = Field(None, description="内容标识列表")
    content_type: str = Field("text", description="内容类型")
    parallel: bool = Field(True, description="是否并行处理")
    timeout: Optional[float] = Field(60.0, description="超时时间（秒）")


class IDListModerationRequestAPI(BaseModel):
    """基于ID列表的审核请求模型"""
    id_list: List[int] = Field(..., description="内容ID列表", min_length=1, max_length=100)


class TextModerationRequestAPI(BaseModel):
    """文字审核请求模型"""
    content: str = Field(..., description="待审核的文本内容", min_length=1, max_length=10000)
    timeout: Optional[float] = Field(30.0, description="超时时间（秒）")


def moderate_content_by_type(content_type: str, content_data: Any) -> Dict[str, Any]:
    """根据内容类型进行审核，等待审核结果完成后返回"""
    import time
    from models.enums import TaskType
    
    try:
        # 提交审核任务
        if content_type == "text":
            result = check_text_service(content_data, "")
        elif content_type == "images":
            if isinstance(content_data, str):
                content_data = json.loads(content_data) if content_data else []
            result = check_images_service(content_data, "")
        elif content_type == "audios":
            if isinstance(content_data, str):
                content_data = json.loads(content_data) if content_data else []
            result = check_audios_service(content_data, "")
        elif content_type == "videos":
            if isinstance(content_data, str):
                content_data = json.loads(content_data) if content_data else []
            result = check_videos_service(content_data, "")
        else:
            return {"error": f"不支持的内容类型: {content_type}"}
        
        # 如果提交失败，直接返回错误
        if not isinstance(result, (dict, list)):
            return {"error": "提交审核任务失败"}
        
        # 处理不同类型的返回结果
        if content_type == "text":
            if not isinstance(result, dict):
                return {"error": "文本审核返回格式错误"}
            if "task_id" not in result or not result["task_id"]:
                return {"error": result.get("msg", "提交文本审核失败")}
            task_id = result["task_id"]
            task_type = TaskType.TEXT.value
        else:
            # 对于images/audios/videos，返回的是列表
            if not isinstance(result, list) or not result:
                return {"error": "提交审核任务失败"}
            # 取第一个任务的task_id
            first_task = result[0]
            if not isinstance(first_task, dict) or "task_id" not in first_task:
                return {"error": "获取任务ID失败"}
            task_id = first_task["task_id"]
            if content_type == "images":
                task_type = TaskType.IMAGE.value
            elif content_type == "audios":
                task_type = TaskType.AUDIO.value
            elif content_type == "videos":
                task_type = TaskType.VIDEO.value
            
            # 处理多个文件的情况
            final_results = []
            for item in result:
                if "task_id" not in item or not item["task_id"]:
                    final_results.append({
                        "file_path": item.get("file_path", "unknown"),
                        "error": item.get("msg", "提交审核失败"),
                        "is_compliant": False
                    })
                    continue
                
                item_task_id = item["task_id"]
                item_task_type = task_type  # 使用之前确定的task_type
                
                # 轮询查询审核结果
                max_attempts = 30  # 最多查询30次
                attempt = 0
                query_result = None
                
                while attempt < max_attempts:
                    try:
                        query_result = query_task(item_task_id, item_task_type)
                        if query_result is not None:  # 审核完成
                            break
                        time.sleep(2)  # 等待2秒后重试
                        attempt += 1
                    except Exception as e:
                        service_logger.error(f"查询任务{task_id}失败: {e}")
                        break
                
                if query_result is not None:
                    final_results.append({
                        "file_path": item.get("file_path", "unknown"),
                        "task_id": task_id,
                        "is_compliant": query_result.is_compliant,
                        "result_text": query_result.result_text,
                        "status": "completed"
                    })
                else:
                    final_results.append({
                        "file_path": item.get("file_path", "unknown"),
                        "task_id": task_id,
                        "error": "审核超时或失败",
                        "is_compliant": False,
                        "status": "timeout"
                    })
            
            return {"results": final_results}
        
        # 对于文本类型，轮询查询审核结果
        max_attempts = 30  # 最多查询30次
        attempt = 0
        query_result = None
        
        while attempt < max_attempts:
            try:
                query_result = query_task(task_id, task_type)
                if query_result is not None:  # 审核完成
                    break
                time.sleep(2)  # 等待2秒后重试
                attempt += 1
            except Exception as e:
                service_logger.error(f"查询任务{task_id}失败: {e}")
                break
        
        if query_result is not None:
            return {
                "task_id": task_id,
                "is_compliant": query_result.is_compliant,
                "result_text": query_result.result_text,
                "status": "completed"
            }
        else:
            return {
                "task_id": task_id,
                "error": "审核超时或失败",
                "is_compliant": False,
                "status": "timeout"
            }
            
    except Exception as e:
        service_logger.error(f"审核{content_type}失败: {e}")
        return {"error": str(e)}


async def query_moderation_result(task_id: str, task_type: str) -> Dict[str, Any]:
    """查询审核结果"""
    try:
        result = query_task(task_id, task_type)
        if result:
            return {
                "is_compliant": result.is_compliant,
                "result_text": result.result_text,
                "status": "completed"
            }
        else:
            return {"status": "pending"}
    except Exception as e:
        service_logger.error(f"查询任务{task_id}结果失败: {e}")
        return {"error": str(e), "status": "error"}


async def generate_audit_report(content_id: int, audit_results: Dict[str, Any]) -> str:
    """使用大模型生成HTML格式的审核报告"""
    import json
    import re
    try:
        # 获取内容信息
        content_obj = Contents.get_by_id(content_id)
        
        # 准备审核结果摘要
        summary_data = {
            "content_id": content_id,
            "title": content_obj.title,
            "audit_results": audit_results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 构建提示词
        prompt = f"""
请根据以下审核结果生成一份详细的HTML格式审核报告：

内容ID: {content_id}
标题: {content_obj.title if content_obj.title is not None else '无标题'}
审核时间: {summary_data['timestamp']}

审核结果详情:
{json.dumps(audit_results, ensure_ascii=False, indent=2)}

请生成一份专业的HTML格式审核报告，包含：
1. 报告标题和基本信息
2. 各维度审核结果汇总表格
3. 详细的审核分析
4. 最终合规性结论
5. 建议和备注

要求：
- 使用现代化的HTML和CSS样式
- 表格清晰易读
- 突出显示重要信息
- 包含适当的颜色标识（绿色表示合规，红色表示不合规）
"""
        
        # 这里应该调用大模型API生成报告
        # 暂时使用模板生成
        html_report = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>内容审核报告 - {content_id}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }}
        .title {{ color: #007bff; font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
        .info {{ color: #666; font-size: 14px; }}
        .section {{ margin-bottom: 25px; }}
        .section-title {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 15px; border-left: 4px solid #007bff; padding-left: 10px; }}
        .result-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        .result-table th, .result-table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        .result-table th {{ background-color: #f8f9fa; font-weight: bold; }}
        .content-preview {{ max-width: 200px; max-height: 100px; overflow: hidden; }}
        .content-preview img {{ max-width: 100%; max-height: 80px; object-fit: cover; border-radius: 4px; }}
        .content-preview .text-content {{ font-size: 12px; color: #666; line-height: 1.4; }}
        .content-preview .image-list {{ display: flex; flex-wrap: wrap; gap: 4px; }}
        .content-preview .image-item {{ width: 40px; height: 40px; border-radius: 4px; overflow: hidden; }}
        .compliant {{ color: #28a745; font-weight: bold; }}
        .non-compliant {{ color: #dc3545; font-weight: bold; }}
        .conclusion {{ background-color: #e9ecef; padding: 20px; border-radius: 5px; margin-top: 20px; }}
        .conclusion.safe {{ background-color: #d4edda; border-left: 4px solid #28a745; }}
        .conclusion.risky {{ background-color: #f8d7da; border-left: 4px solid #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">内容审核报告</div>
            <div class="info">
                <p><strong>内容ID:</strong> {content_id}</p>
                <p><strong>标题:</strong> {content_obj.title if content_obj.title is not None else '无标题'}</p>
                <p><strong>审核时间:</strong> {summary_data['timestamp']}</p>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">审核结果汇总</div>
            <table class="result-table">
                <thead>
                    <tr>
                        <th>审核维度</th>
                        <th>审核内容</th>
                        <th>审核状态</th>
                        <th>合规性</th>
                        <th>详细信息</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        # 生成不同维度的内容预览
        def generate_dimension_content(dimension, content_obj):
            if dimension == "images" and content_obj.images:
                # 图片维度：解析JSON格式的图片列表
                try:
                    images_list = json.loads(content_obj.images) if isinstance(content_obj.images, str) else content_obj.images
                    return images_list
                except (json.JSONDecodeError, TypeError):
                    return []
            elif dimension == "content":
                # 文本内容维度
                if content_obj.content:
                    text_preview = content_obj.content[:100] + '...' if len(content_obj.content) > 100 else content_obj.content
                    return f'<div class="text-content">{text_preview}</div>'
                elif content_obj.processing_html:
                    text_content = re.sub(r'<[^>]+>', '', content_obj.processing_html)
                    text_preview = text_content[:100] + '...' if len(text_content) > 100 else text_content
                    return f'<div class="text-content">{text_preview}</div>'
                else:
                    return '<div class="text-content">无文本内容</div>'
            else:
                # 其他维度显示维度名称
                return f'<div class="dimension-content">{dimension}</div>'
        
        # 添加各维度审核结果
        for dimension, result in audit_results.items():
            if dimension != "overall_compliant":
                status = "已完成" if result.get("status") == "completed" else "处理中"
                compliant = "合规" if result.get("is_compliant", False) else "不合规"
                compliant_class = "compliant" if result.get("is_compliant", False) else "non-compliant"
                # 确保detail不为None，避免字符串拼接错误
                detail = result.get("result_text") or "无详细信息"
                if detail is None:
                    detail = "无详细信息"
                
                # 特殊处理图片维度
                if dimension == "images" and content_obj.images:
                    # 解析JSON格式的图片列表
                    try:
                        images_list = json.loads(content_obj.images) if isinstance(content_obj.images, str) else content_obj.images
                        # 为每张图片生成单独的行
                        for i, img_url in enumerate(images_list):
                            img_preview = f'<div class="image-item"><img src="{img_url}" alt="图片{i+1}" style="max-width: 150px; max-height: 100px; object-fit: cover;"></div>'
                            html_report += f"""
                    <tr>
                        <td>{dimension}</td>
                        <td>{img_preview}</td>
                        <td>{status}</td>
                        <td class="{compliant_class}">{compliant}</td>
                        <td>{detail}</td>
                    </tr>
"""
                    except (json.JSONDecodeError, TypeError):
                        # 如果解析失败，显示错误信息
                        html_report += f"""
                    <tr>
                        <td>{dimension}</td>
                        <td>图片数据解析失败</td>
                        <td>{status}</td>
                        <td class="{compliant_class}">{compliant}</td>
                        <td>{detail}</td>
                    </tr>
"""
                else:
                    # 其他维度的正常处理
                    dimension_content = generate_dimension_content(dimension, content_obj)
                    html_report += f"""
                    <tr>
                        <td>{dimension}</td>
                        <td>{dimension_content}</td>
                        <td>{status}</td>
                        <td class="{compliant_class}">{compliant}</td>
                        <td>{detail}</td>
                    </tr>
"""
        
        # 添加结论
        overall_compliant = audit_results.get("overall_compliant", False)
        conclusion_class = "safe" if overall_compliant else "risky"
        conclusion_text = "内容整体合规，可以发布" if overall_compliant else "内容存在合规风险，建议进一步审查"
        
        html_report += f"""
                </tbody>
            </table>
        </div>
        
        <div class="conclusion {conclusion_class}">
            <h3>最终结论</h3>
            <p><strong>整体合规性:</strong> <span class="{'compliant' if overall_compliant else 'non-compliant'}">{"合规" if overall_compliant else "不合规"}</span></p>
            <p><strong>建议:</strong> {conclusion_text}</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html_report
        
    except Exception as e:
        service_logger.error(f"生成审核报告失败: {e}")
        return f"<html><body><h1>报告生成失败</h1><p>错误信息: {str(e)}</p></body></html>"


@router.post("/", summary="内容审核 - 支持ID列表并发审核")
async def moderate_content_by_ids(request: Request, body: dict, background_tasks: BackgroundTasks):
    """内容审核 - 支持单条、批量和ID列表审核"""
    try:
        service = request.app.state.service
        logger = request.app.state.logger
        logger.info(f"收到内容审核请求: {body}")

        id_list = []
        # 检查是否是ID列表审核
        if "id_list" in body:
            id_list = body["id_list"]
        # 检查是否是单条审核 (通过 content_id)
        elif "content_id" in body:
            id_list = [body["content_id"]]
        else:
            raise HTTPException(status_code=400, detail="请求参数错误, 需要 'id_list' 或 'content_id'")

        logger.info(f"准备审核内容, IDs: {id_list}")
        
        # 异步任务入队，立即返回任务ID和初始状态
        results = []
        for content_id in id_list:
            # 标记内容为 processing 状态
            db.connect(reuse_if_open=True)
            content_obj = Contents.get_or_none(Contents.id == int(content_id))
            if content_obj:
                content_obj.processing_status = "processing"
                content_obj.audit_status = AuditStatus.REVIEWING.value
                content_obj.save()
            # 使用BackgroundTasks启动后台任务
            background_tasks.add_task(process_single_content, int(content_id))
            results.append({
                "content_id": content_id,
                "status": "processing"
            })
        return {
            "success": True,
            "data": results,
            "message": "审核任务已提交，正在处理中，请稍后通过内容ID查询状态"
        }
            
    except Exception as e:
        service_logger.error(f"审核失败: {e}")
        raise HTTPException(status_code=500, detail=f"审核失败: {str(e)}")


async def process_single_content(content_id: int) -> Dict[str, Any]:
    """处理单个内容的审核"""
    import json
    import time
    start_time = time.time()
    try:
        # 连接数据库
        db.connect(reuse_if_open=True)
        
        # 查询内容
        content_obj = Contents.get_or_none(Contents.id == content_id)
        if not content_obj:
            return {
                "content_id": content_id,
                "error": "内容不存在",
                "final_decision": "ERROR",
                "is_compliant": False
            }
        
        # 并发审核四个维度
        audit_tasks = {}
        
        # 提交审核任务
        if content_obj.content:
            audit_tasks["content"] = moderate_content_by_type("text", content_obj.content)
        
        if content_obj.images:
            # 解析JSON格式的图片列表
            try:
                images_list = json.loads(content_obj.images) if isinstance(content_obj.images, str) else content_obj.images
                audit_tasks["images"] = moderate_content_by_type("images", images_list)
            except (json.JSONDecodeError, TypeError):
                service_logger.error(f"解析图片列表失败: {content_obj.images}")
                audit_tasks["images"] = {"error": "图片数据格式错误"}
        
        if content_obj.audios:
            audit_tasks["audios"] = moderate_content_by_type("audios", content_obj.audios)
        
        if content_obj.videos:
            audit_tasks["videos"] = moderate_content_by_type("videos", content_obj.videos)
        
        # 处理审核结果
        audit_results = {}
        all_compliant = True
        
        for dimension, task_result in audit_tasks.items():
            try:
                if "error" in task_result:
                    audit_results[dimension] = {
                        "status": "error",
                        "is_compliant": False,
                        "result_text": task_result["error"]
                    }
                    all_compliant = False
                elif dimension == "content":  # 文本类型
                    audit_results[dimension] = {
                        "status": task_result.get("status", "completed"),
                        "is_compliant": task_result.get("is_compliant", False),
                        "result_text": task_result.get("result_text", "未知结果")
                    }
                    if not task_result.get("is_compliant", False):
                        all_compliant = False
                else:  # 图片、音频、视频类型
                    if "results" in task_result:
                        # 处理多个文件的结果
                        dimension_compliant = True
                        result_texts = []
                        for item in task_result["results"]:
                            if not item.get("is_compliant", False):
                                dimension_compliant = False
                            # 确保所有字段都不为None，避免字符串拼接错误
                            file_path = item.get('file_path') or 'unknown'
                            result_text = item.get('result_text') or item.get('error') or '未知结果'
                            if result_text is None:
                                result_text = '未知结果'
                            result_texts.append(f"{file_path}: {result_text}")
                        
                        audit_results[dimension] = {
                            "status": "completed",
                            "is_compliant": dimension_compliant,
                            "result_text": "; ".join(result_texts)
                        }
                        if not dimension_compliant:
                            all_compliant = False
                    else:
                        audit_results[dimension] = {
                            "status": "error",
                            "is_compliant": False,
                            "result_text": "审核结果格式错误"
                        }
                        all_compliant = False
            except Exception as e:
                audit_results[dimension] = {
                    "status": "error",
                    "is_compliant": False,
                    "result_text": f"处理审核结果失败: {str(e)}"
                }
                all_compliant = False
        
        # 判断整体合规性
        overall_compliant = all_compliant and all(
            result.get("is_compliant", False) for result in audit_results.values()
        )
        audit_results["overall_compliant"] = overall_compliant
        
        # 生成HTML报告
        html_report = await generate_audit_report(content_id, audit_results)
        
        # 更新内容审核状态和保存结果到Contents表
        final_decision = "APPROVED" if overall_compliant else "REJECTED"
        content_obj.audit_status = AuditStatus.APPROVED.value if overall_compliant else AuditStatus.REJECTED.value
        content_obj.risk_level = "safe" if overall_compliant else "risky"
        content_obj.processing_status = "completed"
        content_obj.processing_content = json.dumps(audit_results, ensure_ascii=False)
        content_obj.processing_html = html_report
        content_obj.final_decision = final_decision
        content_obj.save()
        
        # 更新审核统计
        processing_time = time.time() - start_time
        update_audit_stats(success=overall_compliant, processing_time=processing_time)
        
        return {
            "content_id": content_id,
            "final_decision": "APPROVED" if overall_compliant else "REJECTED",
            "is_compliant": overall_compliant,
            "audit_results": audit_results,
            "report_html": html_report
        }
        
    except Exception as e:
        service_logger.error(f"处理内容{content_id}审核失败: {e}")
        return {
            "content_id": content_id,
            "error": str(e),
            "final_decision": "ERROR",
            "is_compliant": False
        }
    finally:
        if not db.is_closed():
            db.close()


@router.get("/content/{content_id}/audit", summary="获取内容审核报告")
async def get_content_audit_report(content_id: int):
    """根据内容ID获取详细的审核报告"""
    try:
        db.connect(reuse_if_open=True)
        content_obj = Contents.get_by_id(content_id)
        processing_content = json.loads(content_obj.processing_content) if content_obj.processing_content else {}
        return {
            "success": True,
            "data": {
                "id": content_obj.id,
                "content_id": content_obj.id,
                "status": content_obj.audit_status,
                "risk_level": content_obj.risk_level,
                "processing_status": content_obj.processing_status,
                "result": content_obj.processing_html,  # HTML格式的报告
                "audit_results": processing_content,
                "created_at": str(content_obj.created_at),
                "updated_at": str(content_obj.updated_at)
            }
        }
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="内容记录未找到")
    except Exception as e:
        service_logger.error(f"获取审核报告失败: {e}")
        raise HTTPException(status_code=500, detail="获取审核报告失败")
    finally:
        if not db.is_closed():
            db.close()


@router.get("/content/{content_id}/audit/download", summary="下载内容审核报告")
async def download_content_audit_report(content_id: int, format: str = "html"):
    """下载审核报告 - 支持HTML和PDF格式"""
    try:
        db.connect(reuse_if_open=True)
        content_obj = Contents.get_by_id(content_id)
        
        html_content = content_obj.processing_html or "<html><body><h1>暂无审核报告</h1></body></html>"
        
        if format.lower() == "pdf":
             try:
                 import weasyprint
                 from fastapi.responses import Response
                 
                 # 生成PDF
                 pdf_buffer = io.BytesIO()
                 weasyprint.HTML(string=html_content).write_pdf(pdf_buffer)
                 pdf_buffer.seek(0)
                 
                 return Response(
                     content=pdf_buffer.getvalue(),
                     media_type="application/pdf",
                     headers={
                         "Content-Disposition": f"attachment; filename=content_audit_report_{content_id}.pdf"
                     }
                 )
             except ImportError:
                 raise HTTPException(status_code=500, detail="PDF生成功能不可用，请联系管理员")
             except Exception as e:
                 service_logger.error(f"PDF生成失败: {e}")
                 raise HTTPException(status_code=500, detail="PDF生成失败")
        else:
            # 默认返回HTML格式
            from fastapi.responses import HTMLResponse
            return HTMLResponse(
                content=html_content,
                headers={
                    "Content-Disposition": f"attachment; filename=content_audit_report_{content_id}.html"
                }
            )
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="内容记录未找到")
    except Exception as e:
        service_logger.error(f"下载审核报告失败: {e}")
        raise HTTPException(status_code=500, detail="下载审核报告失败")
    finally:
        if not db.is_closed():
            db.close()


@router.post("/single", summary="单条内容审核")
async def moderate_single(request: Request, moderation_request: ModerationRequestAPI):
    """审核单条内容 - 异步处理"""
    import asyncio
    import uuid
    from models.enums import AuditStatus
    
    try:
        service = request.app.state.service
        logger = request.app.state.logger
        
        logger.info(f"收到单条审核请求: {moderation_request.content_id}")
        
        # 验证参数
        if not moderation_request.content_id:
            raise ValueError("content_id 不能为空")
        
        content_id = int(moderation_request.content_id)
        
        # 更新状态为审核中
        from models.database import Contents, db
        with db.atomic():
            content_obj = Contents.get_or_none(Contents.id == content_id)
            if not content_obj:
                raise ValueError(f"内容不存在: {content_id}")
            
            content_obj.audit_status = AuditStatus.REVIEWING.value
            content_obj.save()
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 异步执行审核任务
        asyncio.create_task(process_audit_task(task_id, content_id, service, logger))
        
        return {
             "task_id": task_id,
             "content_id": content_id,
             "status": "reviewing",
             "message": "审核任务已提交，正在处理中"
         }
    except Exception as e:
        service_logger.error(f"单条审核失败: {e}")
        raise HTTPException(status_code=500, detail=f"审核失败: {str(e)}")


@router.post("/batch", summary="批量内容审核")
async def moderate_batch(request: Request, batch_request: BatchModerationRequestAPI):
    """批量审核内容"""
    try:
        service = request.app.state.service
        logger = request.app.state.logger
        
        logger.info(f"收到批量审核请求: {len(batch_request.contents)} 条内容")
        
        # 执行批量审核
        result = await service.moderate_batch(
            contents=batch_request.contents,
            content_ids=batch_request.content_ids,
            parallel=batch_request.parallel,
            content_type=batch_request.content_type,
            timeout=batch_request.timeout
        )
        
        return {
            "success": True,
            "data": result,
            "message": "批量审核完成"
        }
        
    except Exception as e:
        service_logger.error(f"批量审核失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量审核失败: {str(e)}")


@router.get("/categories", summary="获取内容分类")
async def get_content_categories():
    """获取内容分类列表"""
    categories = []
    for category in ContentCategory:
        categories.append({
            "name": category.name,
            "value": category.value
        })
    
    return {
        "success": True,
        "categories": categories,
        "message": "分类列表获取成功"
    }


@router.get("/task/{task_id}", summary="查询审核任务状态")
async def get_task_status(task_id: str):
    """查询审核任务状态"""
    if task_id not in task_status_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task_status_store[task_id]


@router.get("/content/{content_id}/status", summary="查询内容审核状态")
async def get_content_status(content_id: int):
    """查询内容审核状态"""
    try:
        from models.database import Contents
        content_obj = Contents.get_or_none(Contents.id == content_id)
        
        if not content_obj:
            raise HTTPException(status_code=404, detail="内容不存在")
        
        # 处理updated_at字段的类型转换
        updated_at_str = None
        if content_obj.updated_at:
            if hasattr(content_obj.updated_at, 'isoformat'):
                updated_at_str = content_obj.updated_at.isoformat()
            else:
                updated_at_str = str(content_obj.updated_at)
        
        return {
            "content_id": content_id,
            "audit_status": content_obj.audit_status,
            "processing_status": content_obj.processing_status,
            "risk_level": content_obj.risk_level,
            "updated_at": updated_at_str
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/risk-levels", summary="获取风险等级")
async def get_risk_levels():
    """获取风险等级列表"""
    levels = []
    for level in RiskLevel:
        levels.append({
            "name": level.name,
            "value": level.value
        })
    
    return {
        "success": True,
        "risk_levels": levels,
        "message": "风险等级列表获取成功"
    }


@router.get("/stats", summary="获取审核统计数据")
async def get_audit_stats():
    """获取审核统计数据"""
    try:
        db.connect(reuse_if_open=True)
        today = date.today()
        
        # 获取总审核量（所有历史数据）
        total_audits = AuditStats.select(AuditStats.total_audits).scalar() or 0
        if total_audits == 0:
            # 如果统计表为空，从Contents表计算
            total_audits = Contents.select().where(
                (Contents.audit_status == AuditStatus.APPROVED.value) |
                (Contents.audit_status == AuditStatus.REJECTED.value)
            ).count()
        else:
            # 计算所有日期的总审核量
            total_audits = sum([stats.total_audits for stats in AuditStats.select()])
        
        # 获取成功审核量
        successful_audits = sum([stats.successful_audits for stats in AuditStats.select()]) or 0
        if successful_audits == 0:
            # 从Contents表计算
            successful_audits = Contents.select().where(
                Contents.audit_status == AuditStatus.APPROVED.value
            ).count()
        
        # 计算成功率
        success_rate = (successful_audits / total_audits * 100) if total_audits > 0 else 0.0
        
        # 计算平均处理时间
        total_processing_time = sum([stats.total_processing_time for stats in AuditStats.select()]) or 0.0
        avg_processing_time = (total_processing_time / total_audits) if total_audits > 0 else 0.0
        
        # 获取今日审核量
        today_stats = AuditStats.get_or_none(AuditStats.date == today)
        today_audits = today_stats.total_audits if today_stats else 0
        
        return {
            "success": True,
            "data": {
                "total_audits": total_audits,
                "success_rate": round(success_rate, 1),
                "avg_processing_time": round(avg_processing_time, 2),
                "today_audits": today_audits
            },
            "message": "统计数据获取成功"
        }
        
    except Exception as e:
        service_logger.error(f"获取审核统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计数据失败")
    finally:
        if not db.is_closed():
            db.close()


@router.post("/text", summary="文字审核")
async def moderate_text(request: Request, text_request: TextModerationRequestAPI):
    """直接文字审核接口 - 同步返回审核结果"""
    import time
    
    try:
        service = request.app.state.service
        logger = request.app.state.logger
        
        start_time = time.time()
        logger.info(f"收到文字审核请求，内容长度: {len(text_request.content)}")
        
        # 创建审核请求对象
        moderation_request = ModerationRequest(
            content=text_request.content,
            content_id=None,
            content_type="text",
            priority=0,
            timeout=text_request.timeout
        )
        
        # 直接调用审核服务进行文字审核
        result = await service.moderate_text_direct(moderation_request)
        
        processing_time = time.time() - start_time
        
        # 更新统计数据
        update_audit_stats(success=True, processing_time=processing_time)
        
        logger.info(f"文字审核完成，处理时间: {processing_time:.2f}s")
        
        return {
            "success": True,
            "data": {
                "original_content": result.original_content,
                "final_decision": result.final_decision,
                "final_score": result.final_score,
                "risk_reasons": result.fusion_result.risk_reasons if result.fusion_result else [],
                "violated_categories": result.categories_detected,
                "processing_time": result.processing_time,
                "engines_used": [engine.value if hasattr(engine, 'value') else str(engine) for engine in result.engines_used],
                "ai_result": {
                    "risk_level": result.ai_result.risk_level.value if result.ai_result else "UNKNOWN",
                    "risk_score": result.ai_result.risk_score if result.ai_result else 0.0,
                    "risk_reasons": result.ai_result.risk_reasons if result.ai_result else [],
                    "confidence_score": result.ai_result.confidence_score if result.ai_result else 0.0
                } if result.ai_result else None,
                "rule_result": {
                    "risk_level": result.rule_result.risk_level.value if result.rule_result else "UNKNOWN",
                    "risk_score": result.rule_result.risk_score if result.rule_result else 0.0,
                    "sensitive_matches": len(result.rule_result.sensitive_matches) if result.rule_result else 0,
                    "violated_categories": result.rule_result.violated_categories if result.rule_result else []
                } if result.rule_result else None
            },
            "message": "文字审核完成"
        }
        
    except Exception as e:
        processing_time = time.time() - start_time if 'start_time' in locals() else 0.0
        update_audit_stats(success=False, processing_time=processing_time)
        
        service_logger.error(f"文字审核失败: {e}")
        raise HTTPException(status_code=500, detail=f"文字审核失败: {str(e)}")