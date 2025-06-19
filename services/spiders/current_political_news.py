#!/usr/bin/env python3
"""
时政要闻爬虫
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.spiders.Spider import SpiderBase
from utils.logger import get_logger
from xpinyin import Pinyin

class NewsSpider(SpiderBase):
    """
    时政要闻爬虫
    """
    def __init__(self, name: str = "时政要闻爬虫", url: str = "http://sc.tobacco.gov.cn/province_api/system/sysArticle/active_list?typeCode=shizhengyaowen&pageNo=1&pageSize=500"):
        super().__init__(name)
        self.name = name
        self.logger = get_logger(self.name)
        self.url = url
    def crawl_list_page(self) -> list:
        """
        抽象方法：爬取列表页内容。
        :param url: 列表页的 URL
        :return: 返回包含列表项的数据结构（如字典或对象列表）
        """
        res = self.make_request(url=self.url)
        if res["status"] == "success":
            response = res["content"].json()
        else:
            self.logger.error(f"【{self.name}】请求列表页出错")
            return []
        return response["result"]["records"]
    def parse(self, items: list) -> list:
        """
        抽象方法：解析列表页内容。
        :param content: 列表页内容
        :return: 解析后的数据结构（如字典或对象列表）
        """
        meta_list = []
        for item in items:
            meta = {}
            meta['title'] = item.get("title", "")
            meta['types'] = item.get("typeCode_dictText", "")
            meta['url'] = f"""http://sc.tobacco.gov.cn/article/details/{item.get("id", "")}/?title=&subtitle={meta['types']}&typecode={Pinyin().get_pinyin(meta['types'], splitter='')}"""
            meta['content'] = item.get("content", "")
            meta["images"] , meta["audios"], meta["videos"] = self.html_parser(meta['content'])
            meta["publish_time"] = item.get("publishDate", "")
            meta_list.append(meta)
        return meta_list

    def run(self) -> None:
        """
        运行爬虫的主要流程。
        :param start_url: 起始 URL
        """
        try:
            self.logger.info(f"开始爬取")
            items = self.crawl_list_page()
            self.logger.info(f"成功爬取 {len(items)} 条数据")
            self.logger.info("开始解析数据")
            meta_list = self.parse(items)
            self.logger.info("成功解析数据")
            self.save_to_database(meta_list)
            self.logger.info("数据已成功保存到数据库")
        except Exception as e:
            self.logger.error(f"爬虫运行出错: {e}")
if __name__ == '__main__':
    NewsSpider().run()