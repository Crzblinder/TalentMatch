# Tasks

## Phase 1: 后端基础设施升级（P0）

- [ ] Task 1: 引入 Celery + Redis 异步任务队列
  - [ ] 添加 `celery[redis]`、`redis` 依赖到 requirements.txt
  - [ ] 创建 `backend/app/tasks/__init__.py` 和 `celery_app.py` 配置 Celery
  - [ ] 创建 `backend/app/tasks/parse_tasks.py`：简历/JD 解析任务
  - [ ] 创建 `backend/app/tasks/match_tasks.py`：岗位匹配任务
  - [ ] 创建 `backend/app/tasks/search_tasks.py`：联网搜索任务
  - [ ] 在 `routes.py` 添加任务提交与状态查询端点：`POST /api/v1/tasks` 和 `GET /api/v1/tasks/{task_id}`
  - [ ] 配置任务重试策略（最多 3 次，指数退避）
  - [ ] 更新 `scripts/start.py` 和 `launch.ps1` 启动 Celery Worker

- [ ] Task 2: 建立多级缓存层
  - [ ] 添加 `redis` 客户端封装 `backend/app/core/cache.py`
  - [ ] 实现 `get`/`set`/`delete`/`clear` 接口，支持 TTL
  - [ ] 封装 `backend/app/services/cache_service.py`：Redis 优先，内存兜底
  - [ ] 为技能图谱、趋势统计、岗位列表、匹配结果添加缓存装饰器
  - [ ] 在数据变更时触发缓存失效

- [ ] Task 3: 向量数据库解耦与可切换
  - [ ] 抽象向量存储接口 `backend/app/rag/vector_store_base.py`
  - [ ] 实现 Chroma 适配器 `backend/app/rag/vector_store_chroma.py`
  - [ ] 实现 Qdrant 适配器 `backend/app/rag/vector_store_qdrant.py`
  - [ ] 在 `backend/app/config.py` 添加 `VECTOR_DB_PROVIDER` 和 `QDRANT_URL` 配置
  - [ ] 修改 `get_vector_store()` 根据配置返回对应适配器
  - [ ] 保持默认 Chroma 模式不变

- [ ] Task 4: 安全配置加固
  - [ ] 在 `backend/app/config.py` 启动校验中检查 SECRET_KEY 是否为默认值
  - [ ] 生产环境使用 SQLite 时拒绝启动
  - [ ] 为敏感配置项添加最小长度/格式校验
  - [ ] 更新 `.env.example` 和 README 中生产配置说明

## Phase 2: 后端业务增强（P1）

- [ ] Task 5: 服务端 PDF 导出
  - [ ] 添加 `weasyprint` 或 `reportlab` 依赖到 requirements.txt
  - [ ] 创建 `backend/app/services/report_service.py` 生成匹配报告 PDF
  - [ ] 设计 PDF 模板：封面、匹配分数、技能对比、分析摘要
  - [ ] 在 `routes.py` 添加 `POST /api/v1/reports/match/pdf` 端点
  - [ ] 确保中文字体正确嵌入

- [ ] Task 6: 用户多简历/多画像管理
  - [ ] 新增 `Resume` 和 `Profile` 数据库模型
  - [ ] 添加 CRUD API：`GET/POST/PUT/DELETE /api/v1/profiles`
  - [ ] 在 `Profile` 模型中增加 `is_active` 字段标记当前活跃画像
  - [ ] 修改匹配接口支持传入 `profile_id` 或默认使用活跃画像
  - [ ] 迁移现有单画像逻辑到新模型

- [ ] Task 7: 结构化日志与链路追踪
  - [ ] 引入 `structlog` 或配置标准库 JSON 日志
  - [ ] 在中间件中生成并传递 `request_id`
  - [ ] 在各 Agent 入口记录输入长度、输出摘要、耗时、模型名
  - [ ] 失败日志包含异常类型和降级信息

## Phase 3: 可观测性与运维（P1）

- [ ] Task 8: Prometheus Metrics 暴露
  - [ ] 添加 `prometheus-client` 依赖
  - [ ] 创建 `backend/app/api/metrics.py` 暴露 `/metrics` 端点
  - [ ] 采集 RSS 采集成功率、LLM 调用延迟、解析失败率、缓存命中率
  - [ ] 在关键路径埋点

- [ ] Task 9: 健康检查与持续探活
  - [ ] 创建 `/health` 端点，聚合数据库、Redis、向量库、LLM、搜索状态
  - [ ] 将配置检测逻辑复用于健康检查
  - [ ] 支持 `/health/live` 和 `/health/ready` 探针
  - [ ] 增加后台定时探活任务（可选）

- [ ] Task 10: 告警阈值与通知
  - [ ] 定义告警规则：LLM 失败率、RSS 采集失败率、解析失败率阈值
  - [ ] 支持邮件/Webhook 通知通道配置
  - [ ] 在告警触发时记录结构化日志

## Phase 4: 测试与质量（P2）

- [ ] Task 11: LLM Eval 评估机制
  - [ ] 创建 `backend/eval/` 目录，放置标注数据集和评估脚本
  - [ ] 实现简历/JD 解析准确率、幻觉率、JSON 结构化成功率评估
  - [ ] 输出评估报告（Markdown/JSON）
  - [ ] 在 CI 中增加 eval job，设置准确率下降阈值

- [ ] Task 12: 提示词版本管理
  - [ ] 将 prompts 统一放到 `backend/app/prompts/` 并按版本命名
  - [ ] 在配置中支持 `PROMPT_VERSION` 切换
  - [ ] 为每个提示词版本维护回归测试用例

- [ ] Task 13: 扩展 E2E 覆盖
  - [ ] 添加岗位收藏 E2E 用例
  - [ ] 添加配置检测页面 E2E 用例
  - [ ] 添加简历优化 E2E 用例
  - [ ] 添加服务端 PDF 导出 E2E 用例
  - [ ] 使用 Page Object 模式重构测试代码

- [ ] Task 14: 性能/压力测试
  - [ ] 添加 Locust 或 k6 压力测试脚本
  - [ ] 测试并发解析、并发匹配场景
  - [ ] 输出基准性能报告

## Phase 5: 前端体验增强（P2）

- [ ] Task 15: 移动端复杂表单适配
  - [ ] 使用前端设计插件优化简历编辑器、匹配分析表单在小屏下的布局
  - [ ] 拆分长表单为多步骤或折叠面板
  - [ ] 优化触摸交互（按钮大小、输入框聚焦）

- [ ] Task 16: 多画像前端管理
  - [ ] 创建画像列表页面
  - [ ] 在顶部栏或侧边栏增加当前活跃画像切换器
  - [ ] 画像创建/编辑弹窗

- [ ] Task 17: 降级状态明确提示
  - [ ] 创建全局 `BackendStatusBanner` 组件
  - [ ] 后端在 API 响应中返回当前使用的 LLM/搜索/解析后端
  - [ ] 前端根据状态显示规则引擎/本地模型/降级提示
  - [ ] 提示条提供配置入口链接

- [ ] Task 18: 服务端 PDF 导出前端对接
  - [ ] 修改 `ExportPDFButton` 调用后端 `/api/v1/reports/match/pdf`
  - [ ] 显示生成进度和下载结果
  - [ ] 移除浏览器端 PDF 生成代码

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
