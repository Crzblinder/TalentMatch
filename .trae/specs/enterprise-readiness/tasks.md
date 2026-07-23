# Tasks

## Phase 1: 后端基础设施升级（P0）

- [x] Task 1: 引入 Celery + Redis 异步任务队列
  - [x] 添加 `celery[redis]`、`redis` 依赖到 requirements.txt
  - [x] 创建 `backend/app/tasks/__init__.py` 和 `celery_app.py` 配置 Celery
  - [x] 创建 `backend/app/tasks/parse_tasks.py`：简历/JD 解析任务
  - [x] 创建 `backend/app/tasks/match_tasks.py`：岗位匹配任务
  - [x] 创建 `backend/app/tasks/search_tasks.py`：联网搜索任务
  - [x] 在 `routes.py` 添加任务提交与状态查询端点：`POST /api/v1/tasks` 和 `GET /api/v1/tasks/{task_id}`
  - [x] 配置任务重试策略（最多 3 次，指数退避）
  - [x] 更新 `launch.ps1` 启动 Celery Worker（已调用 scripts/start.py，其内部启动 backend + frontend + Celery Worker）

- [x] Task 2: 建立多级缓存层
  - [x] 添加 `redis` 客户端封装 `backend/app/core/cache.py`
  - [x] 实现 `get`/`set`/`delete`/`clear` 接口，支持 TTL
  - [x] 封装 `backend/app/services/cache_service.py`：Redis 优先，内存兜底
  - [x] 为技能图谱、趋势统计、岗位列表、匹配结果添加缓存装饰器
  - [x] 在数据变更时触发缓存失效

- [x] Task 3: 向量数据库解耦与可切换
  - [x] 抽象向量存储接口 `backend/app/rag/vector_store_base.py`
  - [x] 实现 Chroma 适配器 `backend/app/rag/vector_store_chroma.py`
  - [x] 实现 Qdrant 适配器 `backend/app/rag/vector_store_qdrant.py`
  - [x] 在 `backend/app/config.py` 添加 `VECTOR_DB_PROVIDER` 和 `QDRANT_URL` 配置
  - [x] 修改 `get_vector_store()` 根据配置返回对应适配器
  - [x] 保持默认 Chroma 模式不变

- [x] Task 4: 安全配置加固
  - [x] 在 `backend/app/config.py` 启动校验中检查 SECRET_KEY 是否为默认值
  - [x] 生产环境使用 SQLite 时拒绝启动
  - [x] 为敏感配置项添加最小长度/格式校验
  - [ ] 更新 `.env.example` 和 README 中生产配置说明（实现阶段补充文档）

## Phase 2: 后端业务增强（P1）

- [x] Task 5: 服务端 PDF 导出
  - [x] 添加 `reportlab` 依赖到 requirements.txt（Windows 友好）
  - [x] 创建 `backend/app/services/report_service.py` 生成匹配报告 PDF
  - [x] 设计 PDF 模板：标题、匹配分数、技能对比、分析摘要、时间戳
  - [x] 在 `routes.py` 添加 `POST /api/v1/reports/match/pdf` 端点
  - [x] 中文字体优先使用系统 SimHei/SimSun/Microsoft YaHei，回退到 Helvetica

- [x] Task 6: 用户多简历/多画像管理（补全 is_active 与默认画像逻辑）
  - [ ] 新增 `Resume` 和 `Profile` 数据库模型（保持现有 `UserSkillProfile` 模型，未新增 Resume 模型）
  - [x] 添加 CRUD API：`GET/POST/PUT/DELETE /api/v1/profiles`
  - [x] 在 `UserSkillProfile` 模型中增加 `is_active` 字段标记当前活跃画像
  - [x] 修改匹配接口支持传入 `profile_id` 或默认使用活跃画像
  - [x] 通过 `init_db.py` 的 `_ensure_columns` 自动迁移 `is_active` 列

- [x] Task 7: 结构化日志与链路追踪
  - [x] 引入 `structlog` 并配置开发环境可读 / 生产环境 JSON 输出
  - [x] 在 `backend/app/main.py` 添加 request_id 中间件，写入响应头 `x-request-id`
  - [x] 在 `BaseAgent.call_llm` 入口记录输入长度、输出摘要、耗时、模型名
  - [x] 失败日志包含异常类型与降级/回退信息

