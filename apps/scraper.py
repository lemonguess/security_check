"""网页抓取路由"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.logger import get_logger
import time

router = APIRouter(tags=["网页抓取"])
logger = get_logger("scraper")


class ScrapeRequest(BaseModel):
    """抓取请求模型"""
    column_type: str  # 栏目类型：时政要闻、行业热点、川烟动态、媒体报道
    page: int = 1
    page_size: int = 20


class ContentItem(BaseModel):
    """内容项模型"""
    id: int
    title: str
    content: Optional[str] = None
    url: str
    publish_time: Optional[str] = None
    column_type: str


class ScrapeResponse(BaseModel):
    """抓取响应模型"""
    success: bool
    # data: List[ContentItem]
    total_count: int
    processing_time: str
    success_count: int
    message: Optional[str] = None


@router.post("/", response_model=ScrapeResponse, summary="根据栏目类型抓取内容")
async def scrape_content(request: ScrapeRequest):
    """
    根据栏目类型抓取内容并从数据库查询
    
    支持的栏目类型：
    - 时政要闻
    - 行业热点
    - 川烟动态
    - 媒体报道
    """
    logger.info(f"开始抓取栏目类型: {request.column_type}")
    start_time = time.time()
    try:
        # 导入爬虫模块
        from services.spiders.current_political_news import NewsSpider
        from services.spiders.industry_focus import FocusSpider
        from services.spiders.company_dynamic import DynamicSpider
        from services.spiders.media_report import ReportSpider
        from models.database import Contents, db
        
        # 根据栏目类型选择对应的爬虫
        spider_map = {
            "时政要闻": NewsSpider,
            "行业热点": FocusSpider,
            "川烟动态": DynamicSpider,
            "媒体报道": ReportSpider,
            # "全部": ""
        }
        
        if request.column_type not in spider_map:
            raise HTTPException(status_code=400, detail=f"不支持的栏目类型: {request.column_type}")
        success_count, failed_count = 0, 0
        # 执行爬虫抓取（如果需要更新数据）
        spider_class = spider_map[request.column_type]
        spider = spider_class()
        try:
            # 执行爬虫抓取新数据
            success_count, failed_count = spider.run()
            logger.info(f"爬虫抓取到 {(success_count)} 条新数据")
        except Exception as e:
            logger.warning(f"爬虫执行失败，将从数据库查询现有数据: {e}")
        return ScrapeResponse(
            success=True,
            # data=content_items,
            total_count=success_count + failed_count,
            processing_time=f"{int(time.time() - start_time)}秒",
            success_count=success_count,
            message=f"成功抓取{request.column_type} {success_count} 条内容（共{success_count + failed_count}条）"
        )
    
    except Exception as e:
        logger.error(f"抓取内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"抓取失败: {str(e)}")


@router.get("/test-tobacco", summary="测试爬虫连接")
async def test_spider_connection():
    """测试爬虫连接"""
    try:
        from services.spiders.current_political_news import NewsSpider
        from models.database import Contents
        
        # 测试爬虫
        spider = NewsSpider()
        items = spider.crawl_list_page()
        
        # 测试数据库查询
        count = Contents.select().where(Contents.column_type == "时政要闻").count()
        
        return {
            "success": True,
            "message": "爬虫和数据库连接正常",
            "spider_items": len(items) if items else 0,
            "db_count": count
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"测试失败: {str(e)}"
        }