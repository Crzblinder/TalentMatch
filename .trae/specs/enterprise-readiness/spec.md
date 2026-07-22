# 企业级可落地性增强 Spec

## Why
当前 TalentMatch 在功能完整度和国产化适配上已具备雏形，但在高并发、高可用、可观测、可测试、可扩展等工程维度仍存在明显缺口，无法直接部署到生产环境或支撑多用户持续使用。本 Spec 针对这些缺口进行系统性补齐，使项目从“可用 demo”演进为“可维护、可扩展、可观测”的工程化产品。

## What Changes
- 引入异步任务队列（Celery + Redis），将简历/JD 解析、匹配分析、联网搜索等大模型调用改为后台任务，避免同步阻塞
- 引入多级缓存层（Redis + 内存），缓存技能图谱、趋势统计、岗位列表、匹配结果等热点数据
- 向量数据库解耦，支持 Chroma 本地模式与 Qdrant/Milvus 远程模式切换，解决多实例部署冲突
- 安全配置加固：移除危险的默认 SECRET_KEY、默认 SQLite 提示、敏感配置校验
- 前端体验增强：移动端表单适配、用户多简历/多画像管理、服务端 PDF 导出、降级状态明确提示
- 测试与质量：扩展 E2E 覆盖、建立 LLM Eval 评估机制、提示词版本化与回归测试
- 运维可观测性：结构化日志、Prometheus Metrics、健康检查探活、告警阈值

## Impact
- Affected specs: production-readiness-optimization（已完成）
- Affected code: 后端 services/agents/routes/config/models、前端 pages/components、CI/CD、部署配置

---

## ADDED Requirements

### Requirement: 异步任务队列
系统 SHALL 使用 Celery + Redis 将大模型调用、文件解析、联网搜索等耗时操作转为后台任务，前端通过任务 ID 轮询或 WebSocket 获取结果。

#### Scenario: 上传大文件解析
- **WHEN** 用户上传一份 5MB PDF 简历
- **THEN** 接口立即返回任务 ID，后台异步解析，不阻塞 HTTP 请求
- **AND** 前端轮询任务状态，完成后展示解析结果

#### Scenario: 任务失败重试
- **WHEN** 后台任务因 LLM 超时失败
- **THEN** 系统按指数退避自动重试最多 3 次
- **AND** 重试均失败后标记任务失败并返回明确错误信息

### Requirement: 多级缓存层
系统 SHALL 使用 Redis 缓存热点数据，并在应用层提供内存缓存作为兜底，减少实时计算和数据库查询。

#### Scenario: 技能图谱缓存命中
- **WHEN** 用户重复访问技能图谱页面
- **THEN** 首次从数据库构建后写入 Redis，后续请求从 Redis 读取
- **AND** 技能数据变更时通过事件或 TTL 使缓存失效

#### Scenario: 趋势统计缓存
- **WHEN** 仪表盘调用趋势统计接口
- **THEN** 系统在 Redis 中缓存 1 小时，避免每次实时聚合

### Requirement: 向量数据库可切换
系统 SHALL 支持通过配置切换向量数据库后端，默认保持 Chroma 本地模式，生产环境可切换为 Qdrant 或 Milvus。

#### Scenario: 使用 Qdrant 部署
- **WHEN** 配置 `VECTOR_DB_PROVIDER=qdrant` 并提供 Qdrant URL
- **THEN** 系统使用 Qdrant 存储和检索向量，不再依赖本地 Chroma 文件
- **AND** 多后端实例可同时访问同一 Qdrant 集群，支持水平扩展

#### Scenario: 默认 Chroma 模式
- **WHEN** 未配置远程向量数据库
- **THEN** 系统继续使用本地 Chroma，保持单机和开发环境易用性

### Requirement: 安全配置加固
系统 SHALL 在启动时校验关键安全配置，拒绝使用危险的默认值，并给出明确的配置指引。

#### Scenario: 默认 SECRET_KEY 拦截
- **WHEN** `SECRET_KEY` 为 `change-me-in-production` 或空
- **THEN** 启动日志输出 ERROR 级别警告，生产模式直接退出
- **AND** 文档中提供生成强 SECRET_KEY 的命令

#### Scenario: 生产环境数据库检查
- **WHEN** `ENV=production` 且使用 SQLite
- **THEN** 系统拒绝启动并提示切换到 MySQL/PostgreSQL

### Requirement: 用户多简历/多画像
系统 SHALL 允许用户保存和管理多份简历与多个画像，并可在不同画像间快速切换目标岗位。

