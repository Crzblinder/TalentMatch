# Checklist

## 后端模糊解析自动判定

- [x] `should_use_fuzzy_parsing()` 函数已创建并位于合理模块
- [x] 简历自动判定规则覆盖：短文本、应届生关键词、项目/实习经历、缺失明确工作经历
- [x] JD 自动判定规则覆盖：应届生/校招/实习生/经验不限/优秀毕业生等关键词
- [x] `/resumes/upload`、`/resumes/parse` 默认使用自动判定，且保留 `?fuzzy=` 显式覆盖
- [x] `/jobs/upload`、`/jobs/parse` 默认使用自动判定，且保留 `?fuzzy=` 显式覆盖
- [x] 新增自动判定单元测试并通过

## 前端移除手动 fuzzy 开关

- [x] `JDUploader.tsx` 中无"应届生模糊识别" Switch
- [x] `ResumeEditor.tsx` 中无"应届生模糊识别" Switch
- [x] `api.ts` 中不再向前端页面传递默认 fuzzy 参数（后端自动处理）

## 收藏页导航高亮

- [x] 访问 `/jobs?favorites=1` 时侧边栏"我的收藏"高亮
- [x] 访问 `/jobs` 时侧边栏"岗位库"高亮，"我的收藏"不高亮
- [x] 从 `/favorites` 重定向到 `/jobs?favorites=1` 后高亮正确

## 简历基本信息选择控件

- [x] 性别使用下拉选择（男/女/保密）
- [x] 出生日期使用日期选择器（YYYY-MM-DD）
- [x] 政治面貌使用下拉选择
- [x] 婚姻状况使用下拉选择
- [x] 身份证类型使用下拉选择
- [x] 籍贯/户口使用下拉选择
- [x] 新增字段已同步到 `ProfileFormData`、`resumeToFormData`、`emptyProfileFormData`
- [x] 基本信息完成度计算包含新增字段

## 爬虫与岗位数据文档

- [x] README 或独立文档说明当前 RSS 数据源
- [x] 说明种子数据兜底机制
- [x] 说明手动触发与定时任务配置
- [x] 给出扩展新数据源的示例

## 浏览器验证

- [x] 启动前后端服务无报错
- [x] JD 上传/简历上传页面无 fuzzy 开关
- [x] 应届生风格简历解析响应中 `fuzzy=true`
- [x] 标准社招简历解析响应中 `fuzzy=false`
- [x] 收藏页与岗位库导航高亮切换正确
- [x] 简历基本信息所有枚举字段均为选择控件
- [x] 前端 `npm run build` 成功
- [x] 后端 pytest 通过（除既有 `test_crawler.py` 失败外）
