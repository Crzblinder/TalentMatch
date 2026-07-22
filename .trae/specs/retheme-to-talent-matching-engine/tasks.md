# Tasks

- [x] Task 1: 清理旧业务代码与数据，准备重构基础
  - [x] SubTask 1.1: 删除 `backend/app/agents/` 下旧舆情相关 agent 文件（scanner.py, matcher.py, predictor.py, governance.py, expert.py）
  - [x] SubTask 1.2: 删除 `backend/app/models/` 下旧模型（case.py, enterprise.py, sentiment.py）及关联表
  - [x] SubTask 1.3: 删除 `backend/app/services/sentiment_service.py` 及不再使用的 migration/seed 脚本
  - [x] SubTask 1.4: 更新 `backend/app/data/generator.py` 生成真实 JD + 技能 + 公司数据，移除 Faker 舆情与企业风险数据

- [x] Task 2: 建立新数据模型与持久化层
  - [x] SubTask 2.1: 创建 `backend/app/models/job.py`（岗位模型）
  - [x] SubTask 2.2: 创建 `backend/app/models/skill.py`（技能模型）
  - [x] SubTask 2.3: 创建 `backend/app/models/skill_relation.py`（技能关系模型：依赖/相似/共现）
  - [x] SubTask 2.4: 创建 `backend/app/models/company.py`（公司模型，替代 Enterprise）
  - [x] SubTask 2.5: 创建 `backend/app/models/user_skill_profile.py`（用户技能画像）
  - [x] SubTask 2.6: 创建 `backend/app/models/match_result.py`（匹配结果）
  - [x] SubTask 2.7: 更新 `backend/app/models/base.py` 导出新模型，更新 `init_db.py` 初始化逻辑

- [x] Task 3: 重构 LangGraph 多 Agent 工作流
  - [x] SubTask 3.1: 创建 `backend/app/agents/jd_parser.py`（JD 解析 Agent）
  - [x] SubTask 3.2: 创建 `backend/app/agents/talent_matcher.py`（人岗匹配 Agent）
  - [x] SubTask 3.3: 创建 `backend/app/agents/trend_predictor.py`（趋势预测 Agent）
  - [x] SubTask 3.4: 创建 `backend/app/agents/learning_planner.py`（学习路径 Agent）
  - [x] SubTask 3.5: 创建 `backend/app/agents/skill_advisor.py`（技能建议 Agent）
  - [x] SubTask 3.6: 重写 `backend/app/agents/workflow.py` 编排新 5-Agent 流
  - [x] SubTask 3.7: 更新 `backend/app/agents/base.py` 中的通用 LLM 调用与降级逻辑

- [x] Task 4: 更新 RAG 检索层
  - [x] SubTask 4.1: 重写 `backend/app/rag/retriever.py` 目标为 JD 与技能知识片段
  - [x] SubTask 4.2: 更新 `backend/app/rag/vector_store.py` collection 命名与元数据字段
  - [x] SubTask 4.3: 调整 embedding 输入源为 JD description 与 skill definitions

- [x] Task 5: 更新后端服务与 API
  - [x] SubTask 5.1: 创建 `backend/app/services/job_service.py`（岗位服务）
  - [x] SubTask 5.2: 创建 `backend/app/services/matching_service.py`（匹配服务）
  - [x] SubTask 5.3: 创建 `backend/app/services/skill_service.py`（技能服务）
  - [x] SubTask 5.4: 重写 `backend/app/api/routes.py` 为 `/api/v1/jobs/*` 路由组
  - [x] SubTask 5.5: 更新 Pydantic schemas，移除 sentiment 相关 DTO
  - [x] SubTask 5.6: 更新 `backend/app/main.py` 中的 API 挂载与事件生命周期

- [x] Task 6: 重构前端页面与路由
  - [x] SubTask 6.1: 重命名并重构 `frontend/src/pages/Dashboard.tsx` → `SkillDashboard.tsx`
  - [x] SubTask 6.2: 重命名并重构 `frontend/src/pages/Analyze.tsx` → `JobMatch.tsx`
  - [x] SubTask 6.3: 重命名并重构 `frontend/src/pages/Cases.tsx` → `JobLibrary.tsx`
  - [x] SubTask 6.4: 重命名并重构 `frontend/src/pages/Enterprises.tsx` → `SkillGraph.tsx`
  - [x] SubTask 6.5: 重命名并重构 `frontend/src/pages/Evaluation.tsx` → `TrendAnalysis.tsx`
  - [x] SubTask 6.6: 更新 `frontend/src/App.tsx` 路由与导航菜单
  - [x] SubTask 6.7: 更新 `frontend/src/api.ts` 接口路径与类型定义

- [x] Task 7: 更新前端组件与可视化
  - [x] SubTask 7.1: 创建/更新技能雷达图组件
  - [x] SubTask 7.2: 创建/更新知识图谱力导向图组件
  - [x] SubTask 7.3: 创建/更新岗位匹配结果卡片组件
  - [x] SubTask 7.4: 创建/更新趋势图表组件（薪资/城市/技能热度）

- [x] Task 8: 更新测试与基础设施
  - [x] SubTask 8.1: 重写 `backend/tests/test_api.py` 与 `backend/tests/test_agents.py`
  - [x] SubTask 8.2: 重写 `e2e/test_analyze_flow.py` 为 `e2e/test_job_match_flow.py`
  - [x] SubTask 8.3: 更新 `README.md` 项目介绍、运行说明、架构图
  - [x] SubTask 8.4: 检查 Docker Compose 与 CI 配置是否受主题变更影响

- [x] Task 9: 解决数据真实性与爬虫槽点
  - [x] SubTask 9.1: 重写 `backend/app/crawler/scraper.py` 为 `JobScraper`，从公开 RSS 源采集真实 JD
  - [x] SubTask 9.2: 重写 `backend/app/crawler/sources.py` 配置 V2EX/Ruby China/LearnKu 等 JD 源
  - [x] SubTask 9.3: 创建 `backend/scripts/generate_seed_jobs.py` 生成 80 条人工整理的行业典型岗位种子
  - [x] SubTask 9.4: 创建 `backend/data/seed_jobs.json` 作为稳定真实岗位样本
  - [x] SubTask 9.5: 修改 `fetch_real_jobs` 合并 seed + RSS 数据，RSS 优先、种子兜底
  - [x] SubTask 9.6: 更新 `backend/app/data/seed.py` 优先使用真实 JD，不足时生成补充
  - [x] SubTask 9.7: 更新 `README.md` 数据来源说明，诚实标注 seed/RSS/fallback 三层数据
  - [x] SubTask 9.8: 删除旧新闻爬虫残留，确保 `backend/app/crawler/` 只与岗位采集相关

# Task Dependencies

- Task 9 depends on Task 2, Task 3, Task 4, Task 5

- Task 3 depends on Task 2
- Task 4 depends on Task 2
- Task 5 depends on Task 2, Task 3, Task 4
- Task 6 depends on Task 5
- Task 7 depends on Task 6
- Task 8 depends on Task 5, Task 6, Task 7
