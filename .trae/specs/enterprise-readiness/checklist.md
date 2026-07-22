# Checklist

## Phase 1: 后端基础设施升级

### 异步任务队列
- [ ] Celery 配置正确，能连接 Redis
- [ ] `POST /api/v1/tasks` 提交解析任务后返回任务 ID
- [ ] `GET /api/v1/tasks/{task_id}` 可查询任务状态和结果
- [ ] 大文件解析不阻塞 HTTP 请求
- [ ] 任务失败时按指数退避重试最多 3 次
- [ ] `scripts/start.py` 和 `launch.ps1` 能同时启动 API 和 Celery Worker

### 多级缓存层
- [ ] Redis 客户端封装提供 get/set/delete/clear 接口
- [ ] Redis 不可用时自动降级到内存缓存
- [ ] 技能图谱请求首次命中数据库，后续命中缓存
- [ ] 趋势统计接口结果缓存 1 小时
- [ ] 数据变更后缓存正确失效

### 向量数据库解耦
- [ ] `VECTOR_DB_PROVIDER=chroma` 时使用本地 Chroma
- [ ] `VECTOR_DB_PROVIDER=qdrant` 时连接远程 Qdrant
- [ ] 向量存储接口统一，业务代码无需关心具体实现
- [ ] 多后端实例可共享同一 Qdrant 集合

### 安全配置加固
- [ ] `SECRET_KEY` 为默认值或空时，生产模式拒绝启动
- [ ] `ENV=production` 且使用 SQLite 时拒绝启动
- [ ] 启动日志清晰提示需要修改的配置项
- [ ] `.env.example` 中 SECRET_KEY 为空，README 提供生成命令

## Phase 2: 后端业务增强

### 服务端 PDF 导出
- [ ] `POST /api/v1/reports/match/pdf` 返回 PDF 文件
- [ ] PDF 包含匹配分数、技能对比、分析摘要、时间戳
- [ ] 中文字体正确显示，无乱码
- [ ] 版式和分页稳定可控

### 用户多简历/多画像管理
- [ ] `Profile` 模型支持多画像存储
- [ ] 画像 CRUD API 工作正常
- [ ] 可标记和切换当前活跃画像
- [ ] 匹配接口默认使用活跃画像，也可通过 `profile_id` 指定
- [ ] 现有单画像数据平滑迁移

### 结构化日志与链路追踪
- [ ] 每条请求有统一的 `request_id`
- [ ] Agent 入口日志包含输入长度、输出摘要、耗时、模型名
- [ ] 失败日志包含异常类型和降级信息
- [ ] 日志格式为 JSON 或结构化键值对

## Phase 3: 可观测性与运维

### Prometheus Metrics
- [ ] `/metrics` 端点可访问
- [ ] 采集 RSS 采集成功率、LLM 调用延迟、解析失败率、缓存命中率
- [ ] 关键路径正确埋点

### 健康检查与持续探活
- [ ] `/health` 聚合展示数据库、Redis、向量库、LLM、搜索状态
- [ ] `/health/live` 和 `/health/ready` 探针区分
- [ ] 外部依赖失效时状态变为 degraded
- [ ] 配置检测逻辑复用于健康检查

### 告警阈值与通知
- [ ] 定义 LLM 失败率、RSS 采集失败率、解析失败率阈值
- [ ] 支持邮件/Webhook 通知通道
- [ ] 告警触发时记录结构化日志

## Phase 4: 测试与质量

### LLM Eval 评估机制
- [ ] `backend/eval/` 包含标注数据集和评估脚本
- [ ] 评估脚本输出解析准确率、幻觉率、JSON 结构化成功率
- [ ] 评估报告写入本地 Markdown/JSON 文件
- [ ] CI 中 eval job 能在无真实 Key 时运行并产出报告

### 提示词版本管理
- [ ] prompts 集中到 `backend/app/prompts/`
- [ ] 提示词文件按版本命名
- [ ] `PROMPT_VERSION` 配置可切换版本
- [ ] 每个版本有回归测试用例

### 扩展 E2E 覆盖
- [ ] 岗位收藏 E2E 用例通过
- [ ] 配置检测页面 E2E 用例通过
- [ ] 简历优化 E2E 用例通过
- [ ] 服务端 PDF 导出 E2E 用例通过
- [ ] 使用 Page Object 模式重构测试

### 性能/压力测试
- [ ] Locust/k6 脚本可运行
- [ ] 并发解析、并发匹配场景有基准数据
- [ ] 输出性能报告

## Phase 5: 前端体验增强

### 移动端复杂表单适配
- [ ] 简历编辑器在小屏下可正常使用
- [ ] 匹配分析表单在小屏下布局合理
- [ ] 触摸交互元素尺寸符合移动端规范

### 多画像前端管理
- [ ] 画像列表页面可创建、编辑、删除画像
- [ ] 顶部栏/侧边栏可切换当前活跃画像
- [ ] 切换后匹配使用新画像

### 降级状态明确提示
- [ ] 全局状态提示条组件存在
- [ ] LLM 降级到规则引擎时显示提示
- [ ] 提示提供配置入口
- [ ] 搜索降级时同样显示提示

### 服务端 PDF 导出前端对接
- [ ] 点击导出按钮调用后端接口
- [ ] 显示生成进度
- [ ] PDF 正确下载
- [ ] 移除旧的浏览器端 PDF 生成代码

## Phase 6: CI/CD 与文档

### CI/CD 增强
- [ ] GitHub Actions 启动 Redis 服务容器
- [ ] CI 中启动 Celery Worker
- [ ] CI 中运行 eval job
- [ ] CI 中不依赖真实付费 API Key

### 部署文档更新
- [ ] README 包含 Redis、Celery、Qdrant 部署说明
- [ ] 提供生产版 docker-compose.yml
- [ ] 生产配置检查清单完整
