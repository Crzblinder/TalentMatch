# 全栈重构：舆情风险预警系统 → 岗位技能图谱与人才匹配引擎

## Why

当前项目定位为"企业舆情风险预警"，但业务维度超出个人开发者的资源与行业 know-how 边界：数据依赖 Faker 生成、企业客户场景难以验证、面试中易被质疑真实性与落地性。结合 2026 届毕业生 1270 万、校招岗位仅 567 万、网申重复填写耗时占比 76%、精准投递获约率是海投 8 倍等真实痛点，将项目重构为面向求职者的"岗位技能图谱与人才匹配引擎"，可充分利用现有 FastAPI + LangGraph + Chroma + React 技术栈，同时规避业务边界不清、数据造假、主题同质化等问题。

## What Changes

- **BREAKING** 业务主题从"舆情风险预警"整体迁移为"岗位技能图谱与人才匹配"
- **BREAKING** 后端核心模型重命名：Case → Job，Enterprise → Skill/Company，SentimentEvent → MatchResult/SkillAnalysis
- **BREAKING** LangGraph Agent 重命名并改写业务逻辑：Scanner→JDParser，Matcher→TalentMatcher，Predictor→TrendPredictor，Governance→LearningPlanner，Expert→SkillAdvisor
- **BREAKING** 前端页面重命名与重构：Analyze→JobMatch，Dashboard→SkillDashboard，Cases→JobLibrary，Enterprises→SkillGraph，Evaluation→TrendAnalysis
- **BREAKING** API 路由从 `/api/v1/sentiment/*` 迁移为 `/api/v1/jobs/*`
- 数据层从 Faker 生成舆情/企业数据改为生成结构化真实 JD 样本 + 技能实体 + 技能关系
- RAG 检索目标从"案例"改为"岗位 JD"与"技能知识"
- 保留现有工程底座：FastAPI、LangGraph、Chroma、SQLAlchemy、SSE 流式输出、LLM 双模式（OpenAI/Ollama）及降级机制
- 保留 Docker Compose、GitHub Actions CI、E2E 测试等基础设施

## Impact

- Affected specs: 后端 API、LangGraph 工作流、RAG 检索、数据模型、前端路由与页面、CI 流水线
- Affected code:
  - `backend/app/models/*`
  - `backend/app/agents/*`
  - `backend/app/api/routes.py`
  - `backend/app/services/*`
  - `backend/app/rag/*`
  - `backend/app/data/*`
  - `frontend/src/pages/*`
  - `frontend/src/App.tsx`
  - `frontend/src/api.ts`
  - `frontend/src/components/*`
  - `e2e/*`
  - `README.md`

## ADDED Requirements

### Requirement: 岗位与技能数据模型
The system SHALL provide structured data models for jobs, skills, companies, and skill relationships.

#### Scenario: 成功创建岗位记录
- **WHEN** 系统初始化或用户导入 JD 数据
- **THEN** 数据库中应存在包含 title、company、industry、city、salary_range、required_skills、experience_level、education_level、description 的岗位记录

### Requirement: 技能知识图谱
The system SHALL build a skill knowledge graph capturing dependency, similarity, and co-occurrence relationships between skills.

#### Scenario: 查询技能的关联技能
- **WHEN** 用户请求某技能的关联技能
- **THEN** 系统返回依赖、相似、共现三类关系，并支持按关系类型过滤

### Requirement: JD 智能解析
The system SHALL parse a raw JD into structured fields and extract explicit/implicit skill requirements.

#### Scenario: 解析 JD 文本
- **WHEN** 用户提交一段 JD 文本
- **THEN** 系统返回 JSON 结构化结果，包含技能列表、经验要求、学历要求、隐性需求

### Requirement: 人岗匹配
The system SHALL match a user skill profile against a target job and produce a match score with gap analysis.

#### Scenario: 成功匹配
- **WHEN** 用户选择目标岗位并提交个人技能
- **THEN** 系统返回匹配度分数、缺失技能、可迁移技能、Top3 命中推荐

### Requirement: 学习路径推荐
The system SHALL recommend a learning path for missing skills based on the skill graph shortest path.

#### Scenario: 生成学习路径
- **WHEN** 用户请求针对目标岗位的学习路径
- **THEN** 系统返回按学习顺序排列的技能列表，包含预估难度与推荐资源类型

### Requirement: 岗位趋势分析
The system SHALL analyze aggregated job data to show skill demand trends and job market heat.

#### Scenario: 查看趋势仪表盘
- **WHEN** 用户打开趋势分析页
- **THEN** 系统展示技能热度排行、薪资分布、城市需求分布、时间趋势

## MODIFIED Requirements

### Requirement: LangGraph 多 Agent 工作流
原系统 SHALL orchestrate 5 agents for sentiment risk analysis. 重构后 SHALL orchestrate 5 agents for JD parsing, talent matching, trend prediction, learning planning, and skill advising. 工作流编排结构、SSE 流式输出、LLM 降级机制保持不变。

### Requirement: RAG 混合检索
原系统 SHALL retrieve historical sentiment cases. 重构后 SHALL retrieve job JDs and skill knowledge snippets using the same hybrid (keyword + vector) retrieval architecture.

### Requirement: 前端页面导航
原系统 SHALL provide Dashboard / Analyze / Cases / Enterprises / Evaluation pages. 重构后 SHALL provide SkillDashboard / JobLibrary / SkillGraph / JobMatch / TrendAnalysis pages，菜单文案与路由同步更新。

## REMOVED Requirements

### Requirement: 舆情风险相关数据与算法
**Reason**: 业务主题变更，舆情风险扫描、情感分析、风险等级预测不再适用。
**Migration**: 用岗位解析、技能分析、趋势预测替代。原 `sentiment` 相关模型、表、API 全部移除。

### Requirement: 企业风险画像
**Reason**: 企业画像与风险治理逻辑不再匹配新主题。
**Migration**: 保留"公司"作为岗位归属实体，移除风险指标与治理方案相关字段和逻辑。