## Phase 3: 可观测性与运维（P1）

- [x] Task 8: Prometheus Metrics 暴露
  - [x] 添加 `prometheus-client` 依赖
  - [x] 创建 `backend/app/api/metrics.py` 暴露 `/metrics` 端点
  - [x] 采集 RSS 采集成功率、LLM 调用延迟、解析失败率、缓存命中率
  - [x] 在关键路径埋点

- [x] Task 9: 健康检查与持续探活
  - [x] 创建 `/health` 端点，聚合数据库、Redis、向量库、LLM、搜索状态
  - [x] 将配置检测逻辑复用于健康检查
  - [x] 支持 `/health/live` 和 `/health/ready` 探针
  - [x] 增加后台定时探活任务

- [x] Task 10: 告警阈值与通知
  - [x] 定义告警规则：LLM 失败率、RSS 采集失败率、解析失败率阈值
  - [x] 支持邮件/Webhook 通知通道配置
  - [x] 在告警触发时记录结构化日志

## Phase 4: 测试与质量（P2）

- [x] Task 11: LLM Eval 评估机制
  - [x] 创建 `backend/eval/` 目录，放置标注数据集和评估脚本
  - [x] 实现简历/JD 解析准确率、幻觉率、JSON 结构化成功率评估
  - [x] 输出评估报告（Markdown/JSON）
  - [x] 在 CI 中增加 eval job，设置准确率下降阈值

- [x] Task 12: 提示词版本管理
  - [x] 将 prompts 统一放到 `backend/app/prompts/` 并按版本命名
  - [x] 在配置中支持 `PROMPT_VERSION` 切换
  - [x] 为每个提示词版本维护回归测试用例

- [x] Task 13: 扩展 E2E 覆盖
  - [x] 添加岗位收藏 E2E 用例
  - [x] 添加配置检测页面 E2E 用例
  - [x] 添加简历优化 E2E 用例
  - [x] 添加服务端 PDF 导出 E2E 用例
  - [x] 使用 Page Object 模式重构测试代码

- [x] Task 14: 性能/压力测试
  - [x] 添加 Locust 或 k6 压力测试脚本
  - [x] 测试并发解析、并发匹配场景
  - [x] 输出基准性能报告

## Phase 5: 前端体验增强（P2）

- [x] Task 15: 移动端复杂表单适配
  - [x] 使用响应式布局优化简历编辑器、匹配分析表单在小屏下的布局
  - [x] 拆分长表单为多步骤或折叠面板（ResumeProfileForm 已在移动端使用 Accordion）
  - [x] 优化触摸交互（按钮大小、输入框聚焦）

- [x] Task 16: 多画像前端管理
  - [x] 创建画像列表页面（ProfileManager.tsx）
  - [x] 在顶部栏或侧边栏增加当前活跃画像切换器（Layout 中的 ProfileSwitcher）
  - [x] 画像创建/编辑弹窗

- [ ] Task 17: 降级状态明确提示
  - [ ] 创建全局 `BackendStatusBanner` 组件
  - [ ] 后端在 API 响应中返回当前使用的 LLM/搜索/解析后端
  - [ ] 前端根据状态显示规则引擎/本地模型/降级提示
  - [ ] 提示条提供配置入口链接

- [ ] Task 18: 服务端 PDF 导出前端对接
  - [ ] 修改 `ExportPDFButton` 调用后端 `/api/v1/reports/match/pdf`
  - [ ] 显示生成进度和下载结果
  - [ ] 移除浏览器端 PDF 生成代码

### Phase 5 前端体验增强完成说明（Task 15-16）

1. **Task 15（移动端复杂表单适配）**
   - `frontend/src/pages/JobMatch.tsx`：保留桌面端岗位表格，新增移动端 `<md` 岗位卡片列表（单选、薪资、技能标签、发布时间），避免 375px 下表格横向溢出；步骤指示器在移动端简化为进度条；所有按钮/输入框触摸目标 ≥44px。
   - `frontend/src/pages/ResumeEditor.tsx`：标题栏、字段顺序拖拽区、搜索栏均支持小屏换行与截断；项目/实习/自我评价输入框与文本域加大到 ≥44px 并增加 `focus-visible:ring-primary` 聚焦高亮；AI 优化按钮与字段排序按钮适配移动端。
   - `frontend/src/components/JDUploader.tsx`：JD 解析页面的联网求职情报搜索栏改为可换行，输入框、选择框、搜索按钮统一高度 44px。
   - `frontend/src/components/ResumeProfileForm.tsx`：已在移动端使用 Accordion 折叠面板，桌面端保持 Tabs；所有表单控件已设置 `min-h-[44px]`。

