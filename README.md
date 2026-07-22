# TalentMatch Engine — 岗位技能图谱与人才匹配引擎

[![CI](https://github.com/Crzblinder/talentmatch-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/Crzblinder/talentmatch-engine/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 面向 2026 届及以后求职者的智能化求职助手：从"海投简历"到"精准匹配"，让每一次投递都有据可依。

TalentMatch Engine 是一个基于 **LangGraph Multi-Agent 编排**的岗位技能图谱与人才匹配引擎。它针对当前毕业生和职场新人面临的真实痛点——网申系统重复填写、简历被 AI 初筛过滤、海投低效、岗位需求与个人技能难以对齐——提供了一套可解释、可量化的匹配方案。

---

## 核心能力

### 五大智能 Agent

| Agent | 说明 |
|-------|------|
| JD 解析 Agent | 从原始 JD 中提取岗位名称、公司、核心技能、经验、学历与隐含需求 |
| 人才匹配 Agent | 基于技能覆盖度、缺失技能与可迁移技能计算加权匹配分数 |
| 趋势预测 Agent | 聚合岗位数据，输出热门技能、主流薪资与岗位趋势 |
| 学习路径规划 Agent | 根据缺失技能与技能图谱依赖关系生成可执行的学习路径 |
| 技能顾问 Agent | 输出简历优化、技能补强与求职策略建议 |

### 关键业务功能

| 功能模块 | 说明 |
|----------|------|
| 简历上传解析 | 支持 PDF/DOCX 上传，自动提取结构化信息（基本信息、教育经历、工作/项目经历、技能、证书、语言能力等） |
| 自动模糊解析 | 根据简历/JD 内容自动判定是否启用应届生友好模式，无需手动切换 |
| JD 上传解析 | 支持 PDF/DOCX/图片上传，图片通过多模态模型 OCR 识别后解析 |
| JD 模糊识别 | 自动识别应届生友好度、隐性门槛、技能别名等 |
| 简历优化 | 根据目标 JD 动态修改项目经历、实习经历、个人优势，支持字段排放顺序配置 |
| 人岗匹配 | 多维度加权匹配（技能覆盖度、经验匹配、学历匹配、可迁移技能） |
| 岗位智能推荐 | 基于用户画像遍历岗位库，按匹配分数降序推荐 |
| 岗位收藏 | 支持收藏/取消收藏感兴趣的岗位，分页浏览收藏列表 |
| 岗位对比 | 支持多岗位并排对比，直观查看技能需求差异 |
| 匹配结果导出 | 支持将匹配分析结果导出为 PDF |
| 联网智能搜索 | 支持公司、面经、薪资、校招、技能趋势等多种意图的联网搜索与 LLM 摘要 |
| 求职困境分析 | 针对应届毕业生识别经验不足、技能缺口、学历门槛等结构性障碍并给出应对建议 |
| 技能图谱 | 技能依赖、相似、共现关系可视化，支撑可迁移技能与学习路径 |
| 技能归一化 | 自动将别名映射到标准技能名称，统一匹配口径 |
| 趋势分析 | 热门技能、主流薪资、热门岗位、行业分布等市场趋势 |
| 仪表盘 | 岗位总数、公司总数、平均薪资、热门城市/行业/技能、经验分布等聚合数据 |
| SSE 流式输出 | LangGraph 每个节点完成时通过 Server-Sent Events 实时推送进度到前端 |

### 爬虫与岗位数据

| 能力 | 说明 |
|------|------|
| 公开 RSS 采集 | 自动采集 V2EX、Ruby China、LearnKu 等社区公开 RSS 中的技术岗位 |
| 种子数据兜底 | 80 条人工整理的行业典型岗位，确保离线环境也有真实样本 |
| 智能过滤 | 通用社区 RSS 自动过滤非招聘内容（面经、广告、讨论等） |
| 结构化提取 | 自动提取岗位名称、公司名、城市、薪资、经验、学历、技能关键词 |
| 手动触发 | `POST /api/v1/crawler/trigger` 立即执行采集 |
| 定时任务 | 支持 `SCHEDULER_ENABLED` 配置定时自动采集（默认 6 小时间隔） |
| 数据源扩展 | 支持添加新的公开 RSS 源或接入第三方招聘 API |

---

## 真实痛点与解决方案

| 痛点 | 解决方案 |
|------|----------|
| 应届生求职竞争激烈，简历难以脱颖而出 | 简历优化建议 + 岗位关键词对齐 + 自动模糊解析 |
| 网申系统重复填写，海投效率低 | 统一的技能画像，一次填写多次匹配 |
| 企业使用 AI 初筛简历，关键词不匹配即被过滤 | JD 解析 + 匹配结果直观展示岗位需求与个人技能差距 |
| 不知道岗位需要哪些技能，学习方向模糊 | 学习路径规划基于技能图谱生成 |
| 投递后无反馈，难以评估自身竞争力 | 量化匹配分数与可迁移技能，明确提升方向 |
| 应届生经历不足，难以包装简历 | 模糊解析模式自动识别项目经历、课程设计、实习为有效经历 |
| 不清楚市场行情和薪资水平 | 趋势分析提供热门技能、薪资范围、行业分布等市场数据 |

---

## 技术栈

- **后端**：Python 3.11、FastAPI、SQLAlchemy、Pydantic
- **智能体**：LangGraph + LangChain — 有状态图编排、SSE 流式输出，支持 OpenAI-compatible LLM + 本地 Ollama 双模式 + 确定性降级
- **RAG**：ChromaDB + `BAAI/bge-small-zh-v1.5` 中文 Embedding（可选）
- **数据库**：MySQL 8（默认 Docker）/ SQLite（本地快速启动）
- **前端**：React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui + Recharts + D3.js
- **部署**：Docker Compose 一键启动（云端 API / 本地 Ollama 双轨制）
- **测试**：pytest + Playwright

---

## 快速开始

> 系统支持两种大模型运行模式，请根据你的环境选择：

### 推荐：跨平台智能启动脚本（本地快速体验）

该脚本会自动识别操作系统、Python/Node 环境、网络环境（中国大陆/海外/内网），并针对性配置镜像源、数据库、端口等：

```bash
# 检测环境（不启动服务）
python scripts/start.py --dry-run

# 一键启动前后端（自动创建 venv、安装依赖、初始化数据库、注入种子数据）
python scripts/start.py

# 仅启动后端
python scripts/start.py --backend-only

# 端口被占用时自动结束占用进程
python scripts/start.py --kill-port

# 跳过依赖安装和种子数据，快速重启
python scripts/start.py --skip-deps --no-seed
```

脚本特性：
- 自动检测中国大陆网络并设置 `HF_ENDPOINT=https://hf-mirror.com`
- 自动选择 SQLite 作为本地数据库
- 自动检测端口占用并寻找备用端口（或 `--kill-port` 强制释放）
- 未配置 `OPENAI_API_KEY` 时自动启用规则引擎降级模式

### Windows 一键启动（推荐已安装环境后使用）

首次完成 `python scripts/start.py` 安装后，后续可直接双击项目根目录的 `launch.bat`：

```bash
launch.bat
```

它会自动：
- 跳过依赖安装，快速启动后端 + 前端
- 服务就绪后自动打开浏览器访问 `http://127.0.0.1:5173/`
- 首次运行时询问是否在桌面创建快捷方式，之后双击桌面图标即可启动

等价命令：

```bash
python scripts/start.py --open-browser --skip-deps --no-seed
```

### 路线 A：云端 API 模式（有 API Key）

适用场景：有 OpenAI 或兼容 API Key，追求更高推理质量。

```bash
# 1. 复制环境变量并填入 API Key
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY（留空则自动使用确定性降级，仍可运行）

# 2. 一键启动
docker compose up --build -d

# 3. 初始化数据（首次运行）
docker exec talentmatch_backend python scripts/init_db.py
docker exec talentmatch_backend python scripts/seed_data.py

# 4. 访问
# 前端：http://localhost:5173
# API 文档：http://localhost:8000/docs
```

### 路线 B：本地 Ollama 模式（零成本免密）

适用场景：无 API Key、内网环境、希望完全本地化运行。

```bash
# 1. 复制环境变量并开启本地模式
cp .env.example .env
# 编辑 .env，取消注释 USE_LOCAL_LLM=true

# 2. 一键启动（含 Ollama 服务 + 自动拉取中文模型 qwen2.5:7b）
make docker-up-ollama
# 或直接执行：
# docker compose -f docker-compose.yml -f docker-compose.ollama.yml up --build -d

# 3. 等待 Ollama 拉取模型完成（首次约 4-5 GB），访问同上
```

> 推荐模型：`qwen2.5:7b`（中文能力强，7B 参数量适合消费级 GPU）。如需更换模型，修改 `docker-compose.ollama.yml` 中的 `OLLAMA_MODEL` 环境变量。

---

## 国产化技术栈与配置

TalentMatch 已完成面向国内环境的国产化改造，降低对国外服务的网络与 API 依赖，默认保持“未配置 Key 仍可运行”的降级策略。

### 国产化技术栈说明

| 能力 | 国产/国内直连方案 | 说明 |
|------|-------------------|------|
| 大语言模型 | 阿里云百炼 DashScope、智谱 Zhipu | 通过 OpenAI-compatible 接口接入 `qwen-max` / `qwen-plus` / `glm-4`，无需代理即可访问 |
| 联网搜索 | 博查 Bocha、智谱 Web Search、本地 SearXNG | 优先使用国内搜索源，失败或没有 Key 时自动降级到 DuckDuckGo |
| 文档解析 / OCR | 阿里云百炼通义千问文档解析 | PDF / DOCX / 图片 JD 可走 `qwen-vl-max` / `qwen-long` 等云端多模态模型解析 |
| MCP Server | 基于官方 Python SDK 自建 | `backend/mcp_server.py` 暴露 4 个工具，schema 与 `backend/app/skills/mcp_config.json` 一致 |
| 国内招聘数据源 | Boss 直聘、智联招聘公开列表页 | Playwright 抓取补充岗位数据，默认关闭 |
| 内容安全 | 阿里云绿网 / 内容安全 | 对简历、JD 等敏感内容进行合规检测，默认关闭 |

这些能力在 `USE_DOMESTIC_LLM=true` 等开关控制下自动生效；未配置 Key 或网络不可达时，系统会退回到规则引擎、本地解析或 DuckDuckGo 搜索，仍可正常启动和运行。

### 国产化配置指南

最小可用的 `.env` 国产化配置示例：

```env
# 优先使用国产 LLM
USE_DOMESTIC_LLM=true
DASHSCOPE_API_KEY=your-dashscope-key
DASHSCOPE_MODEL=qwen-max

# 联网搜索（三选一即可，都会自动降级）
BOCHA_API_KEY=your-bocha-key

# 保持本地 LLM 关闭，避免与国产 LLM 冲突
USE_LOCAL_LLM=false
```

说明：

- `USE_DOMESTIC_LLM=true` 时，LLM 优先级为：**DashScope > 智谱 > 原有 OpenAI-compatible**。
- 未配置 `DASHSCOPE_API_KEY` / `ZHIPU_API_KEY` 等任何 Key 时，系统会降级到规则引擎 / 本地解析，仍可启动运行，方便本地体验与 CI。
- 多模态 / 文档解析默认使用 `qwen-vl-max`，可通过 `DOMESTIC_MULTIMODAL_MODEL` 和 `DASHSCOPE_DOC_PARSE_MODEL` 调整。

### MCP Server 使用

TalentMatch 内置自托管 MCP Server，供外部 Agent 或 IDE 调用：

```bash
# 安装依赖后启动（stdio 模式）
python backend/mcp_server.py
```

暴露的 4 个工具：

| 工具名 | 用途 |
|--------|------|
| `search_jobs` | 联网搜索求职相关信息，如公司评价、面经、薪资、校招动态、技能趋势等 |
| `fuzzy_parse_resume` | 对简历进行模糊识别解析，识别边界不清的经历、零经验场景、求职困境等 |
| `fuzzy_parse_jd` | 对岗位描述进行模糊识别解析，识别应届生友好度、隐性门槛、技能别名等 |
| `detect_job_search_obstacles` | 识别应届毕业生的求职困境与障碍 |

工具 schema 与 `backend/app/skills/mcp_config.json` 完全一致，可直接作为 MCP Client 的配置来源。

### SearXNG 本地搜索部署

如需完全私有、无需 API Key 的联网搜索，可一键启动本地 SearXNG：

```bash
docker compose -f docker-compose.searxng.yml up -d
```

启动后默认访问地址：`http://localhost:8080`，JSON API 示例：

```bash
curl "http://localhost:8080/search?q=Python&format=json"
```

SearXNG 服务不会随主 `docker-compose.yml` 自动启动。如需叠加启动，使用：

```bash
docker compose -f docker-compose.yml -f docker-compose.searxng.yml up -d
```

### 国内招聘数据源

Boss 直聘、智联招聘公开列表页抓取默认关闭，避免开发/测试环境误触发反爬。

开启方式：

1. 在 `.env` 中设置总开关：
   ```env
   DOMESTIC_CRAWLER_ENABLED=true
   ```
2. 在 `backend/app/crawler/sources.py` 中将对应源的 `enabled` 设为 `true`：
   ```python
   {"name": "boss_zhipin", "enabled": True, ...}
   {"name": "zhilian_zhaopin", "enabled": True, ...}
   ```

提醒：开启后可能遇到验证码、IP 限制等反爬机制，建议仅在需要补充国内岗位数据时启用，并适当增大 `DOMESTIC_CRAWLER_DELAY_MS`。

### 内容安全与脱敏

如需对简历、JD 等文本进行内容合规检测，可开启阿里云内容安全：

```env
ENABLE_CONTENT_SAFETY=true
ALIBABA_CLOUD_ACCESS_KEY_ID=your-access-key-id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your-access-key-secret
CONTENT_SAFETY_ENDPOINT=green-cip.cn-shanghai.aliyuncs.com
```

如需对解析后的简历数据进行脱敏（如隐藏手机号、邮箱、身份证号等），开启：

```env
ENABLE_RESUME_MASKING=true
```

两项功能默认关闭，开启前请确保已开通对应的阿里云内容安全服务并拥有有效 AccessKey。

### 本地开发（不使用 Docker）

```bash
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_db.py
python scripts/seed_data.py
uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

或沿用旧版快捷脚本：

```bash
# Linux / macOS
bash scripts/start_local.sh

# Windows PowerShell
.\scripts\start_local.ps1
```

---

## 前端页面

系统包含 7 个核心页面，通过侧边栏导航访问：

### 仪表盘 (`/`)
- 岗位总数、公司总数、平均薪资等关键指标卡片
- 热门城市、热门行业、热门技能排行榜
- 岗位经验分布图表
- 市场趋势摘要

### 岗位匹配 (`/match`)
- 创建/选择用户技能画像（技能、经验级别、目标岗位）
- 上传或粘贴岗位 JD，自动解析
- 一键执行人岗匹配分析，SSE 流式展示各 Agent 执行进度
- 匹配结果展示：匹配分数、技能覆盖度、经验匹配、学历匹配、匹配技能、缺失技能、可迁移技能
- 学习路径建议
- 支持导出匹配结果为 PDF
- 支持将岗位加入收藏

### 简历优化 (`/resume-editor`)
- 上传 PDF/DOCX 简历文件，自动解析为结构化数据
- 分标签页展示：基本信息、教育经历、工作经历、项目经历、技能、证书、语言能力、自我评价
- 基本信息字段使用选择控件（性别、政治面貌、婚姻状况、身份证类型、户口所在地、籍贯、出生日期）
- 上传目标岗位 JD（支持 PDF/DOCX/图片），自动解析
- AI 简历优化：根据 JD 要求动态调整项目经历、实习经历、个人优势
- 字段排放顺序配置：可自定义项目经历、实习经历、个人优势的排列顺序
- 优化前后对比
- 联网搜索：支持搜索公司信息、面经、薪资行情等

### 岗位库 (`/jobs`)
- 岗位列表分页浏览，支持按城市、行业、经验级别筛选
- 关键词搜索岗位
- 岗位详情卡片：公司、薪资、技能要求、经验/学历要求
- 岗位对比：多选岗位并排对比
- 岗位收藏/取消收藏
- 切换收藏视图（`/jobs?favorites=1`）

### 我的收藏 (`/favorites`)
- 重定向到 `/jobs?favorites=1`，复用岗位库页面展示收藏列表
- 从收藏列表快速取消收藏

### 技能图谱 (`/skills`)
- 技能网络图可视化（D3.js 力导向图），展示技能依赖/相似/共现关系
- 技能雷达图，对比用户技能与岗位需求
- 点击技能节点查看详情与关联技能
- 技能分类筛选

### 趋势分析 (`/trends`)
- 热门技能排行与趋势
- 热门岗位排行
- 平均薪资范围
- 行业分布与城市分布图表
- 关键市场指标

---

## API 概览

### 健康检查
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/jobs/health` | 服务健康检查 |
| GET | `/api/v1/skills/config` | Skills 与 MCP 配置 |

### 岗位管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/jobs` | 岗位列表（分页、支持城市/行业/经验级别筛选） |
| GET | `/api/v1/jobs/{id}` | 岗位详情 |
| GET | `/api/v1/jobs/search` | 岗位混合检索（关键词 + 向量） |
| POST | `/api/v1/jobs/parse` | 解析 JD 文本（自动判定模糊解析） |
| POST | `/api/v1/jobs/fuzzy-parse` | JD 模糊识别解析（应届生友好度、隐性门槛、技能别名） |
| POST | `/api/v1/jobs/upload` | 上传 JD 文件（PDF/DOCX/图片，图片支持多模态 OCR） |

### 简历管理
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/resumes/upload` | 上传简历文件（PDF/DOCX），自动解析（自动判定模糊解析） |
| POST | `/api/v1/resumes/parse` | 直接解析简历文本（自动判定模糊解析） |
| POST | `/api/v1/resumes/fuzzy-parse` | 简历模糊识别解析（经历边界、零经验技能、求职困境） |
| POST | `/api/v1/resumes/optimize` | 根据目标 JD 优化简历内容（支持字段排序） |

### 技能管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/skills` | 技能列表（支持按分类筛选） |
| GET | `/api/v1/skills/{id}` | 技能详情 |
| GET | `/api/v1/skills/{id}/related` | 关联技能（依赖/相似/共现关系） |
| POST | `/api/v1/skills/invalidate-cache` | 清空技能图谱缓存（开发调试） |

### 用户画像
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/profiles` | 创建用户技能画像 |
| GET | `/api/v1/profiles` | 用户画像列表 |
| GET | `/api/v1/profiles/{id}/recommendations` | 基于画像的岗位智能推荐（按匹配分数降序） |
| POST | `/api/v1/profiles/{id}/obstacles` | 分析指定画像的求职困境 |

### 岗位收藏
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/profiles/{id}/favorites` | 收藏岗位 |
| DELETE | `/api/v1/profiles/{id}/favorites/{job_id}` | 取消收藏 |
| GET | `/api/v1/profiles/{id}/favorites` | 收藏列表（分页） |

### 人岗匹配
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/matches` | 执行人岗匹配 |
| GET | `/api/v1/matches` | 匹配结果列表 |
| GET | `/api/v1/matches/{id}` | 匹配结果详情 |
| POST | `/api/v1/matches/learning-path` | 生成学习路径 |
| POST | `/api/v1/matches/stream` | SSE 流式匹配分析（实时推送各 Agent 进度） |

### 搜索与分析
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/search` | 联网智能搜索（公司/面经/薪资/校招/技能趋势） |
| POST | `/api/v1/obstacles/analyze` | 求职困境与障碍分析 |
| GET | `/api/v1/trends` | 岗位趋势分析（热门技能、薪资、热门岗位） |
| GET | `/api/v1/dashboard` | 仪表盘聚合数据 |

### 爬虫管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/crawler/status` | 爬虫最近运行状态 |
| POST | `/api/v1/crawler/trigger` | 手动触发岗位采集 |

完整文档见：`http://localhost:8000/docs`

---

## 爬虫与岗位数据来源

本系统岗位数据由**公开 RSS 实时采集**与**人工整理种子数据**共同提供，确保开箱即有岗位可浏览、可匹配。相关实现位于 `backend/app/crawler/`。

### 1. 数据来源说明

当前使用的公开 RSS 源定义于 `backend/app/crawler/sources.py`：

| 源名称 | 类型 | 说明 | 地址 | 是否需过滤 |
|--------|------|------|------|------------|
| v2ex_jobs | rss | V2EX 酷工作节点 RSS，中文技术岗位公开源 | `https://www.v2ex.com/feed/jobs.xml` | 否 |
| ruby_china_jobs | rss | Ruby China 社区话题 RSS，偶含技术岗位 | `https://ruby-china.org/topics/feed` | 是 |
| learnku_python_jobs | rss | LearnKu Python 社区 RSS，含招聘/求职帖 | `https://learnku.com/python/feed` | 是 |
| learnku_laravel_jobs | rss | LearnKu Laravel 社区 RSS，含 PHP/前端岗位帖 | `https://learnku.com/laravel/feed` | 是 |
| learnku_go_jobs | rss | LearnKu Go 社区 RSS，含 Go 岗位帖 | `https://learnku.com/go/feed` | 是 |

`backend/app/crawler/scraper.py` 中的 `JobScraper` 会依次访问上述源，解析标题、正文、薪资、经验、学历、城市、公司名与技能关键词，并统一为结构化 JD。通用社区 RSS（`requires_filter=True`）会经过 `_is_job_related` 过滤，只保留招聘相关条目；专用岗位源（`requires_filter=False`）直接全量解析。单个源失败仅记录日志，不影响其他源继续采集。采集结果默认保存到 `backend/data/raw_jobs.json`（已被 `.gitignore` 忽略）。

### 2. 种子数据兜底

`backend/data/seed_jobs.json` 包含 80 条人工整理的行业典型岗位，覆盖主流技术栈与城市分布，已随仓库提交。

`fetch_real_jobs()` 在 `backend/app/crawler/scraper.py` 中的合并逻辑如下：

1. 始终加载 `seed_jobs.json` 作为稳定基础；
2. 若未强制刷新，再加载本地缓存 `raw_jobs.json`；
3. 当 `种子 + RSS 缓存 < MIN_REAL_JOBS（30 条）` 或传入 `force_fetch=True` 时，执行在线 RSS 实时采集；
4. 按 `title + company_name + source_url` 合并去重，RSS 数据优先，种子数据兜底。

因此即使 RSS 源全部不可用，系统仍能从种子数据获得约 80 条真实岗位。若真实岗位总数仍不足数据库初始化目标（默认 250 条），`seed_database()` 会用生成器补充剩余岗位，保证演示与匹配可用。

### 3. 触发方式

- **自动采集**：`backend/app/config.py` 中 `scheduler_enabled` 默认 `False`，对应环境变量 `SCHEDULER_ENABLED`。设置为 `true` 后，服务启动时 `backend/app/scheduler.py` 会注册间隔任务，默认每 `FETCH_INTERVAL_HOURS=6` 小时执行一次全量 RSS 采集。
- **手动触发**：调用接口 `POST /api/v1/crawler/trigger`，立即执行一次全量 RSS 采集并返回 `{success, fetched}` 等结果。该接口不依赖调度器是否启用。也可访问 `GET /api/v1/crawler/status` 查看最近一次运行状态（时间、成功源、失败源、总数）。

### 4. 如何扩展数据源

**方式一：增加公开 RSS 源**

在 `backend/app/crawler/sources.py` 中按现有格式追加源：

```python
{
    "name": "new_source_jobs",
    "type": "rss",
    "url": "https://example.com/jobs.xml",
    "parser": "rss_atom",
    "description": "示例招聘 RSS 源",
    "requires_filter": True,  # 通用内容需过滤；纯岗位源可设 False
}
```

`JobScraper._fetch_source` 已内置 `rss_atom` 解析，`requires_filter=True` 时会自动过滤招聘帖；`_parse_job` 会统一提取结构化字段。若新源字段格式特殊，可扩展 `_parse_rss_atom_entries` 或 `_parse_job`。

**方式二：接入第三方招聘 API**

如需接入 Boss 直聘、拉勾、猎聘等商业招聘平台，建议申请其官方 API Key，然后：

1. 在 `sources.py` 中新增 `type: "api"` 的源配置（可自定义字段如 `api_key_env`、`endpoint`）；
2. 在 `scraper.py` 的 `_fetch_source` 中按 `source["type"]` 分发，新增 API 请求与响应解析逻辑；
3. 返回与 `_parse_job` 输出一致的字典结构，确保后续去重与入库逻辑无需改动。

### 5. 注意事项

- 当前 RSS 源受网络环境影响，部分地址在中国大陆访问可能需要代理；如遇采集失败，请检查网络连通性或调整 `HTTP_PROXY` / `HTTPS_PROXY`。
- 公开 RSS 源通常只保留最近 10~50 条帖子，实时采集条数有限，因此种子数据是稳定兜底。
- 直接爬取第三方招聘网站可能违反其服务条款并触发反爬机制，建议优先使用官方开放 API 或公开 RSS。
- 单个 RSS 源失败仅记录日志，不会影响其他源继续采集。

---

## LangGraph 智能体工作流

系统基于 LangGraph `StateGraph` 构建有状态图，节点顺序执行：

```
┌──────────┐     ┌─────────────┐     ┌─────────────────┐
│  parse   │ --> │    match    │ --> │    predict      │
│ JD 解析   │     │  人才匹配    │     │   趋势预测       │
└──────────┘     └─────────────┘     └─────────────────┘
                                              |
                                              v
┌──────────┐     ┌─────────────┐
│  advise  │ <-- │    plan     │
│ 综合建议  │     │ 学习路径规划 │
└──────────┘     └─────────────┘
```

**执行流程**：

1. `parse`：解析 JD 文本，输出结构化岗位信息；
2. `match`：将用户画像与目标岗位匹配，输出匹配分数与技能差距；
3. `predict`：基于岗位库聚合数据输出市场趋势；
4. `plan`：根据缺失技能与技能图谱生成学习路径；
5. `advise`：综合以上结果给出简历优化与求职策略建议。

每个节点完成时生成 SSE 事件，前端可实时展示执行进度。

---

## 自动模糊解析机制

系统会根据简历/JD 的实际内容自动判定是否启用模糊解析（应届生友好模式），无需用户手动切换。

### 简历判定规则

| 优先级 | 信号 | 结果 |
|--------|------|------|
| 1 | 存在"工作经历""工作经验""年以上""年经验""资深""高级""专家""总监""经理""主管"等信号 | `fuzzy=false` |
| 2 | 存在"在校""实习""应届生""毕业生""课程设计""毕业设计"或匹配 `202x届` 毕业年份 | `fuzzy=true` |
| 3 | 存在"项目"但缺少"工作经历"分段 | `fuzzy=true` |
| 4 | 文本长度 < 200 且无社招信号 | `fuzzy=true` |
| 5 | 默认 | `fuzzy=false` |

### JD 判定规则

| 优先级 | 信号 | 结果 |
|--------|------|------|
| 1 | 存在"年以上""年经验""资深""高级""专家""总监""管理经验"且无应届生信号 | `fuzzy=false` |
| 2 | 存在"应届生""校招""实习生""接受零基础""经验不限""优秀毕业生""毕业生优先""无经验"或描述宽泛 | `fuzzy=true` |
| 3 | 默认 | `fuzzy=false` |

当 `fuzzy=true` 时，系统使用 `fresh_graduate` 提示词变体，对项目经历、实习经历、课程设计等非传统工作经历进行更细致的解析，并自动触发求职困境检测。

---

## 项目结构

```
.
├── backend/
│   ├── app/
│   │   ├── agents/          # 智能体（JD解析、简历解析、人才匹配、趋势预测、学习路径、技能顾问、简历优化、困境检测、搜索）
│   │   │   ├── base.py          # BaseAgent 基类
│   │   │   ├── jd_parser.py     # JD 解析 Agent
│   │   │   ├── resume_parser.py # 简历解析 Agent
│   │   │   ├── talent_matcher.py# 人才匹配 Agent
│   │   │   ├── trend_predictor.py # 趋势预测 Agent
│   │   │   ├── learning_planner.py # 学习路径规划 Agent
│   │   │   ├── skill_advisor.py # 技能顾问 Agent
│   │   │   ├── resume_optimizer.py # 简历优化 Agent
│   │   │   ├── obstacle_detector.py # 求职困境检测 Agent
│   │   │   ├── search_agent.py  # 联网搜索 Agent
│   │   │   ├── tools.py         # Agent 工具函数（模糊解析等）
│   │   │   ├── graph_state.py   # JobMatchState 工作流状态定义
│   │   │   ├── graph_nodes.py   # 图节点函数
│   │   │   ├── workflow.py      # LangGraph StateGraph 构建与编译
│   │   │   └── orchestrator.py  # 工作流编排器封装
│   │   ├── api/             # REST API（含 SSE 流式端点）
│   │   │   ├── routes.py        # 全部 API 路由
│   │   │   └── schemas.py       # Pydantic 请求/响应模型
│   │   ├── crawler/         # 岗位爬虫
│   │   │   ├── scraper.py       # RSS 采集、解析、去重、缓存
│   │   │   └── sources.py       # 公开 RSS 数据源配置
│   │   ├── data/            # 样例岗位 / 企业 / 技能生成器
│   │   │   └── generator.py     # 技能词表、公司/岗位生成器
│   │   ├── graph/           # 技能图谱构建与查询
│   │   │   └── skill_graph.py   # 技能关系图（依赖/相似/共现）
│   │   ├── llm/             # LangChain LLM 工厂（OpenAI / Ollama 双模式）
│   │   │   └── factory.py       # LLM 客户端创建（含多模态）
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   │   ├── base.py          # 数据库连接与会话管理
│   │   │   ├── job.py           # 岗位模型
│   │   │   ├── company.py       # 公司模型
│   │   │   ├── skill.py         # 技能与技能关系模型
│   │   │   ├── user_skill_profile.py # 用户画像模型
│   │   │   ├── match_result.py  # 匹配结果模型
│   │   │   └── favorite_job.py  # 岗位收藏模型
│   │   ├── prompts/         # 外置提示词模板（.txt，可直接编辑定制）
│   │   │   ├── jd_parser/       # JD 解析提示词
│   │   │   ├── talent_matcher/  # 人才匹配提示词
│   │   │   ├── trend_predictor/ # 趋势预测提示词
│   │   │   ├── learning_planner/# 学习路径提示词
│   │   │   ├── skill_advisor/   # 技能顾问提示词
│   │   │   ├── resume_parser/   # 简历解析提示词
│   │   │   └── resume_optimizer/# 简历优化提示词
│   │   ├── rag/             # Embedding / Chroma / 混合检索
│   │   ├── services/        # 业务逻辑服务
│   │   │   ├── job_service.py   # 岗位查询/搜索/统计
│   │   │   ├── jd_service.py    # JD 解析服务
│   │   │   ├── resume_service.py# 简历解析服务（含自动模糊判定）
│   │   │   ├── skill_service.py # 技能管理/归一化/图谱查询
│   │   │   ├── matching_service.py # 人岗匹配/推荐/学习路径
│   │   │   ├── favorite_service.py # 岗位收藏服务
│   │   │   └── dashboard_service.py # 仪表盘统计服务
│   │   ├── skills/          # TalentMatch Skills 配置
│   │   ├── config.py        # 全局配置（LLM、数据库、调度器等）
│   │   ├── scheduler.py     # 定时任务调度器
│   │   └── main.py          # FastAPI 应用入口
│   ├── data/                # 种子数据与缓存
│   │   ├── seed_jobs.json   # 80 条人工整理行业典型岗位
│   │   └── raw_jobs.json    # RSS 采集缓存（gitignore）
│   ├── scripts/             # init_db / seed_data / export_graph / with_server
│   └── tests/               # pytest 单元与集成测试
├── frontend/
│   ├── src/
│   │   ├── components/      # UI 组件
│   │   │   ├── Layout.tsx        # 侧边栏导航布局（含高亮逻辑）
│   │   │   ├── OnboardingDialog.tsx  # 新手引导弹窗
│   │   │   ├── ResumeProfileForm.tsx # 简历画像表单（选择控件）
│   │   │   ├── JDUploader.tsx    # JD 上传与解析组件
│   │   │   ├── JobCard.tsx       # 岗位卡片
│   │   │   ├── JobCompareSheet.tsx   # 岗位对比面板
│   │   │   ├── MatchResultCard.tsx   # 匹配结果卡片
│   │   │   ├── SkillNetworkGraph.tsx # D3.js 技能网络图
│   │   │   ├── SkillRadarChart.tsx   # 技能雷达图
│   │   │   ├── TrendCharts.tsx   # 趋势图表（Recharts）
│   │   │   ├── ExportPDFButton.tsx   # 导出 PDF 按钮
│   │   │   └── EmptyState.tsx    # 空状态占位组件
│   │   ├── pages/           # 页面组件
│   │   │   ├── SkillDashboard.tsx  # 仪表盘
│   │   │   ├── JobMatch.tsx       # 岗位匹配
│   │   │   ├── ResumeEditor.tsx   # 简历优化
│   │   │   ├── JobLibrary.tsx     # 岗位库（含收藏视图）
│   │   │   ├── SkillGraph.tsx     # 技能图谱
│   │   │   └── TrendAnalysis.tsx  # 趋势分析
│   │   ├── api.ts           # 前端 API 调用层
│   │   ├── types.ts         # TypeScript 类型定义
│   │   ├── App.tsx          # 路由配置
│   │   └── main.tsx         # 应用入口
│   └── package.json
├── e2e/                     # Playwright 端到端冒烟测试
├── scripts/                 # 跨平台启动脚本
│   ├── start.py             # 智能启动脚本（推荐）
│   ├── start_local.sh       # Linux/macOS 快捷启动
│   └── start_local.ps1      # Windows PowerShell 快捷启动
├── docker-compose.yml       # MySQL + Backend + Frontend（云端 API 模式）
├── docker-compose.ollama.yml # Ollama 叠加编排（本地免密模式）
├── Makefile                 # 常用命令
└── .github/workflows/ci.yml # GitHub Actions CI
```

---

## 数据来源

本系统同时使用了**真实公开岗位数据**与**程序生成的兜底数据**，并在 `backend/app/data/` 与 `backend/app/crawler/` 中做了显式区分：

- **技能词表**：`backend/app/data/generator.py` 中人工整理的 100+ 技能，涵盖编程语言、前后端框架、数据库、AI/ML、工具与软技能，用于统一解析与匹配口径。
- **真实岗位数据**：系统通过两条渠道获取真实 JD，合并去重后写入数据库：
  1. **人工整理的行业典型岗位种子**：`backend/data/seed_jobs.json` 包含 80 条基于真实招聘平台常见岗位结构整理的 JD，覆盖主流技术栈与城市分布，保证离线环境也有充足真实样本。
  2. **公开 RSS 实时采集**：`backend/app/crawler/scraper.py` 中的 `JobScraper` 从以下公开 RSS 源采集（遵守 robots.txt 与 RSS 使用规范，设置 1.5s 源间延迟，失败自动跳过）：
     - V2EX 酷工作节点 RSS：`https://www.v2ex.com/feed/jobs.xml`
     - Ruby China 社区话题 RSS：`https://ruby-china.org/topics/feed`
     - LearnKu Python / Laravel / Go 社区 RSS：`https://learnku.com/{python,laravel,go}/feed`
- **数据解析**：对每条真实 JD 提取岗位名称、公司名、城市、薪资（k/元）、经验、学历、技能关键词；缺失字段使用规则模板补全（如薪资按经验级别给默认值）。
- **公司数据**：从真实 JD 的 `company_name` 字段抽取并去重生成公司记录；当真实公司不足时，用生成器补充到 40 家。
- **兜底生成**：当真实 JD 不足 250 条时（公开 RSS 在当前网络环境通常只能采集 10~30 条），`seed_database()` 会用 Faker 生成剩余岗位，保证系统启动后仍有 250 条左右可用 JD。
- **环境控制**：设置环境变量 `FETCH_REAL_JOBS=true` 时，`python -m app.init_db` 与 `scripts/seed_data.py` 会优先加载/采集真实数据；默认 `false` 时仅使用生成数据，便于离线或 CI 环境。
- **本地缓存**：RSS 采集结果写入 `backend/data/raw_jobs.json`，已被 `.gitignore` 忽略；`seed_jobs.json` 作为稳定种子提交到仓库，默认启动即可使用真实岗位样本。

> 当前实测：默认启动可加载 90 条真实 JD（80 条人工整理种子 + 10 条左右公开 RSS），再补充 160 条生成岗位，共 250 条 JD 用于演示与匹配。

---

## 配置

复制 `.env.example` 为 `.env`，根据所选运行模式配置对应区块：

```env
# 通用参数（两种模式均需配置）
DATABASE_URL=mysql+pymysql://talentmatch:talentmatch@mysql:3306/talentmatch?charset=utf8mb4
VECTOR_DB_PATH=./chroma_data

# 前端
VITE_API_BASE_URL=http://localhost:8000

# 应用
APP_ENV=development
LOG_LEVEL=INFO
SECRET_KEY=change-me-in-production

# 路线 A：云端 API 模式
USE_LOCAL_LLM=false
OPENAI_API_KEY=sk-xxx        # 留空则使用确定性降级
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# 路线 B：本地 Ollama 模式
USE_LOCAL_LLM=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# 多模态模型（用于图片 JD 识别）
MULTIMODAL_MODEL=gpt-4o

# 定时任务
SCHEDULER_ENABLED=false
FETCH_INTERVAL_HOURS=6
```

> 未配置任何 LLM 时，系统仍可通过内置规则引擎正常运行（确定性降级），方便本地体验与 CI。

---

## 提示词定制

所有 Agent 的系统提示词已外置为独立文本文件，存放在 `backend/app/prompts/` 目录：

```
backend/app/prompts/
├── jd_parser/         # JD 解析 Agent
├── talent_matcher/    # 人才匹配 Agent
├── trend_predictor/   # 趋势预测 Agent
├── learning_planner/  # 学习路径规划 Agent
├── skill_advisor/     # 技能顾问 Agent
├── resume_parser/     # 简历解析 Agent
└── resume_optimizer/  # 简历优化 Agent
```

如需调整某个 Agent 的推理逻辑或输出格式，**直接编辑对应的 `.txt` 文件即可**，无需修改 Python 源码。修改后重启后端服务即可生效。

---

## 测试

```bash
# 后端单元测试
cd backend
pytest -q

# 导出 LangGraph 工作流 Mermaid 图
cd backend
python scripts/export_graph.py
# 输出 Mermaid 源码到 backend/docs/workflow.mmd

# 前端构建
cd frontend
npm run build

# 端到端冒烟测试（首次运行会下载 Playwright Chromium）
cd /workspace
python e2e/test_job_match_flow.py
```

> 提示：`seed_data.py` 首次执行时会从 Hugging Face 下载 Embedding 模型到本地缓存（`backend/models_cache/`），属于一次性初始化。若只想快速验证页面连通性，可使用 `e2e/seed_minimal.py` 插入少量样本数据。
>
> **中国大陆网络**：若 Hugging Face 下载缓慢或 SSL 报错，可在 `.env` 中设置镜像源后重新运行：
> ```env
> HF_ENDPOINT=https://hf-mirror.com
> ```

---

## LangGraph 工作流可视化

项目提供 `scripts/export_graph.py` 脚本，可一键导出当前工作流的 Mermaid 图和 ASCII 图：

```bash
cd backend
python scripts/export_graph.py
```

输出内容：
- **Mermaid 源码**：可粘贴到 [Mermaid Live Editor](https://mermaid.live) 在线渲染，或直接嵌入 Markdown 文档
- **ASCII 图**：终端直接预览工作流拓扑
- **自动保存**：`backend/docs/workflow.mmd`

> 前端岗位匹配页面在流式分析进行中时，会通过 SSE 实时接收每个 Agent 的执行进度，并展示当前执行节点。

---

## 贡献指南

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/xxx`
3. 提交变更：`git commit -m "feat: xxx"`
4. 推送分支：`git push origin feature/xxx`
5. 创建 Pull Request

---

## 许可证

[MIT](LICENSE)

---

## 致谢

- Embedding 模型：[BAAI/bge-small-zh-v1.5](https://huggingface.co/BAAI/bge-small-zh-v1.5)
- 前端脚手架：[Vite](https://vitejs.dev/)
- UI 组件：[shadcn/ui](https://ui.shadcn.com/) + [Tailwind CSS](https://tailwindcss.com/)
- 图表可视化：[Recharts](https://recharts.org/) + [D3.js](https://d3js.org/)