# Tasks

## Phase 1: 后端基础设施 (P0)

- [x] Task 1: 简历上传与解析 API
  - [x] 添加 `python-docx` 和 `PyPDF2` 依赖到 requirements.txt
  - [x] 创建 `backend/app/services/resume_service.py`：解析 PDF/DOCX 文本提取
  - [x] 在 `routes.py` 添加 `POST /api/v1/resumes/upload` 端点
  - [x] 在 `schemas.py` 添加 `ResumeUploadResponse` schema
  - [x] 上传后自动调用 JDParser 提取技能，返回结构化画像预览

- [x] Task 2: 技能名称归一化
  - [x] 在 `backend/app/services/skill_service.py` 添加 `normalize_skill_name()` 方法
  - [x] 利用 `Skill.aliases` 字段构建别名→标准名映射表
  - [x] 修改 `TalentMatcher.match()` 在匹配前先做技能名归一化
  - [x] 修改 `MatchingService.match_profile_to_job()` 用户输入技能也做归一化

- [x] Task 3: 匹配算法升级
  - [x] 在 `backend/app/models/job.py` 的 `required_skills` 字段中支持结构化技能（含权重标记）
  - [x] 修改 `TalentMatcher._compute_score()` 加入技能权重因子
  - [x] 添加经验年限匹配计算（用户经验 vs 岗位要求）
  - [x] 添加学历匹配计算
  - [x] 添加软技能/硬技能区分处理
  - [x] 修改 `MatchResult` 模型增加 `experience_match` 和 `education_match` 字段

## Phase 2: 后端业务增强 (P1)

- [x] Task 4: 岗位智能推荐 API
  - [x] 在 `backend/app/services/matching_service.py` 添加 `recommend_jobs()` 方法
  - [x] 在 `routes.py` 添加 `GET /api/v1/profiles/{id}/recommendations` 端点
  - [x] 在 `schemas.py` 添加 `JobRecommendationOut` 包含匹配分数和岗位信息
  - [x] 支持 `top_n` 参数控制返回数量，默认 20

- [x] Task 5: 技能图谱缓存
  - [x] 在 `backend/app/graph/skill_graph.py` 添加内存缓存层（模块级 dict）
  - [x] 添加 `get_cached_graph()` 和 `invalidate_cache()` 函数
  - [x] 修改所有调用 `build_graph_from_db()` 的地方改为使用缓存版本
  - [x] 在 `SkillService` 技能变更时触发缓存失效

- [x] Task 6: 定时岗位数据采集
  - [x] 添加 `apscheduler` 依赖到 requirements.txt
  - [x] 创建 `backend/app/scheduler.py` 配置定时任务
  - [x] 在 `main.py` 的 lifespan 中启动调度器
  - [x] 添加 `SCHEDULER_ENABLED` 和 `FETCH_INTERVAL_HOURS` 配置项
  - [x] 添加 `POST /api/v1/crawler/trigger` 手动触发采集端点

## Phase 3: 前端设计系统重构 (P1)

- [x] Task 7: 前端工程化升级
  - [x] 初始化 Tailwind CSS + shadcn/ui 项目结构
  - [x] 配置 shadcn/ui 主题（颜色、圆角、阴影 token）
  - [x] 安装所需 shadcn/ui 组件（Button, Card, Input, Select, Table, Dialog, Tabs, Badge, Sheet, Tooltip, Skeleton, Toast, Command, ScrollArea, Separator, Accordion, Slider, Switch, Label, Textarea, DropdownMenu, Popover, Alert, AspectRatio, Avatar, Breadcrumb, Calendar, Carousel, Checkbox, Collapsible, ContextMenu, Drawer, HoverCard, InputOTP, Menubar, NavigationMenu, Pagination, Progress, RadioGroup, Resizable, ScrollArea, Sonner, Toggle, ToggleGroup）
  - [x] 删除旧 `index.css` 中与 Tailwind 冲突的样式
  - [x] 迁移全局布局（Sidebar + Main）到 Tailwind + shadcn/ui

- [x] Task 8: 仪表盘页面重构
  - [x] 使用 shadcn/ui Card 组件重构统计卡片
  - [x] 优化信息层级：核心指标突出，次要信息折叠
  - [x] 使用 Skeleton 组件替代"加载中..."文字
  - [x] 空状态使用 EmptyState 组件 + CTA 引导