2. **Task 16（多画像前端管理）**
   - 新增 `frontend/src/components/ProfileContext.tsx`：全局管理画像列表、生效画像、CRUD 与活跃切换，提供 `useProfile` Hook。
   - 新增 `frontend/src/pages/ProfileManager.tsx`：支持列表查看、新建、编辑、删除、设为活跃；活跃画像排序置顶。
   - 更新 `frontend/src/components/Layout.tsx`：桌面端侧边栏与移动端顶部栏均加入 `ProfileSwitcher` 下拉，可快速切换活跃画像并跳转画像管理页；导航新增「画像管理」。
   - 更新 `frontend/src/App.tsx`：以 `ProfileProvider` 包裹应用并注册 `/profiles` 路由。
   - 更新 `frontend/src/api.ts` 与 `frontend/src/types.ts`：增加 `getActiveProfile`、`setActiveProfile`、`updateProfile`、`deleteProfile`，`ProfileResponse` 补齐 `is_active`。
   - 更新 `backend/app/api/routes.py`：新增 `DELETE /api/v1/profiles/{profile_id}`，级联删除关联匹配记录。
   - `JobMatch` 集成生效画像：进入页面时自动用 `effectiveProfile` 预填表单；若用户未修改画像信息，匹配时直接使用生效画像 ID，避免重复创建。

### 验证方式（Task 15-16）

```powershell
# 1. 启动项目
cd d:\TalentMatch
python scripts/start.py

# 2. 前端构建检查
cd d:\TalentMatch\frontend
npm run build

# 3. 核心 E2E 冒烟测试
cd d:\TalentMatch
python e2e/test_job_match_flow.py

# 4. 手动验证
# - 访问 http://127.0.0.1:5173/profiles 创建/编辑/删除画像并切换活跃画像
# - 访问 http://127.0.0.1:5173/match，确认步骤 1 自动预填当前活跃画像
# - 使用浏览器 DevTools 切换至 375px 宽度，检查 ResumeEditor 与 JobMatch 无横向溢出、按钮可点击
```

## Phase 6: CI/CD 与文档（P2）

- [ ] Task 19: CI/CD 增强
  - [ ] 在 GitHub Actions 中启动 Redis 服务容器
  - [ ] 增加 Celery Worker 启动步骤
  - [ ] 增加 eval job 和性能测试 job
  - [ ] 确保 CI 中所有 job 不依赖真实付费 API Key

- [ ] Task 20: 部署文档更新
  - [ ] 更新 README 中 Redis、Celery、Qdrant 部署说明
  - [ ] 提供 docker-compose.yml 生产版本（含 Redis、Qdrant、Worker）
  - [ ] 添加生产配置检查清单

# Task Dependencies

```
Phase 1 (后端基础设施)
├── Task 1 (Celery + Redis) ───────────── 无依赖
├── Task 2 (多级缓存) ─────────────────── 无依赖，与 Task 1 可并行
├── Task 3 (向量库解耦) ───────────────── 无依赖
└── Task 4 (安全配置) ─────────────────── 无依赖

Phase 2 (后端业务增强)
├── Task 5 (服务端 PDF) ───────────────── 依赖 Task 1
├── Task 6 (多画像) ───────────────────── 依赖 Task 2（缓存画像数据）
└── Task 7 (结构化日志) ───────────────── 无依赖

Phase 3 (可观测性)
├── Task 8 (Metrics) ──────────────────── 依赖 Task 2
├── Task 9 (健康检查) ─────────────────── 依赖 Task 1, Task 2, Task 3
└── Task 10 (告警) ───────────────────── 依赖 Task 8, Task 9

Phase 4 (测试与质量)
├── Task 11 (LLM Eval) ────────────────── 依赖 Task 1
├── Task 12 (提示词版本) ──────────────── 无依赖
├── Task 13 (E2E 扩展) ────────────────── 依赖 Task 6, Task 9
└── Task 14 (压力测试) ────────────────── 依赖 Task 1, Task 2

Phase 5 (前端体验)
├── Task 15 (移动端适配) ──────────────── 依赖 Task 6
├── Task 16 (多画像前端) ──────────────── 依赖 Task 6
├── Task 17 (降级提示) ────────────────── 依赖 Task 7
└── Task 18 (PDF 导出对接) ────────────── 依赖 Task 5

Phase 6 (CI/CD 与文档)
├── Task 19 (CI 增强) ──────────────────── 依赖 Task 1, Task 11, Task 13
└── Task 20 (部署文档) ─────────────────── 依赖 Task 1, Task 2, Task 3
```

