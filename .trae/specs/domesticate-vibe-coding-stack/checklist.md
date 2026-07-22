# Checklist

## 国产 LLM 接入

- [x] `backend/app/config.py` 已新增 `DASHSCOPE_API_KEY`、`DASHSCOPE_MODEL`、`DASHSCOPE_BASE_URL`
- [x] `backend/app/config.py` 已新增 `ZHIPU_API_KEY`、`ZHIPU_MODEL`、`ZHIPU_BASE_URL`
- [x] `backend/app/config.py` 已新增 `USE_DOMESTIC_LLM` 开关
- [x] `backend/app/llm/factory.py` 在 `USE_DOMESTIC_LLM=true` 时优先返回百炼或智谱客户端
- [x] `backend/app/llm/factory.py` 的 `create_multimodal()` 支持国产多模态模型
- [x] 未配置 Key 时系统仍能通过规则引擎降级运行
- [x] `.env.example` 已包含国产 LLM 配置示例

## 国内联网搜索

- [x] `backend/app/agents/search_tool.py` 已实现 `_search_bocha()`
- [x] `backend/app/agents/search_tool.py` 已实现 `_search_zhipu()`
- [x] `backend/app/agents/search_tool.py` 已实现 `_search_searxng()`
- [x] `search_web()` 按博查 -> 智谱 -> SearXNG -> Tavily -> DuckDuckGo 优先级选择
- [x] `docker-compose.searxng.yml` 已包含 SearXNG 服务编排
- [ ] 博查或 SearXNG 至少有一种在国内直连网络下可返回结果（需配置真实 API Key 或启动本地 SearXNG 后验证）

## 云端文档解析

- [x] `backend/app/services/resume_service.py` 已新增 `_parse_with_dashscope()` 或类似方法
- [x] 配置存在时 PDF/DOCX 解析优先使用云端解析
- [x] 云端解析失败时自动降级到本地解析
- [x] 图片 JD OCR 优先尝试国产多模态模型

## MCP Server

- [x] 已新增 `backend/mcp_server.py`
- [x] MCP Server 使用官方 `mcp` Python SDK
- [x] 已注册 `search_jobs`、`fuzzy_parse_resume`、`fuzzy_parse_jd`、`detect_job_search_obstacles` 四个工具
- [x] 工具 schema 与 `backend/app/skills/mcp_config.json` 一致
- [x] `python backend/mcp_server.py` 可正常启动

## 国内招聘数据源

- [x] `backend/app/crawler/sources.py` 已新增国内平台源配置
- [x] `backend/app/crawler/scraper.py` 已按 `source["type"]` 分发并支持 Playwright 抓取
- [x] 国内平台抓取结果统一为 `_parse_job()` 输出格式
- [x] 抓取失败不影响现有 RSS/种子数据加载

## 内容安全与脱敏

- [x] `backend/app/config.py` 已新增阿里云内容安全配置项
- [x] 已新增 `backend/app/utils/content_safety.py` 封装内容安全检测
- [x] 简历/JD 上传与优化流程已调用内容安全检测
- [x] 检测到违规内容时返回明确错误
- [x] 已实现 `ENABLE_RESUME_MASKING` 配置与基础脱敏函数

## 文档与配置

- [x] `README.md` 已更新国产化技术栈说明
- [x] `README.md` 已更新国产化部署说明
- [x] `.env.example` 已包含全部新增配置项
- [x] `docker-compose.yml` 可选引入 SearXNG/MCP Server（可选）

## 验证与测试

- [x] 国产 LLM 客户端初始化测试通过
- [ ] 国内搜索工具真实网络测试通过（至少一种返回非空结果；需配置真实 API Key 或本地 SearXNG）
- [x] MCP Server 工具列表测试通过
- [x] 前端 `npm run build` 成功
- [x] 后端 `pytest` 通过（既有失败除外；本次全量 90 passed / 0 failed）
- [ ] 关闭代理环境下手动验证联网搜索成功（需真实 Key 与国内网络环境）
