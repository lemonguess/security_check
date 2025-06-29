from abc import ABC, abstractmethod
from utils.logger import get_logger
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from models.database import Contents, db
from models.enums import ColumnType
import json
import re
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent
ua = UserAgent()
class SpiderBase(ABC):
    """
    基类 Spider，定义了爬虫的基本功能框架。
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(self.name)
        self.url = ""
        self.headers = {'User-Agent': ua.random}

    @abstractmethod
    def parse(self, items:list) -> list:
        """
        解析响应内容，提取所需信息。
        :param response: 包含状态码和响应内容的字典
        :return: 解析后的结果列表
        """
        # 返回一个空字典作为默认值，避免返回None
        ...
    @abstractmethod
    def crawl_list_page(self) -> list:
        """
        抽象方法：爬取列表页内容。
        :param url: 列表页的 URL
        :return: 返回包含列表项的数据结构（如字典或对象列表）
        """
        pass

    def html_parser(self, html_content):
        """
        解析HTML内容，提取图片、音频、视频链接
        :param html_content: HTML内容字符串或BeautifulSoup对象
        :return: (images_list, audios_list, videos_list) 三个列表
        """
        if not html_content:
            return [], [], []
        
        # 如果是BeautifulSoup对象，转换为字符串
        if hasattr(html_content, 'text'):
            html_str = str(html_content)
        else:
            html_str = str(html_content)
        
        images = []
        audios = []
        videos = []
        
        try:
            # 提取图片链接 - img标签的src属性
            img_pattern = r'<img[^>]+src=["\']([^"\'>]+)["\'][^>]*>'
            img_matches = re.findall(img_pattern, html_str, re.IGNORECASE)
            images.extend(img_matches)
            
            # 提取音频链接 - audio标签的src属性
            audio_pattern = r'<audio[^>]+src=["\']([^"\'>]+)["\'][^>]*>'
            audio_matches = re.findall(audio_pattern, html_str, re.IGNORECASE)
            audios.extend(audio_matches)
            
            # 提取音频链接 - source标签在audio内的src属性
            audio_source_pattern = r'<audio[^>]*>.*?<source[^>]+src=["\']([^"\'>]+)["\'][^>]*>.*?</audio>'
            audio_source_matches = re.findall(audio_source_pattern, html_str, re.IGNORECASE | re.DOTALL)
            audios.extend(audio_source_matches)
            
            # 提取视频链接 - video标签的src属性
            video_pattern = r'<video[^>]+src=["\']([^"\'>]+)["\'][^>]*>'
            video_matches = re.findall(video_pattern, html_str, re.IGNORECASE)
            videos.extend(video_matches)
            
            # 提取视频链接 - source标签在video内的src属性
            video_source_pattern = r'<video[^>]*>.*?<source[^>]+src=["\']([^"\'>]+)["\'][^>]*>.*?</video>'
            video_source_matches = re.findall(video_source_pattern, html_str, re.IGNORECASE | re.DOTALL)
            videos.extend(video_source_matches)
            
            # 根据文件扩展名进一步分类链接
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
            audio_extensions = {'.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a'}
            video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}
            
            # 从所有链接中根据扩展名分类
            all_links_pattern = r'(?:src|href)=["\']([^"\'>]+)["\']'
            all_links = re.findall(all_links_pattern, html_str, re.IGNORECASE)
            
            for link in all_links:
                try:
                    parsed_url = urlparse(link.lower())
                    path = parsed_url.path
                    
                    # 检查文件扩展名
                    for ext in image_extensions:
                        if path.endswith(ext) and link not in images:
                            images.append(link)
                            break
                    
                    for ext in audio_extensions:
                        if path.endswith(ext) and link not in audios:
                            audios.append(link)
                            break
                    
                    for ext in video_extensions:
                        if path.endswith(ext) and link not in videos:
                            videos.append(link)
                            break
                            
                except Exception:
                    continue
            
            # 去重并过滤有效链接
            images = list(set([img for img in images if img and img.strip()]))
            audios = list(set([audio for audio in audios if audio and audio.strip()]))
            videos = list(set([video for video in videos if video and video.strip()]))
            
            self.logger.info(f"解析HTML完成: 图片 {len(images)} 个, 音频 {len(audios)} 个, 视频 {len(videos)} 个")
            
        except Exception as e:
            self.logger.error(f"解析HTML内容时出错: {e}")
            
        return images, audios, videos

    def make_request(self, url: str, retries: int = 3) -> dict:
        """
        发送带有重试机制的HTTP请求，并返回响应内容。
        :param url: 请求的目标URL
        :param retries: 最大重试次数，默认为3次
        :return: 包含状态码和响应内容的字典
        """
        for attempt in range(1, retries + 1):
            try:
                response = requests.get(url, timeout=10, headers=self.headers, verify=False)
                if response.status_code == 200:
                    return {"status": "success", "content": response}
                else:
                    self.logger.warning(f"Request failed with status code {response.status_code} on attempt {attempt}")
            except Timeout:
                self.logger.error(f"Timeout occurred while making request to {url} on attempt {attempt}")
            except ConnectionError:
                self.logger.error(f"Connection error occurred while making request to {url} on attempt {attempt}")
            except RequestException as e:
                self.logger.error(f"An unexpected error occurred: {e} on attempt {attempt}")

            if attempt < retries:
                self.logger.info(f"Retrying... Attempt {attempt + 1}/{retries}")

        return {"status": "failure", "message": "Max retries exceeded"}


    def clean_html_content(self, html_content: str) -> str:
        """
        清理HTML内容，去除HTML标签和超链接，提取纯文本
        :param html_content: 原始HTML内容
        :return: 清理后的纯文本内容
        """
        if not html_content:
            return ''
        
        try:
            # 去除HTML标签
            clean_text = re.sub(r'<[^>]+>', '', html_content)
            
            # 去除多余的空白字符
            clean_text = re.sub(r'\s+', ' ', clean_text)
            
            # 去除首尾空白
            clean_text = clean_text.strip()
            
            # 解码HTML实体
            import html
            clean_text = html.unescape(clean_text)
            
            return clean_text
        except Exception as e:
            self.logger.error(f"清理HTML内容时出错: {e}")
            return html_content

    def save_to_database(self, data: list) -> tuple:
        """
        将爬取的数据保存到数据库。
        :param data: 爬取的数据列表，每个元素应包含content、types、images、audios、videos等字段
        """
        if not data:
            self.logger.warning("没有数据需要保存")
            return 0, 0
        
        success_count = 0
        failed_count = 0
        
        for item in data:
            try:
                # 处理数据字段
                title = item.get('title', '')
                url = item.get('url', '')
                html_content = item.get('content', '')  # 原始HTML内容
                
                # 栏目类型映射：将中文名称映射到枚举值
                type_mapping = {
                    '时政要闻': ColumnType.CurrentPoliticalNews.value,
                    '行业热点': ColumnType.IndustryFocus.value,
                    '川烟动态': ColumnType.CompanyDynamic.value,
                    '媒体报道': ColumnType.MediaReport.value
                }
                raw_type = item.get('types', '')
                content_type = type_mapping.get(raw_type, ColumnType.CurrentPoliticalNews.value)
                
                publish_time = item.get('publish_time', '')
                images = item.get('images', [])
                audios = item.get('audios', [])
                videos = item.get('videos', [])
                
                # 清理HTML内容，提取纯文本
                clean_content = self.clean_html_content(html_content)
                
                # 将列表转换为JSON字符串存储
                import json
                images_json = json.dumps(images) if images else None
                audios_json = json.dumps(audios) if audios else None
                videos_json = json.dumps(videos) if videos else None
                
                # 创建Contents实例并保存
                content_model = Contents.create(
                    title=title,
                    url=url,
                    html=html_content,  # 存储原始HTML内容
                    content=clean_content,  # 存储清理后的纯文本内容
                    column_type=content_type,
                    audit_status='pending',  # 默认为待审核状态
                    publish_time=publish_time,
                    images=images_json,
                    audios=audios_json,
                    videos=videos_json
                )
                
                success_count += 1
                self.logger.info(f"成功保存数据，ID: {content_model.id}, title: {title}")
                
            except Exception as e:
                failed_count += 1
                self.logger.error(f"保存单条数据失败: {e}, title: {item.get('title', 'N/A')}, url: {item.get('url', 'N/A')}")
                # 继续处理下一条数据，不中断整个流程
                continue
                
        self.logger.info(f"批量保存完成，成功: {success_count} 条，失败: {failed_count} 条，总计: {len(data)} 条数据")
        return success_count, failed_count

    @abstractmethod
    def run(self) -> tuple:
        """
        运行爬虫的主要流程。
        :param start_url: 起始 URL
        """
        # try:
        #     self.logger.info(f"开始爬取 {start_url}")
        #     items = self.crawl_list_page(start_url)
        #     self.logger.info(f"成功爬取 {len(items)} 条数据")
        #     self.save_to_database(items)
        #     self.logger.info("数据已成功保存到数据库")
        # except Exception as e:
        #     self.logger.error(f"爬虫运行出错: {e}")
        pass