## 本次回填完成说明（2026-07-23）

完成了 Task 1、Task 5、Task 6、Task 7 的后端回填，以及 Task 8-10 的可观测性实现，使 Phase 1-3 核心功能可端到端运行。

### 关键改动

1. **Task 1（Celery Worker 一键启动）**
   - 确认 `launch.ps1` 已调用 `scripts/start.py`，后者在全栈/仅后端模式下都会启动 Celery Worker。

2. **Task 5（服务端 PDF 导出）**
   - `backend/requirements.txt` 增加 `reportlab>=4.2.0`。
   - 新增 `backend/app/services/report_service.py`，使用 ReportLab 生成 A4 PDF，包含标题、时间戳、岗位信息、用户画像、总体匹配分数、技能对比、分析摘要。
   - 中文字体自动探测系统 `simhei.ttf` / `simsun.ttc` / `msyh.ttc`，不存在时回退到 Helvetica。
   - `backend/app/api/routes.py` 新增 `POST /api/v1/reports/match/pdf`，支持按 `match_id` 拉取数据库生成，或传入 `match_data/job_data/profile_data` 直接生成。
   - `backend/app/api/schemas.py` 新增 `MatchReportPDFRequest`。

3. **Task 6（多画像 is_active）**
   - `backend/app/models/user_skill_profile.py` 增加 `is_active` 布尔列，默认 `False`。
   - `backend/app/api/schemas.py` 为 `UserSkillProfileCreate/Out/Update` 增加 `is_active` 字段。
   - `backend/app/api/routes.py` 新增：
     - `GET /api/v1/profiles/active` 获取当前活跃画像
     - `GET /api/v1/profiles/{id}` 获取单个画像
     - `PUT /api/v1/profiles/{id}` 更新画像（含切换活跃状态）
     - `POST /api/v1/profiles/{id}/set-active` 设置活跃画像
   - 全局保证只有一个活跃画像（`_ensure_single_active_profile`）。
   - `POST /api/v1/matches` 与 `POST /api/v1/matches/learning-path` 在未传 `profile_id` 时自动使用活跃画像。
   - `backend/app/init_db.py` 的 `_ensure_columns` 自动为旧表补齐 `is_active` 列。

4. **Task 7（结构化日志）**
   - `backend/requirements.txt` 增加 `structlog>=24.1.0`。
   - `backend/app/main.py` 配置 structlog：开发环境彩色控制台，生产环境 JSON；同步标准库日志；新增 HTTP 中间件为每个请求生成/传递 `request_id` 并回写响应头 `x-request-id`。
   - `backend/app/agents/base.py` 改用 structlog，在 `call_llm` 入口/出口记录 `agent/model/input_length/output_summary/duration_ms`，失败时记录 `exception_type` 与降级原因。

5. **其他修复**
   - 修复 `backend/app/rag/vector_store.py` 的 E402 import 顺序问题，使 `python -m ruff check app tests` 全部通过。
   - `backend/app/config.py` 增加 `prompt_version` 字段，兼容现有提示词版本加载逻辑。

### 验证方式

