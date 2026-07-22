# Tasks

- [x] Task 1: 扩展 LLM 工厂以支持国产大模型
  - [x] SubTask 1.1: 在 `backend/app/config.py` 中新增百炼与智谱配置项（DashScope、Zhipu）
  - [x] SubTask 1.2: 修改 `backend/app/llm/factory.py`，`create()` 支持 `USE_DOMESTIC_LLM=true` 时优先使用国产 LLM
  - [x] SubTask 1.3: 修改 `create_multimodal()`，支持国产多模态模型（Qwen-VL / GLM-4V）
  - [x] SubTask 1.4: 更新 `.env.example`，添加国产 LLM 配置示例

- [x] Task 2: 实现国内联网搜索能力
  - [x] SubTask 2.1: 在 `backend/app/agents/search_tool.py` 中新增 `_search_bocha()` 函数
  - [x] SubTask 2.2: 在 `backend/app/agents/search_tool.py` 中新增 `_search_zhipu()` 函数
  - [x] SubTask 2.3: 在 `backend/app/agents/search_tool.py` 中新增 `_search_searxng()` 函数
  - [x] SubTask 2.4: 修改 `search_web()` 调用优先级：博查 -> 智谱 -> SearXNG -> Tavily -> DuckDuckGo
  - [x] SubTask 2.5: 在 `docker-compose.searxng.yml` 中添加 SearXNG 服务编排
  - [ ] SubTask 2.6: 验证博查/智谱/SearXNG 至少有一种能在国内网络下返回结果（需配置真实 API Key 或启动本地 SearXNG 后验证）

- [x] Task 3: 接入云端简历/JD 文档解析
  - [x] SubTask 3.1: 在 `backend/app/services/resume_service.py` 中新增 `_parse_with_dashscope()` 方法
  - [x] SubTask 3.2: 修改 `parse_resume()` / `extract_text_from_pdf()` / `extract_text_from_docx()`，配置存在时优先使用云端解析
  - [x] SubTask 3.3: 修改 JD 图片 OCR 流程，优先尝试国产多模态模型（`create_multimodal()`）
  - [x] SubTask 3.4: 确保云端解析失败时自动降级到本地解析

- [x] Task 4: 自建 MCP Server 暴露核心工具
  - [x] SubTask 4.1: 新增 `backend/mcp_server.py`，使用官方 `mcp` Python SDK
  - [x] SubTask 4.2: 注册 `search_jobs`、`fuzzy_parse_resume`、`fuzzy_parse_jd`、`detect_job_search_obstacles` 四个工具
  - [x] SubTask 4.3: 确保工具 schema 与 `backend/app/skills/mcp_config.json` 一致
  - [x] SubTask 4.4: 通过 `python backend/mcp_server.py` 启动验证

- [x] Task 5: 增加国内招聘数据源支持
  - [x] SubTask 5.1: 在 `backend/app/crawler/sources.py` 中新增国内平台源配置（Boss 直聘/智联公开页）
  - [x] SubTask 5.2: 在 `backend/app/crawler/scraper.py` 的 `_fetch_source()` 中按 `type` 分发，新增 Playwright 抓取逻辑
  - [x] SubTask 5.3: 实现国内平台页面解析，统一输出 `_parse_job()` 所需字段
  - [x] SubTask 5.4: 将抓取工具同时注册为 MCP 工具 `search_jobs` 的可选实现

- [x] Task 6: 接入内容安全与数据脱敏
  - [x] SubTask 6.1: 在 `backend/app/config.py` 中新增阿里云内容安全配置项
  - [x] SubTask 6.2: 新增 `backend/app/utils/content_safety.py`，封装阿里云绿网/内容安全检测 API
  - [x] SubTask 6.3: 在简历/JD 上传与优化流程中调用内容安全检测
  - [x] SubTask 6.4: 新增 `ENABLE_RESUME_MASKING` 配置与基础脱敏函数（身份证、手机号）

- [x] Task 7: 更新文档与配置
  - [x] SubTask 7.1: 更新 `README.md`，增加国产化技术栈与部署说明
  - [x] SubTask 7.2: 更新 `.env.example`，包含全部新增配置项
  - [x] SubTask 7.3: 在 `docker-compose.yml` 中可选引入 SearXNG 与 MCP Server 服务

- [x] Task 8: 验证与测试
  - [x] SubTask 8.1: 编写测试：国产 LLM 客户端可初始化
  - [ ] SubTask 8.2: 编写测试：博查/智谱/SearXNG 至少一个返回非空结果（需配置真实 API Key 或本地 SearXNG 后验证）
  - [x] SubTask 8.3: 编写测试：MCP Server 工具列表包含 4 个工具
  - [x] SubTask 8.4: 运行 `npm run build` 与 `pytest`，确保无新增错误
  - [ ] SubTask 8.5: 在关闭代理环境下手动验证联网搜索与 LLM 调用（需真实 Key 与国内网络环境）

# Task Dependencies

- Task 3 依赖 Task 1（需要 `create_multimodal()` 支持国产多模态）
- Task 4 依赖 Task 2（`search_jobs` MCP 工具依赖国内搜索实现）
- Task 5 依赖 Task 4（国内平台抓取作为 MCP 工具可选实现）
- Task 6 依赖 Task 1（内容安全摘要需要 LLM 支持，但检测调用不依赖）
- Task 8 依赖 Task 1-6 全部完成
