# 模糊解析自动判定、导航高亮与表单选择框优化 Spec

## Why

用户反馈当前实现与预期存在偏差：
1. **模糊解析不应是手动开关**：需求是"在解析简历和岗位 JD 的时候根据实际内容自动判断是否启用模糊解析"，而不是在前端放一个"应届生模糊识别"开关让用户手动选择。
2. **收藏页导航高亮错误**：点击"我的收藏"后 URL 变为 `/jobs?favorites=1`，但侧边栏高亮的是"岗位库"而非"我的收藏"。
3. **表单字段应是选择框**：简历基本信息中的性别、出生日期、政治面貌、婚姻状况、身份证类型、籍贯/户口等枚举类字段仍使用文本输入，应改为下拉选择或日期选择器。
4. **爬虫与岗位数据来源不清晰**：需要明确当前真实岗位数据从哪里来、如何扩展、如何在本地获取。

本 Spec 聚焦修复上述 UX 与逻辑问题，并在浏览器中实际验证通过后再交付。

## What Changes

- **后端**：新增 `should_use_fuzzy_parsing(text: str, content_type: "resume" | "jd") -> bool` 自动判定函数，根据内容特征自动决定是否启用 fuzzy 解析。
- **后端**：在 `/resumes/upload`、`/resumes/parse`、`/jobs/upload`、`/jobs/parse` 端点默认使用自动判定；保留 `fuzzy` 查询参数作为显式覆盖开关（供高级场景）。
- **前端**：移除 `JDUploader`、`ResumeEditor` 等页面上的"应届生模糊识别"手动 Switch。
- **前端**：修复 `Layout.tsx` 导航高亮逻辑，使 `/jobs?favorites=1` 正确高亮"我的收藏"。
- **前端**：重构 `ResumeProfileForm` 基本信息页，将枚举字段改为 shadcn/ui Select 或日期选择器。
- **文档**：补充 `README.md` 或新增 `docs/crawler.md`，说明爬虫数据源、种子数据与扩展方式。

## Impact

- 受影响页面：简历编辑器、JD 上传器、岗位库/收藏页、简历表单。
- 受影响后端：解析服务、路由参数默认值。
- 不影响：匹配算法、数据库 Schema、技能图谱核心逻辑。

## ADDED Requirements

### Requirement: 简历/JD 模糊解析自动判定

The system SHALL automatically determine whether to enable fuzzy parsing based on the uploaded/pasted content, without requiring the user to manually toggle a switch.

#### Scenario: 标准清晰的简历
- **WHEN** 用户上传一份结构清晰、工作经历完整、分段明确的简历
- **THEN** 系统使用默认解析器，`fuzzy=false`

#### Scenario: 应届生/内容边界不清的简历
- **WHEN** 简历文本短、缺少明确工作经历、充斥"在校""项目""实习""应届生""202x届"等关键词，或段落边界模糊
- **THEN** 系统自动启用 fuzzy 解析，`fuzzy=true`

#### Scenario: 标准 JD
- **WHEN** 岗位描述结构完整、要求明确
- **THEN** 系统使用默认解析器，`fuzzy=false`

#### Scenario: 隐含门槛/应届生友好的 JD
- **WHEN** JD 中出现"应届生""校招""实习生""接受零基础""经验不限""优秀毕业生"等关键词，或要求描述模糊
- **THEN** 系统自动启用 fuzzy 解析，`fuzzy=true`

#### Scenario: 显式覆盖
- **WHEN** API 调用者显式传入 `?fuzzy=true` 或 `?fuzzy=false`
- **THEN** 以显式参数为准，跳过自动判定

### Requirement: 收藏页导航高亮正确

The system SHALL highlight the correct sidebar navigation item when the user is viewing their favorite jobs.

#### Scenario: 查看我的收藏
- **WHEN** URL 为 `/jobs?favorites=1` 或 `/favorites`
- **THEN** 侧边栏"我的收藏"项高亮，"岗位库"项不高亮

#### Scenario: 浏览岗位库
- **WHEN** URL 为 `/jobs` 且无 `favorites=1` 参数
- **THEN** 侧边栏"岗位库"项高亮，"我的收藏"项不高亮

### Requirement: 简历基本信息字段使用选择控件

The system SHALL provide selection controls for enumerated personal information fields in the resume basic info form.

#### Scenario: 编辑性别
- **WHEN** 用户编辑性别
- **THEN** 使用下拉选择：男、女、保密

#### Scenario: 编辑出生日期
- **WHEN** 用户编辑出生日期
- **THEN** 使用日期选择器，格式为 YYYY-MM-DD

#### Scenario: 编辑政治面貌
- **WHEN** 用户编辑政治面貌
- **THEN** 使用下拉选择：中共党员、中共预备党员、共青团员、群众、民主党派、无党派人士

#### Scenario: 编辑婚姻状况
- **WHEN** 用户编辑婚姻状况
- **THEN** 使用下拉选择：未婚、已婚、保密

#### Scenario: 编辑身份证类型
- **WHEN** 用户编辑身份证类型
- **THEN** 使用下拉选择：居民身份证、护照、港澳居民来往内地通行证、台湾居民来往大陆通行证、其他

#### Scenario: 编辑籍贯/户口
- **WHEN** 用户编辑籍贯或户口所在地
- **THEN** 使用下拉选择（省级或常见城市列表），避免自由文本

### Requirement: 爬虫与岗位数据来源说明

The system SHALL provide clear documentation on how real job data is obtained and how to extend data sources.

#### Scenario: 开发者查看数据源
- **WHEN** 开发者查看 README 或爬虫文档
- **THEN** 能看到：当前使用的公开 RSS 源列表、种子数据机制、定时/手动触发方式、以及如何添加新的 RSS/API 源

## MODIFIED Requirements

无原有需求的破坏性修改；仅将手动 fuzzy 开关改为自动判定，并保留参数覆盖能力。

## REMOVED Requirements

### Requirement: 前端"应届生模糊识别"手动 Switch
- **Reason**: 与"根据实际内容自动判断"的需求冲突。
- **Migration**: 移除 UI 开关；后端自动判定；如调试需要，可通过 API 显式 `?fuzzy=true/false` 覆盖。
