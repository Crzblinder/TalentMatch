# 生产可落地性优化 Spec

## Why
当前项目架构骨架和 Agent 链路完善，但距离真正可落地、可复用的开源工程项目仍有显著差距。需要在匹配算法、业务完整度、UX 设计和前端工程化四个维度进行系统性优化，使其成为用户安装配置后即可直接使用的产品。

## What Changes
- 简历上传与解析能力（文件上传 + PDF/DOCX 文本提取 + 结构化解析）
- 技能名称归一化（利用 aliases 字段做模糊匹配，消除同义词问题）
- 匹配算法升级（技能权重、熟练度、经验/学历匹配、软技能区分）
- 岗位智能推荐（给定画像，返回 Top N 最匹配岗位）
- 技能图谱缓存（避免每次请求重建）
- 定时岗位数据抓取（后台定时任务自动采集最新 JD）
- 前端设计系统重构（统一设计 Token、组件规范化、引入 shadcn/ui）
- 新手引导流程（分步向导：创建画像 → 匹配岗位 → 查看结果）
- 岗位收藏功能
- 技能图谱交互升级（缩放、拖拽、点击探索、力导向布局）
- 岗位对比 + 排序 + 导出功能
- 前端页面排版与美感全面优化

## Impact
- Affected specs: N/A (新 spec)
- Affected code: 后端全部 services / agents / routes / models，前端全部 pages / components / styles

---

## ADDED Requirements

### Requirement: 简历上传与解析
系统 SHALL 提供简历文件上传接口，支持 PDF 和 DOCX 格式，自动提取文本并解析为结构化技能画像。

#### Scenario: 用户上传 PDF 简历
- **WHEN** 用户通过 POST `/api/v1/resumes/upload` 上传 PDF 文件
- **THEN** 系统提取文本内容，调用 JD 解析 Agent 识别技能、经验、学历
- **AND** 返回结构化的技能画像预览供用户确认

#### Scenario: 上传不支持的格式
- **WHEN** 用户上传 .txt 或 .jpg 等非 PDF/DOCX 文件
- **THEN** 系统返回 400 错误，提示仅支持 PDF 和 DOCX 格式

### Requirement: 技能名称归一化
系统 SHALL 在匹配时利用技能库的 aliases 字段进行模糊匹配，将用户输入的同义技能名归一化到标准名称。

#### Scenario: 同义词匹配
- **WHEN** 用户输入技能 "Reactjs"，岗位要求 "React"
- **THEN** 系统通过 aliases 匹配将 "Reactjs" 识别为 "React"，算作匹配技能

#### Scenario: 无匹配别名
- **WHEN** 用户输入技能 "MyCustomTool"，技能库中无对应别名
- **THEN** 系统保留原始名称，不计入匹配，标记为未识别技能

### Requirement: 匹配算法升级
系统 SHALL 在匹配时考虑技能权重、熟练度、经验年限和学历，而非仅做集合交集计算。

#### Scenario: 加权匹配计算
- **WHEN** 岗位要求 "Python(核心, 权重0.8)" 和 "Docker(加分, 权重0.4)"
- **THEN** 用户掌握 Python 的得分高于掌握 Docker

#### Scenario: 经验年限匹配
- **WHEN** 用户经验 5 年，岗位要求 3-5 年
- **THEN** 经验匹配度得分较高，反之要求 5-10 年则得分较低

#### Scenario: 学历匹配
- **WHEN** 岗位要求"本科"，用户学历"硕士"
- **THEN** 学历匹配得分满分（高于要求），反之"大专"则得分降低

### Requirement: 岗位智能推荐
系统 SHALL 提供反向匹配接口，给定用户画像 ID，返回按匹配分数降序排列的 Top N 岗位列表。

#### Scenario: 推荐岗位
- **WHEN** 用户通过 GET `/api/v1/profiles/{id}/recommendations?top_n=20` 请求推荐
- **THEN** 系统计算画像与所有岗位的匹配分数，返回 Top 20 结果

#### Scenario: 推荐结果为空
- **WHEN** 岗位库中无任何岗位
- **THEN** 系统返回空列表，message 提示"暂无岗位数据"