- [x] Task 9: 岗位匹配页面重构
  - [x] 添加步骤指示器（Stepper）组件
  - [x] 画像输入区使用 shadcn/ui Input/Textarea/Select
  - [x] 岗位选择改为可排序表格 + 搜索
  - [x] 匹配结果卡片使用设计系统卡片，分数更突出
  - [x] 技能对比雷达图样式优化

- [x] Task 10: 岗位库页面重构
  - [x] 表格支持列头点击排序（薪资、时间、匹配分数）
  - [x] 使用 shadcn/ui Table 组件
  - [x] 抽屉面板改为 Sheet 组件
  - [x] 岗位详情展示优化（标签、布局）

- [x] Task 11: 趋势分析 + 技能图谱页面重构
  - [x] 趋势分析页图表区域使用 shadcn/ui Card 包裹
  - [x] 技能图谱页交互升级：使用 D3.js 力导向布局替代静态 SVG 圆形布局
  - [x] 添加缩放、拖拽、节点点击探索功能
  - [x] 添加图谱图例和工具栏

## Phase 4: 前端业务增强 (P2)

- [x] Task 12: 新手引导流程
  - [x] 创建 `OnboardingDialog` 组件（分步引导弹窗）
  - [x] Step 1：上传简历或手动输入技能
  - [x] Step 2：查看推荐岗位列表
  - [x] Step 3：选择岗位执行匹配
  - [x] 使用 localStorage 记录是否已完成引导

- [x] Task 13: 岗位收藏功能
  - [x] 后端：创建 `favorite_jobs` 表（关联 profile_id + job_id）
  - [x] 后端：添加 `POST/DELETE /api/v1/profiles/{id}/favorites` 和 `GET /api/v1/profiles/{id}/favorites` 端点
  - [x] 前端：岗位卡片/列表中添加收藏按钮（心形图标）
  - [x] 前端：添加收藏列表页面入口

- [x] Task 14: 岗位对比功能
  - [x] 创建 `JobCompareSheet` 组件
  - [x] 支持选择最多 3 个岗位并排展示
  - [x] 对比维度：岗位名称、公司、薪资、城市、技能要求、经验、学历、匹配分数
  - [x] 岗位列表添加复选框和"对比选中"按钮

- [x] Task 15: 匹配结果导出
  - [x] 添加 `jspdf` 和 `html2canvas` 依赖到前端
  - [x] 创建 `ExportPDFButton` 组件
  - [x] 生成包含匹配分数、技能对比、分析摘要的 PDF
  - [x] 在匹配结果面板添加导出按钮

- [x] Task 16: 修复 JobService 对结构化技能格式的兼容性问题
  - [x] 定位 `backend/app/services/job_service.py` 中使用 `required_skills` 的地方
  - [x] 使用 `parse_required_skills()` 将结构化技能统一转换为字符串名称
  - [x] 验证仪表盘等调用不再因 dict 类型 skill 报错

# Task Dependencies

- [Task 16] depends on [Task 3]

```
Phase 1 (后端基础设施)
├── Task 1 (简历上传) ──────────── 无依赖，可并行
├── Task 2 (技能归一化) ───────── 无依赖，可并行
└── Task 3 (匹配算法升级) ──────── 依赖 Task 2

Phase 2 (后端业务增强)
├── Task 4 (岗位推荐) ──────────── 依赖 Task 3
├── Task 5 (图谱缓存) ──────────── 无依赖，可并行
└── Task 6 (定时采集) ──────────── 无依赖，可并行

Phase 3 (前端设计系统重构)
└── Task 7 (工程化升级) ────────── 无依赖，先做
    ├── Task 8 (仪表盘重构) ────── 依赖 Task 7
    ├── Task 9 (匹配页重构) ────── 依赖 Task 7
    ├── Task 10 (岗位库重构) ───── 依赖 Task 7
    └── Task 11 (趋势+图谱重构) ── 依赖 Task 7

Phase 4 (前端业务增强)
├── Task 12 (新手引导) ─────────── 依赖 Task 7, 8, 9
├── Task 13 (岗位收藏) ─────────── 依赖 Task 7, 10
├── Task 14 (岗位对比) ─────────── 依赖 Task 7, 10
└── Task 15 (结果导出) ─────────── 依赖 Task 7, 9
```
