# AI内容审核系统

## 项目概述

基于AgentScope的智能内容审核平台，集成网易云盾和阿里云盾双引擎，提供多媒体内容安全检测服务。系统采用前后端分离架构，支持文本、图片、音频、视频等多种内容类型的智能审核，可识别暴力、色情、敏感信息等违规内容。

![image-20250706225951185](https://lemon-guess.oss-cn-hangzhou.aliyuncs.com/img/image-20250706225951185.png)

![image-20250706230028759](https://lemon-guess.oss-cn-hangzhou.aliyuncs.com/img/image-20250706230028759.png)

![image-20250706230232973](https://lemon-guess.oss-cn-hangzhou.aliyuncs.com/img/image-20250706230232973.png)

## 技术架构

### 后端技术栈

- **Web框架**: FastAPI (异步高性能)
- **数据库**: SQLite + Peewee ORM
- **AI框架**: AgentScope (智能代理)
- **内容检测**: 网易云盾 + 阿里云盾
- **任务调度**: 异步任务队列
- **服务端口**: 6188

### 前端技术栈

- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **开发端口**: 5173
- **UI组件**: 自定义组件库

## 核心功能

### 🔍 多媒体内容检测

- **文本审核**: 敏感词过滤、政治敏感内容检测
- **图片审核**: 色情、暴力、广告等违规图片识别
- **音频审核**: 语音内容合规性检测
- **视频审核**: 视频画面和音轨双重检测

### 🤖 智能审核引擎

- **规则引擎**: 基于敏感词库和正则表达式
- **AI代理**: AgentScope智能审核代理
- **融合引擎**: 多引擎结果融合决策
- **实时统计**: 审核量、成功率、处理时间统计

### 📊 数据爬取与监控

- **多源爬取**: 企业动态、行业资讯、媒体报道
- **实时监控**: 当前政治新闻监控
- **自动审核**: 爬取内容自动进入审核流程

### 📈 统计分析

- **审核统计**: 总审核量、成功率分析
- **性能监控**: 平均处理时间、今日审核量
- **历史数据**: 审核历史记录和趋势分析

## 项目结构

```
security_check/
├── apps/                    # 应用模块
│   ├── checks.py           # 检测接口
│   ├── content.py          # 内容管理
│   ├── moderation.py       # 审核逻辑
│   └── scraper.py          # 爬虫接口
├── engines/                 # 审核引擎
│   ├── base_engine.py      # 基础引擎
│   ├── fusion_engine.py    # 融合引擎
│   └── rule_engine.py      # 规则引擎
├── models/                  # 数据模型
│   ├── database.py         # 数据库模型
│   ├── enums.py           # 枚举定义
│   └── models.py          # 业务模型
├── services/               # 服务层
│   ├── agents/            # AI代理
│   ├── aliyunsdk/         # 阿里云SDK
│   ├── wangyiyunsdk/      # 网易云SDK
│   ├── spiders/           # 爬虫服务
│   └── moderation_service.py # 审核服务
├── utils/                  # 工具模块
│   ├── config.py          # 配置管理
│   ├── logger.py          # 日志工具
│   └── metrics.py         # 指标收集
├── vue-security-check/     # 前端项目
│   ├── src/
│   │   ├── components/    # Vue组件
│   │   ├── types/         # TypeScript类型
│   │   └── App.vue        # 主应用
│   ├── package.json       # 前端依赖
│   └── vite.config.ts     # Vite配置
├── static/                 # 静态文件
├── main.py                 # 应用入口
└── requirements.txt        # Python依赖
```

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- SQLite 3

### 后端部署

1. **克隆项目**

   ```bash
   git clone <repository-url>
   cd security_check
   ```

2. **安装Python依赖**

   ```bash
   # 推荐使用uv工具
   uv sync
   ```

3. **配置环境**

   ```bash
   # 复制配置文件
   cp config/conf.ini.example config/conf.ini
   # 编辑配置文件，填入API密钥等信息
   ```

4. **初始化数据库**

   ```bash
   python models/database.py
   ```

5. **启动后端服务**

   ```bash
   python main.py
   # 服务将在 http://localhost:6188 启动
   ```

### 前端部署

1. **进入前端目录**

   ```bash
   cd vue-security-check
   ```

2. **安装依赖**

   ```bash
   npm install
   # 或使用yarn
   yarn install
   ```

3. **启动开发服务器**

   ```bash
   npm run dev
   # 前端将在 http://localhost:5173 启动
   ```

4. **构建生产版本**

   ```bash
   npm run build
   ```

## API接口

### 内容检测接口

- `POST /api/v1/check/image` - 图片检测
- `POST /api/v1/check/audio` - 音频检测
- `POST /api/v1/check/video` - 视频检测
- `POST /api/v1/check/text` - 文本检测

### 审核管理接口

- `GET /api/v1/moderation/stats` - 审核统计
- `POST /api/v1/moderation/process` - 处理审核
- `GET /api/v1/moderation/history` - 审核历史

### 内容管理接口

- `GET /api/v1/content/list` - 内容列表
- `GET /api/v1/content/{id}` - 内容详情
- `PUT /api/v1/content/{id}/status` - 更新状态

### 爬虫接口

- `POST /api/v1/scrape/start` - 启动爬取
- `GET /api/v1/scrape/status` - 爬取状态

### 系统接口

- `GET /api/v1/health` - 健康检查
- `GET /api/v1/stats` - 系统统计

## 数据库设计

### 核心表结构

#### Contents表 - 内容信息

| 字段               | 类型     | 说明         |
| ------------------ | -------- | ------------ |
| id                 | UUID     | 内容唯一标识 |
| content_type       | VARCHAR  | 内容类型     |
| content_url        | TEXT     | 内容URL      |
| audit_status       | VARCHAR  | 审核状态     |
| processing_content | TEXT     | 处理结果     |
| created_at         | DATETIME | 创建时间     |
| updated_at         | DATETIME | 更新时间     |

#### AuditStats表 - 审核统计

| 字段                  | 类型    | 说明       |
| --------------------- | ------- | ---------- |
| id                    | INTEGER | 主键       |
| date                  | DATE    | 统计日期   |
| total_audits          | INTEGER | 总审核量   |
| successful_audits     | INTEGER | 成功审核量 |
| failed_audits         | INTEGER | 失败审核量 |
| total_processing_time | FLOAT   | 总处理时间 |

### 枚举定义

#### 审核状态 (AuditStatus)

- `PENDING` - 待审核
- `REVIEWING` - 审核中
- `APPROVED` - 审核通过
- `REJECTED` - 审核拒绝

#### 内容类型 (ContentType)

- `TEXT` - 文本
- `IMAGE` - 图片
- `AUDIO` - 音频
- `VIDEO` - 视频

## 配置说明

### 环境变量

```bash
# 数据库配置
DATABASE_URL=sqlite:///security_check.db

# API配置
API_HOST=0.0.0.0
API_PORT=6188

# 云平台配置
PLATFORM=wangyi  # wangyi | aliyun
WANGYI_SECRET_ID=your_secret_id
WANGYI_SECRET_KEY=your_secret_key
ALIYUN_ACCESS_KEY=your_access_key
ALIYUN_SECRET_KEY=your_secret_key
```

### 配置文件 (config/conf.ini)

```ini
[database]
url = sqlite:///security_check.db

[api]
host = 0.0.0.0
port = 6188

[wangyi]
secret_id = your_secret_id
secret_key = your_secret_key

[aliyun]
access_key = your_access_key
secret_key = your_secret_key
```

## 开发指南

### 添加新的检测引擎

1. 在 `engines/` 目录下创建新引擎类
2. 继承 `BaseEngine` 基类
3. 实现 `detect()` 方法
4. 在 `fusion_engine.py` 中注册新引擎

### 添加新的爬虫

1. 在 `services/spiders/` 目录下创建爬虫类
2. 继承 `Spider` 基类
3. 实现 `crawl()` 方法
4. 在爬虫服务中注册

### 前端组件开发

1. 在 `vue-security-check/src/components/` 下创建组件
2. 使用TypeScript编写类型安全的代码
3. 遵循Vue 3 Composition API规范

## 许可证

MIT License

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request