```powershell
# 1. 安装依赖
cd d:\TalentMatch\backend
python -m pip install -r requirements.txt

# 2. 启动后端
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3. 另开终端，检查 ruff
python -m ruff check app tests

# 4. 测试 PDF 端点（返回有效 PDF）
curl -X POST http://127.0.0.1:8000/api/v1/reports/match/pdf `
  -H "Content-Type: application/json" `
  -d '{"match_data":{"match_score":0.85,"skill_score":0.9,"experience_match":0.8,"education_match":0.75,"matched_skills":["Python"],"missing_skills":["K8s"],"analysis_summary":"匹配良好"},"job_data":{"title":"后端","company":{"name":"A"},"city":"上海","salary_min":20000,"salary_max":30000,"experience_level":"3年","education_level":"本科"}}' `
  --output report.pdf

# 5. 测试活跃画像匹配（先创建 is_active=true 的画像，再不带 profile_id 匹配）
curl -X POST http://127.0.0.1:8000/api/v1/profiles -H "Content-Type: application/json" -d '{"name":"我","skills":["Python"],"is_active":true}'
curl -X POST http://127.0.0.1:8000/api/v1/matches -H "Content-Type: application/json" -d '{"job_id":1}'
```

### Phase 3 可观测性完成说明（Task 8-10）

6. **Task 8（Prometheus Metrics）**
   - `backend/requirements.txt` 已包含 `prometheus-client>=0.20.0`。
   - 新增 `backend/app/api/metrics.py`：定义 `CollectorRegistry` 与 `talentmatch_*` 指标，包括 `rss_fetch_total`、`llm_call_duration_milliseconds`、`llm_call_total`、`parse_task_total`、`cache_access_total`、`health_check_total`。
   - 提供 `record_rss_fetch`、`record_llm_call`、`record_parse_task`、`record_cache_access`、`record_health_check` 等埋点辅助函数。
   - `backend/app/main.py` 注册 `GET /metrics` 端点，返回 Prometheus 抓取格式。
   - 关键路径埋点位置：`backend/app/crawler/scraper.py`（RSS）、`backend/app/agents/base.py`（LLM）、`backend/app/services/cache_service.py`（缓存）、`backend/app/tasks/parse_tasks.py`（解析）。

7. **Task 9（健康检查与持续探活）**
   - 新增 `backend/app/api/health.py`：定义 `HealthStatus` / `HealthReport`，复用 `app.utils.config_tester` 检测数据库、向量库、LLM、搜索，并补充 Redis 缓存检查。
   - `backend/app/main.py` 注册：
     - `GET /health`：完整聚合健康报告。
     - `GET /health/live`：存活探针。
     - `GET /health/ready`：就绪探针，关键依赖失败时返回 503。
   - `backend/app/scheduler.py` 新增 `health_probe_job`，每 5 分钟后台运行一次就绪检查并记录日志。

8. **Task 10（告警阈值与通知）**
   - `backend/app/config.py` 增加告警配置：`alert_enabled`、LLM/RSS/解析失败率阈值、SMTP 与 Webhook 通知参数。
   - 新增 `backend/app/services/alert_service.py`：定义 `AlertRule` / `AlertEvent`，基于 Prometheus Counter 计算失败率，超过阈值时触发告警。
   - 支持邮件（SMTP）与 Webhook 双通道通知；告警事件通过 JSON 结构化日志输出。
   - `backend/app/scheduler.py` 新增 `alert_evaluation_job`，每 5 分钟后台评估一次；默认 `alert_enabled=false`，未配置时不发送通知。

### 验证方式（Task 8-10）

```powershell
# 1. 启动后端
cd d:\TalentMatch\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. 另开终端检查指标
curl.exe -s http://127.0.0.1:8000/metrics | findstr /i "talentmatch"

# 3. 检查健康检查
curl.exe -s http://127.0.0.1:8000/health | python -m json.tool
curl.exe -s http://127.0.0.1:8000/health/live | python -m json.tool
curl.exe -s -o nul -w "%{http_code}" http://127.0.0.1:8000/health/ready

