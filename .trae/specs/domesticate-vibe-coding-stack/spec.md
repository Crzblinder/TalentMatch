# 国产化 Vibe Coding 技术栈替换 Spec

## Why

项目当前依赖的联网搜索（DuckDuckGo/Tavily）、LLM（OpenAI/Ollama-only）与国内招聘数据源均不符合《国产化 Vibe Coding 替换方案与执行指南》提出的"国内直连、真实可用、合规可控"要求。为提升在国内网络环境下的可用性、降低代理依赖、避免虚构库导致运行失败，需要将搜索、LLM、文档解析、MCP 与内容安全等关键能力替换为国产化或国内可直连方案。

## What Changes

- 新增国产 LLM 接入：阿里云百炼（Qwen-Max / Qwen-Plus）与智谱 GLM-4，通过 OpenAI-compatible 接口接入，保留现有降级能力。
- 新增国内联网搜索：博查（Bocha）API 与智谱 Web Search，作为 Tavily/DuckDuckGo 的优先替代，并保留原有降级路径。
- 新增本地开源搜索兜底：SearXNG Docker Compose 编排与 `searxng_search` 工具函数。
- 新增云端简历/JD 文档解析：通义千问文档解析 API（Qwen-Long / Qwen-VL）与 Doc2X 接入点，优先用于 PDF/图片，本地解析作为降级。
- 新增自建 MCP Server：基于官方 `mcp` Python SDK，将 `search_jobs`、`fuzzy_parse_resume`、`fuzzy_parse_jd`、`detect_job_search_obstacles` 暴露为 MCP 工具。
- 新增国内招聘数据源支持：可选接入 Boss 直聘、智联招聘等公开页面抓取（通过 Playwright 自建 MCP 工具），与现有 RSS 种子数据共存。
- 新增内容安全与数据脱敏：接入阿里云/百炼内容安全 API，对上传简历进行敏感信息检测与解析后脱敏/清理。
- 更新配置：`.env.example` 增加国产化相关配置项；README 增加国产化部署说明。

## Impact

- Affected specs：LLM 配置、联网搜索、简历解析、MCP 工具链、数据源、内容安全。
- Affected code：
  - `backend/app/llm/factory.py`
  - `backend/app/config.py`
  - `backend/app/agents/search_tool.py`
  - `backend/app/agents/search_agent.py`
  - `backend/app/services/resume_service.py`
  - `backend/app/services/jd_service.py`
  - `backend/app/agents/tools.py`
  - `backend/app/skills/mcp_config.json`
  - 新增 `backend/mcp_server.py`
  - 新增 `searxng` Docker Compose 叠加文件
  - `.env.example`
  - `README.md`

## ADDED Requirements

### Requirement: 国产 LLM 接入

The system SHALL support domestic LLM providers through OpenAI-compatible endpoints.

#### Scenario: 使用阿里云百炼
- **WHEN** 用户配置 `USE_DOMESTIC_LLM=true`、`DASHSCOPE_API_KEY`、`DASHSCOPE_MODEL=qwen-max`
- **THEN** `LLMClientFactory.create()` 返回指向 `https://dashscope.aliyuncs.com/compatible-mode/v1` 的 ChatOpenAI 实例

#### Scenario: 使用智谱 GLM-4
- **WHEN** 用户配置 `USE_DOMESTIC_LLM=true`、`ZHIPU_API_KEY`、`ZHIPU_MODEL=glm-4`
- **THEN** `LLMClientFactory.create()` 返回指向 `https://open.bigmodel.cn/api/paas/v4` 的 ChatOpenAI 实例

#### Scenario: 无 Key 时确定性降级
- **WHEN** 未配置任何有效 API Key
- **THEN** 系统仍通过规则引擎运行，不阻塞服务启动

### Requirement: 国内联网搜索

The system SHALL provide domestic web search options and fallback to existing search implementations.

#### Scenario: 博查搜索
- **WHEN** 配置 `BOCHA_API_KEY`
- **THEN** `search_web()` 优先调用博查 API 并返回结构化 `{title, url, snippet}` 列表

#### Scenario: 智谱 Web Search
- **WHEN** 配置 `ZHIPU_API_KEY` 且启用智谱搜索
- **THEN** `search_web()` 可调用智谱 Web Search 并返回结构化结果

#### Scenario: SearXNG 本地搜索
- **WHEN** 本地部署 SearXNG（`docker compose -f docker-compose.searxng.yml up`）
- **THEN** `searxng_search()` 可访问 `http://localhost:8080` 执行元搜索并返回结果