### Requirement: 技能图谱缓存
系统 SHALL 在首次构建技能图谱后缓存于内存，后续请求直接复用，避免每次 API 调用重建。

#### Scenario: 缓存命中
- **WHEN** 第二次请求匹配接口
- **THEN** 系统直接使用内存中的图谱缓存，不重新查询数据库

#### Scenario: 缓存失效
- **WHEN** 技能数据发生变更（新增/修改/删除技能或关系）
- **THEN** 缓存自动失效，下次请求时重建

### Requirement: 定时岗位数据采集
系统 SHALL 提供定时任务，定期从公开 RSS 源抓取最新岗位数据并写入数据库。

#### Scenario: 定时采集触发
- **WHEN** 系统启动后，后台定时任务每 6 小时自动执行一次
- **THEN** 采集器从配置的 RSS 源抓取最新 JD，去重后写入数据库

#### Scenario: 采集失败处理
- **WHEN** RSS 源不可达或返回错误
- **THEN** 系统记录警告日志，跳过该源，继续处理下一个源

### Requirement: 前端设计系统
系统前端 SHALL 使用 shadcn/ui 组件库 + Tailwind CSS 重构，统一设计 Token 和组件规范。

#### Scenario: 组件一致性
- **WHEN** 开发者在任意页面使用 Button 组件
- **THEN** 按钮样式、尺寸、交互行为统一，无需手写 CSS

### Requirement: 新手引导流程
系统前端 SHALL 在首次使用时展示分步引导，帮助用户完成画像创建和首次匹配。

#### Scenario: 首次访问
- **WHEN** 用户首次打开应用，无已有画像
- **THEN** 系统展示引导弹窗：Step 1 上传简历/手动输入技能 → Step 2 查看推荐岗位 → Step 3 执行匹配

#### Scenario: 已有画像用户
- **WHEN** 用户已有画像数据
- **THEN** 系统跳过引导，直接进入仪表盘

### Requirement: 岗位收藏
系统 SHALL 允许用户收藏感兴趣的岗位，并提供收藏列表查看和管理。

#### Scenario: 收藏岗位
- **WHEN** 用户在岗位列表或详情页点击收藏按钮
- **THEN** 岗位加入收藏列表，按钮状态变为已收藏

#### Scenario: 取消收藏
- **WHEN** 用户对已收藏岗位再次点击取消收藏
- **THEN** 岗位从收藏列表移除

### Requirement: 技能图谱交互升级
系统前端技能图谱 SHALL 支持缩放、拖拽、点击探索和力导向自动布局。

#### Scenario: 拖拽节点
- **WHEN** 用户拖拽图谱中的技能节点
- **THEN** 节点跟随鼠标移动，连线实时更新

#### Scenario: 点击探索
- **WHEN** 用户点击图谱中的技能节点
- **THEN** 以该节点为中心展开新的关联图谱

#### Scenario: 缩放
- **WHEN** 用户使用滚轮或双指捏合
- **THEN** 图谱整体缩放，保持节点和文字清晰

### Requirement: 岗位对比
系统前端 SHALL 支持选择最多 3 个岗位进行并排对比。

#### Scenario: 对比两个岗位
- **WHEN** 用户在岗位列表选择 2 个岗位并点击"对比"
- **THEN** 系统展示对比面板，并排显示岗位名称、公司、薪资、技能要求、匹配分数

### Requirement: 岗位排序
系统前端岗位列表 SHALL 支持按薪资、发布时间、匹配分数的升序/降序排序。

#### Scenario: 按薪资排序
- **WHEN** 用户点击表格"薪资"列头
- **THEN** 岗位列表按薪资降序重新排列，再次点击切换为升序

### Requirement: 匹配结果导出
系统前端 SHALL 支持将匹配结果导出为 PDF 文件。

#### Scenario: 导出匹配结果
- **WHEN** 用户在匹配结果页点击"导出 PDF"
- **THEN** 系统生成包含匹配分数、技能对比、分析摘要的 PDF 文件并触发下载

---

## MODIFIED Requirements
无（此为全新 spec，不涉及修改已有需求）