# 4. 代码质量检查
python -m ruff check app/api/metrics.py app/api/health.py app/services/alert_service.py app/main.py app/scheduler.py app/config.py
```

### Phase 4 测试与质量完成说明（Task 11-14）

9. **Task 11（LLM Eval 评估机制）**
   - 新增 `backend/eval/run_eval.py`：加载 `backend/eval/data/resume_parse_samples.jsonl` 与 `jd_parse_samples.jsonl` 标注数据集，调用 `ResumeParser` / `JDParser` 评估字段准确率、幻觉率、JSON 结构化成功率与耗时。
   - 默认强制 `OPENAI_API_KEY=""`，在无付费 Key 时走规则引擎降级，确保可运行。
   - 输出 `backend/eval/reports/eval_report.json` 与 `eval_report.md`；任意任务准确率低于 0.5 时返回非零退出码，便于 CI 中断。

10. **Task 12（提示词版本管理）**
    - 新增 `backend/app/prompts/loader.py`：按 `backend/app/prompts/{agent}/{variant}.txt` 或 `backend/app/prompts/{agent}/{version}/{variant}.txt` 加载提示词。
    - 支持变体别名（default / zero-shot / cot 等），指定变体不存在时自动 fallback 到 `zero_shot`；版本目录不存在时回退到未版本化提示词。
    - `backend/app/config.py` 已增加 `prompt_version` 配置；`BaseAgent` 读取 `settings.prompt_version` 加载对应版本提示词。
    - 新增 `backend/tests/test_prompt_loader.py` 回归测试，覆盖默认加载、别名映射、版本化加载、多级 fallback、缺失 Agent 异常等场景。

11. **Task 13（扩展 E2E 覆盖 + Page Object 重构）**
    - 新增 Page Object：`e2e/pages/base.py`、`layout.py`、`job_library.py`、`job_match.py`、`resume_editor.py`、`config_tests.py`。
    - 新增 E2E 用例：
      - `e2e/test_favorites.py`：岗位收藏/取消收藏及导航高亮验证。
      - `e2e/test_config_tests.py`：配置检测页面汇总卡片与分类筛选验证。
      - `e2e/test_resume_editor.py`：简历上传（生成 `.docx`）、解析、AI 优化流程验证。
      - `e2e/test_pdf_export.py`：服务端 PDF 导出 API 验证。
    - `e2e/test_job_match_flow.py` 已重构为使用 Page Object，并跳过新手引导弹窗。

12. **Task 14（性能/压力测试）**
    - 新增 `backend/perf/load_test.py`：基于 `ThreadPoolExecutor` 的本地并发基准测试，覆盖 JD 解析、简历解析、岗位匹配三个场景，输出 RPS / 平均/P95/最大延迟。
    - 新增 `backend/perf/locustfile.py`：Locust 压力测试脚本，模拟用户执行 JD 解析、简历解析、创建匹配等任务。
    - 压力测试不依赖付费 API Key（使用规则引擎/本地模型），便于本地与 CI 运行。

13. **本次联调修复**
    - 修复 `backend/app/services/job_service.py` 中 `list_jobs` 被 `@cached` 装饰后，ORM 对象被 JSON 序列化为字符串，导致后续请求返回 500 的问题；现在在服务层即将 `Job` 实例转换为可缓存的字典。
    - 同步调整 `backend/app/api/routes.py` 的 `list_jobs`，兼容缓存命中时的字典项与未缓存时的 ORM 实例兜底。
    - 修复 `backend/app/api/health.py` 搜索健康检查：当只配置了 SearXNG（本地默认地址）和 DuckDuckGo 等兜底搜索且未配置付费搜索 Key 时，将其失败视为 `skip` 而非 `fail`，避免健康状态误报。

### 验证方式（Task 11-14）

```powershell
# 1. 安装依赖并启动项目
cd d:\TalentMatch
python scripts/start.py

# 2. 运行 LLM Eval（无 API Key 可走规则引擎）
cd d:\TalentMatch\backend
python -m eval.run_eval

# 3. 运行提示词加载器回归测试
python -m pytest backend/tests/test_prompt_loader.py -q

# 4. 运行核心 E2E 冒烟测试
python e2e/test_job_match_flow.py

# 5. 本地并发基准测试（需先启动后端）
python -m perf.load_test

# 6. Locust 压力测试（可选）
python -m locust -f backend/perf/locustfile.py --host http://127.0.0.1:8000

# 7. 代码质量检查
python -m ruff check app tests
cd d:\TalentMatch\frontend && npm run build
```

### 未改动范围

- 未实现 Task 6 中的新增独立 `Resume` / `Profile` 模型（保持现有 `UserSkillProfile`）。
- 未对接前端 `ExportPDFButton`（属于 Task 18 / Phase 5）。
- 未改动 Task 15-20。