#### Scenario: 搜索降级
- **WHEN** 博查/智谱/SearXNG 均不可用
- **THEN** 回退到 DuckDuckGo/Tavily；两者均失败时返回空结果并记录日志

### Requirement: 云端文档解析

The system SHALL support cloud-based resume/JD document parsing with local parsing as fallback.

#### Scenario: 通义千问文档解析
- **WHEN** 上传 PDF/DOCX/图片且配置了 `DASHSCOPE_API_KEY`
- **THEN** 优先调用通义千问文档解析 API 获取 Markdown/JSON
- **AND** 本地 PyPDF2/python-docx 解析作为降级

#### Scenario: 多模态图片 JD 识别国产化
- **WHEN** 上传图片 JD 且配置了国产多模态模型
- **THEN** 使用 Qwen-VL / GLM-4V 进行 OCR 识别
- **AND** 原 OpenAI 多模态作为兼容路径保留

### Requirement: 自建 MCP Server

The system SHALL expose core agent tools as an MCP server using the official Python SDK.

#### Scenario: 启动 MCP Server
- **WHEN** 运行 `python backend/mcp_server.py`
- **THEN** 通过 stdio 提供 `search_jobs`、`fuzzy_parse_resume`、`fuzzy_parse_jd`、`detect_job_search_obstacles` 四个工具
- **AND** 工具定义与 `backend/app/skills/mcp_config.json` 保持一致

#### Scenario: MCP 工具调用
- **WHEN** MCP Client 调用 `search_jobs(query="北京 Java", intent="general", location="北京", top_n=5)`
- **THEN** 返回国内搜索源结果，优先博查/SearXNG

### Requirement: 国内招聘数据源

The system SHALL optionally fetch job data from domestic recruitment platforms.

#### Scenario: Boss 直聘公开页抓取
- **WHEN** 配置启用国内平台抓取且 MCP Server 可用
- **THEN** 通过 Playwright 抓取指定城市/关键词的公开岗位列表，解析为统一 JD 结构
- **AND** 失败时仅记录日志，不影响现有 RSS/种子数据

### Requirement: 内容安全与数据脱敏

The system SHALL check uploaded content for sensitive information and provide basic data protection.

#### Scenario: 内容安全审核
- **WHEN** 简历/JD 文本进入解析或优化流程
- **THEN** 如配置 `ALIBABA_CLOUD_ACCESS_KEY_ID` 与绿网/内容安全 endpoint，调用阿里云内容安全 API 进行文本审核
- **AND** 检测到违规内容时返回明确错误，不进入后续处理

#### Scenario: 简历数据清理
- **WHEN** 简历解析完成并返回结果后
- **THEN** 可选对身份证号、手机号等字段进行脱敏或移除（由 `ENABLE_RESUME_MASKING` 控制）

## MODIFIED Requirements

### Requirement: LLM 工厂配置

现有 `LLMClientFactory` 仅支持 OpenAI-compatible 与 Ollama。修改后：
- 新增 `DASHSCOPE_API_KEY`、`DASHSCOPE_MODEL`、`DASHSCOPE_BASE_URL` 配置项
- 新增 `ZHIPU_API_KEY`、`ZHIPU_MODEL`、`ZHIPU_BASE_URL` 配置项
- `create()` 在 `USE_DOMESTIC_LLM=true` 时优先构造国产 LLM 客户端
- 保持现有 `USE_LOCAL_LLM` 与 OpenAI 配置完全兼容

### Requirement: 联网搜索工具

现有 `search_tool.py` 使用 DuckDuckGo/Tavily。修改后：
- 新增 `_search_bocha()` 与 `_search_zhipu()` 实现
- `search_web()` 按"博查 -> 智谱 -> Tavily -> DuckDuckGo"优先级选择
- 新增 `_search_searxng()` 用于本地 SearXNG

### Requirement: 简历解析服务

现有 `ResumeService` 仅本地解析。修改后：
- `extract_text_from_pdf` / `extract_text_from_docx` 增加云端解析优先分支
- 新增 `_parse_with_dashscope()` 辅助方法
- 解析失败自动回退本地解析

## REMOVED Requirements

### Requirement: 使用 Tavily 作为默认联网搜索

**Reason**：Tavily 为国外服务，国内直连不稳定，不符合国产化要求。
**Migration**：保留 `TAVILY_API_KEY` 配置作为最末位降级选项，但默认推荐博查/智谱/SearXNG。

### Requirement: 依赖 DuckDuckGo 作为唯一默认搜索

**Reason**：DuckDuckGo 在国内网络环境下可用性差，且常被反爬拦截。
**Migration**：DuckDuckGo 作为所有国内搜索失败后的兜底选项保留。