#### Scenario: 创建新画像
- **WHEN** 用户在画像管理页面点击“新建画像”
- **THEN** 系统保存新的画像记录，包含独立技能、经验、学历信息
- **AND** 用户可随时切换当前活跃画像

#### Scenario: 切换画像后匹配
- **WHEN** 用户切换活跃画像并重新执行岗位匹配
- **THEN** 系统使用新画像计算匹配分数，无需重新填写信息

### Requirement: 服务端 PDF 导出
系统 SHALL 提供后端 PDF 导出接口，替代浏览器客户端生成，确保版式、分页、中文字体稳定可控。

#### Scenario: 导出匹配报告
- **WHEN** 用户点击“导出 PDF”
- **THEN** 前端调用后端接口生成 PDF 并触发下载
- **AND** PDF 包含匹配分数、技能对比、分析摘要、时间戳

### Requirement: 降级状态明确提示
系统 SHALL 在前端清晰展示当前使用的 LLM/搜索/解析后端状态，当发生降级时给出明确提示。

#### Scenario: LLM 降级到规则引擎
- **WHEN** 所有 LLM Key 缺失或调用失败
- **THEN** 前端顶部显示“当前使用规则引擎解析，结果可能不如 AI 精准”提示条
- **AND** 提示条提供配置入口

### Requirement: LLM Eval 评估机制
系统 SHALL 建立 LLM 输出评估框架，定期或按需评估简历/JD 解析准确率、幻觉率、JSON 结构化成功率。

#### Scenario: 解析准确率评估
- **WHEN** 运行评估脚本并传入标注数据集
- **THEN** 系统输出各模型/提示词版本的准确率、召回率、F1、JSON 解析成功率
- **AND** 评估结果写入本地报告文件

#### Scenario: 提示词回归测试
- **WHEN** 修改 prompts 目录下的提示词文件
- **THEN** CI 自动运行 Eval 任务，若准确率下降超过阈值则阻止合并

### Requirement: 扩展 E2E 覆盖
系统 SHALL 扩展 E2E 测试覆盖简历优化、收藏对比、配置检测、服务端 PDF 导出等核心链路。

#### Scenario: 收藏岗位
- **WHEN** E2E 测试访问岗位库并点击收藏
- **THEN** 验证收藏列表中出现该岗位，且导航高亮“我的收藏”

#### Scenario: 配置检测页面
- **WHEN** E2E 测试访问 /config-tests
- **THEN** 验证页面加载并显示检测结果摘要

### Requirement: 结构化日志与链路追踪
系统 SHALL 使用结构化日志记录各 Agent 执行耗时、输入输出摘要、失败原因，并支持追踪一次请求在多个 Agent 间的流转。

#### Scenario: 解析请求追踪
- **WHEN** 一次简历解析请求进入系统
- **THEN** 日志中包含统一的 request_id、各阶段耗时、模型名称、是否命中缓存
- **AND** 失败时包含异常堆栈和降级信息

### Requirement: Prometheus Metrics 与告警
系统 SHALL 暴露 /metrics 端点，采集 RSS 采集成功率、LLM 调用延迟、解析失败率、缓存命中率等关键指标。

#### Scenario: 采集失败告警
- **WHEN** 连续 3 次 RSS 采集失败率超过 50%
- **THEN** Metrics 中相关指标上升，可触发外部告警系统通知

### Requirement: 持续健康探活
系统 SHALL 提供 /health 端点，持续检测数据库、Redis、向量库、LLM、搜索等外部依赖的可用性。

#### Scenario: 外部 API 失效
- **WHEN** 运行中某 LLM API 突然不可用
- **THEN** /health 端点状态变为 degraded，并在日志中记录具体失效项
- **AND** 系统按降级策略继续服务

---

## MODIFIED Requirements

### Requirement: 配置检测模块
配置检测 SHALL 从单次检查扩展为可配置的持续探活任务，支持通过 /health 聚合展示，并在依赖失效时触发告警。

#### Scenario: 探活任务触发告警
- **WHEN** 配置检测发现数据库连接断开
- **THEN** /health 返回 degraded 状态
- **AND** 若配置了告警通道，则发送通知

---

## REMOVED Requirements

### Requirement: 浏览器端 PDF 生成
**Reason**: 版式、分页、中文字体不可控，客户端依赖浏览器渲染。
**Migration**: 迁移到服务端 PDF 导出接口，前端调用后端 /api/v1/reports/match/pdf 下载。
