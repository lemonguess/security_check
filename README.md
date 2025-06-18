# 安全内容检测平台

## 项目概述
本项目是一个整合网易云盾和阿里云盾的多媒体内容安全检测平台，专注于使用人工智能技术检测音频、图片和视频内容的合规性。系统可识别暴力、色情、敏感信息等违规内容，为应用提供安全可靠的内容过滤服务。

## 安装依赖

### 使用 uv 工具安装（推荐）
1. 确保已安装 `uv` 工具，如果未安装，可以通过以下命令安装：
   ```bash
   pip install uvloop
   ```
2. 使用 `uv` 工具安装项目依赖：
   ```bash
   uv pip install -r requirements.txt
   ```

### 使用 pip 安装
```
pip install -r requirements.txt
```

## 技术特点
- **双云平台集成**：
  - 支持网易云盾和阿里云盾双引擎
  - 通过`PLATFORM`配置切换检测平台
  - 统一API接口设计，简化调用流程
- **多媒体内容检测**：
  - 图片同步检测（即时返回结果）
  - 音频/视频异步检测（任务队列处理）
  - 支持HTTP回调通知机制
- **技术栈**：
  - **Web框架**：FastAPI提供RESTful接口
  - **数据库**：SQLite存储任务信息，使用Peewee ORM管理
  - **任务调度**：异步任务队列定期查询检测结果
  - **SDK集成**：官方Python SDK对接云平台
- **API接口**：
  - `POST /image/check` - 图片检测
  - `POST /audio/check` - 音频检测
  - `POST /video/check` - 视频检测

## 数据库设计
使用SQLite数据库存储检测任务信息，核心表结构：

### 任务表 (Task)
| 字段名       | 类型         | 说明                         |
|--------------|--------------|------------------------------|
| id           | UUID         | 任务唯一标识                 |
| type         | CharField    | 任务类型（image/audio/video）|
| status       | IntegerField | 任务状态（0:创建,1:成功,2:失败）|
| create_time  | DateTimeField| 任务创建时间                 |
| update_time  | DateTimeField| 任务更新时间                 |
| callback_url | CharField    | 回调地址（可选）             |
| content      | CharField    | 待检测内容的URL              |

### 枚举定义
- **任务类型 (TaskType)**:
  - IMAGE = "image"
  - AUDIO = "audio"
  - VIDEO = "video"
  
- **任务状态 (TaskStatus)**:
  - CREATED = 0 (任务已创建)
  - SUCCESS = 1 (检测成功)
  - FAILED = 2 (检测失败)

## 项目结构
```
