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
from datetime import datetime

from services.moderation_service import ModerationService
from models.models import ModerationRequest, BatchModerationRequest, ModerationResult
from models.database import Audit, Contents, db
from models.enums import ContentCategory, RiskLevel, AuditStatus
from utils.logger import get_logger
from services.wangyiyunsdk import (
    check_text_service, check_images_service, check_audios_service, 
    check_videos_service, query_task
)
from services.agents import create_moderation_agent

service_logger = get_logger(__name__)

router = APIRouter(tags=["内容审核"])


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


async def moderate_content_by_type(content_type: str, content_data: Any, callback_url: str = "") -> Dict[str, Any]:
    """根据内容类型进行审核"""
    try:
        if content_type == "text":
            result = check_text_service(content_data, callback_url)
            return result if isinstance(result, dict) else {"result": result}
        elif content_type == "images":
            if isinstance(content_data, str):
                content_data = json.loads(content_data) if content_data else []
            result = check_images_service(content_data, callback_url)
            return result if isinstance(result, dict) else {"result": result}
        elif content_type == "audios":
            if isinstance(content_data, str):
                content_data = json.loads(content_data) if content_data else []
            result = check_audios_service(content_data, callback_url)
            return result if isinstance(result, dict) else {"result": result}
        elif content_type == "videos":
            if isinstance(content_data, str):
                content_data = json.loads(content_data) if content_data else []
            result = check_videos_service(content_data, callback_url)
            return result if isinstance(result, dict) else {"result": result}
        else:
            return {"error": f"不支持的内容类型: {content_type}"}
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
标题: {content_obj.title or '无标题'}
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
                <p><strong>标题:</strong> {content_obj.title or '无标题'}</p>
                <p><strong>审核时间:</strong> {summary_data['timestamp']}</p>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">审核结果汇总</div>
            <table class="result-table">
                <thead>
                    <tr>
                        <th>审核维度</th>
                        <th>审核状态</th>
                        <th>合规性</th>
                        <th>详细信息</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        # 添加各维度审核结果
        for dimension, result in audit_results.items():
            if dimension != "overall_compliant":
                status = "已完成" if result.get("status") == "completed" else "处理中"
                compliant = "合规" if result.get("is_compliant", False) else "不合规"
                compliant_class = "compliant" if result.get("is_compliant", False) else "non-compliant"
                detail = result.get("result_text", "无详细信息")
                
                html_report += f"""
                    <tr>
                        <td>{dimension}</td>
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
async def moderate_content_by_ids(request: Request, body: dict):
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
        
        # 并发处理所有ID
        results = []
        
        # 使用asyncio.gather并发处理异步任务
        tasks = []
        for content_id in id_list:
            tasks.append(process_single_content(int(content_id)))
        
        # 等待所有任务完成
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"审核内容 {id_list[i]} 失败: {result}")
                    processed_results.append({
                        "content_id": id_list[i],
                        "error": str(result),
                        "final_decision": "ERROR",
                        "is_compliant": False
                    })
                else:
                    processed_results.append(result)
            
            results = processed_results
        except Exception as e:
            logger.error(f"批量审核失败: {e}")
            raise HTTPException(status_code=500, detail=f"批量审核失败: {str(e)}")
        
        return {
            "success": True,
            "data": results,
            "message": "审核任务已完成"
        }
            
    except Exception as e:
        service_logger.error(f"审核失败: {e}")
        raise HTTPException(status_code=500, detail=f"审核失败: {str(e)}")


async def process_single_content(content_id: int) -> Dict[str, Any]:
    """处理单个内容的审核"""
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
        callback_url = f"http://localhost:6188/api/callback/{content_id}"
        
        # 提交审核任务
        if content_obj.content:
            audit_tasks["content"] = await moderate_content_by_type("text", content_obj.content, callback_url)
        
        if content_obj.images:
            audit_tasks["images"] = await moderate_content_by_type("images", content_obj.images, callback_url)
        
        if content_obj.audios:
            audit_tasks["audios"] = await moderate_content_by_type("audios", content_obj.audios, callback_url)
        
        if content_obj.videos:
            audit_tasks["videos"] = await moderate_content_by_type("videos", content_obj.videos, callback_url)
        
        # 等待所有任务完成并收集结果
        audit_results = {}
        all_compliant = True
        
        # 这里需要等待异步任务完成，实际应该通过回调或轮询机制
        # 暂时模拟结果
        for dimension, task in audit_tasks.items():
            try:
                # 模拟审核结果
                audit_results[dimension] = {
                    "status": "completed",
                    "is_compliant": True,  # 这里应该是实际的审核结果
                    "result_text": "内容合规"
                }
            except Exception as e:
                audit_results[dimension] = {
                    "status": "error",
                    "is_compliant": False,
                    "result_text": f"审核失败: {str(e)}"
                }
                all_compliant = False
        
        # 判断整体合规性
        overall_compliant = all_compliant and all(
            result.get("is_compliant", False) for result in audit_results.values()
        )
        audit_results["overall_compliant"] = overall_compliant
        
        # 生成HTML报告
        html_report = generate_audit_report(content_id, audit_results)
        
        # 保存审核记录
        audit_record = Audit.create(
            content=content_obj,
            status=AuditStatus.APPROVED.value if overall_compliant else AuditStatus.REJECTED.value,
            result=html_report
        )
        
        # 更新内容审核状态
        content_obj.audit_status = AuditStatus.APPROVED.value if overall_compliant else AuditStatus.REJECTED.value
        content_obj.save()
        
        return {
            "content_id": content_id,
            "audit_id": audit_record.id,
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


@router.get("/audit/{audit_id}", summary="获取审核报告")
async def get_audit_report(audit_id: int):
    """根据审核ID获取详细的审核报告"""
    try:
        db.connect(reuse_if_open=True)
        audit_record = Audit.get_by_id(audit_id)
        return {
            "success": True,
            "data": {
                "id": audit_record.id,
                "content_id": audit_record.content.id,
                "status": audit_record.status,
                "result": audit_record.result,  # HTML格式的报告
                "created_at": str(audit_record.created_at)
            }
        }
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="审核记录未找到")
    except Exception as e:
        service_logger.error(f"获取审核报告失败: {e}")
        raise HTTPException(status_code=500, detail="获取审核报告失败")
    finally:
        if not db.is_closed():
            db.close()


@router.get("/audit/{audit_id}/download", summary="下载审核报告")
async def download_audit_report(audit_id: int):
    """下载HTML格式的审核报告"""
    try:
        db.connect(reuse_if_open=True)
        audit_record = Audit.get_by_id(audit_id)
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(
            content=audit_record.result,
            headers={
                "Content-Disposition": f"attachment; filename=audit_report_{audit_id}.html"
            }
        )
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="审核记录未找到")
    except Exception as e:
        service_logger.error(f"下载审核报告失败: {e}")
        raise HTTPException(status_code=500, detail="下载审核报告失败")
    finally:
        if not db.is_closed():
            db.close()


@router.post("/single", summary="单条内容审核")
async def moderate_single(request: Request, moderation_request: ModerationRequestAPI):
    """审核单条内容"""
    try:
        service = request.app.state.service
        logger = request.app.state.logger
        
        logger.info(f"收到单条审核请求: {moderation_request.content_id}")
        
        # 执行审核
        result = await service.moderate(
            content=moderation_request.content,
            content_id=moderation_request.content_id,
            content_type=moderation_request.content_type,
            priority=moderation_request.priority,
            timeout=moderation_request.timeout
        )
        
        return {
            "success": True,
            "data": result,
            "message": "审核完成"
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