# Tasks

- [x] Task 1: 实现后端模糊解析自动判定逻辑
  - [x] SubTask 1.1: 在 `backend/app/services/resume_service.py` 中新增 `should_use_fuzzy_parsing(text: str, content_type: str) -> bool` 静态/模块函数
  - [x] SubTask 1.2: 实现简历判定规则：文本长度、是否存在"在校/项目/实习/应届生/202x届"等关键词、是否缺少明确工作经历分段
  - [x] SubTask 1.3: 实现 JD 判定规则：是否存在"应届生/校招/实习生/接受零基础/经验不限/优秀毕业生"等关键词，或要求描述模糊
  - [x] SubTask 1.4: 在 `backend/app/api/routes.py` 的 `/resumes/upload`、`/resumes/parse`、`/jobs/upload`、`/jobs/parse` 端点将 `fuzzy` 默认值改为自动判定结果；保留显式参数覆盖能力
    - 注：`/resumes/parse` 端点在验证阶段补充实现，以确保简历文本解析同样支持自动判定。
  - [x] SubTask 1.5: 为自动判定函数添加单元测试

- [x] Task 2: 移除前端"应届生模糊识别"手动开关
  - [x] SubTask 2.1: 从 `frontend/src/components/JDUploader.tsx` 中移除 fuzzy Switch 及相关状态
  - [x] SubTask 2.2: 从 `frontend/src/pages/ResumeEditor.tsx` 中移除 fuzzy Switch 及相关状态
  - [x] SubTask 2.3: 检查并清理 `frontend/src/api.ts` 中不再需要的 fuzzy 参数传递（后端已自动判定）

- [x] Task 3: 修复收藏页侧边栏导航高亮
  - [x] SubTask 3.1: 在 `frontend/src/components/Layout.tsx` 中使用 `useLocation` 读取查询参数
  - [x] SubTask 3.2: 当 `pathname === '/jobs' && searchParams.get('favorites') === '1'` 时，将"我的收藏"项标记为 active
  - [x] SubTask 3.3: 确保"/favorites"重定向到"/jobs?favorites=1"后高亮仍然正确

- [x] Task 4: 简历基本信息字段改为选择控件
  - [x] SubTask 4.1: 在 `frontend/src/components/ResumeProfileForm.tsx` 顶部定义常量：性别选项、政治面貌选项、婚姻状况选项、身份证类型选项、省级/城市选项
  - [x] SubTask 4.2: 将 gender 输入框改为 shadcn/ui Select
  - [x] SubTask 4.3: 将 birthDate 输入框改为日期选择器（input type="date" 或 shadcn/ui Calendar/Popover）
  - [x] SubTask 4.4: 将 politicalStatus 输入框改为 Select
  - [x] SubTask 4.5: 在表单中补充 marriage、id_card_type、hukou、jiguan 字段，并均使用 Select
  - [x] SubTask 4.6: 更新 `ProfileFormData` 类型与 `resumeToFormData` / `emptyProfileFormData` 转换函数
  - [x] SubTask 4.7: 调整"基本信息"完成度计算，纳入新增字段

- [x] Task 5: 补充爬虫与岗位数据来源文档
  - [x] SubTask 5.1: 在 `README.md` 中新增"爬虫与岗位数据"章节，说明当前 RSS 源（v2ex_jobs、ruby_china_jobs、learnku 系列）
  - [x] SubTask 5.2: 说明种子数据 `backend/data/seed_jobs.json` 的兜底机制
  - [x] SubTask 5.3: 说明手动触发 `/api/v1/crawler/trigger` 与定时任务 `SCHEDULER_ENABLED` 配置
  - [x] SubTask 5.4: 给出添加新 RSS 源或接入第三方招聘 API 的示例

- [x] Task 6: 浏览器实际验证
  - [x] SubTask 6.1: 启动前后端服务，访问 JD 上传/简历上传页面，确认 fuzzy 开关已移除
  - [x] SubTask 6.2: 上传/解析一份应届生风格简历，确认后端响应中 `fuzzy=true`
  - [x] SubTask 6.3: 上传/解析一份标准社招简历，确认后端响应中 `fuzzy=false`
  - [x] SubTask 6.4: 点击侧边栏"我的收藏"，确认 URL 为 `/jobs?favorites=1` 且"我的收藏"高亮
  - [x] SubTask 6.5: 点击"岗位库"，确认 URL 为 `/jobs` 且"岗位库"高亮
  - [x] SubTask 6.6: 进入简历编辑器/岗位匹配页基本信息页，确认性别、出生日期、政治面貌、婚姻状况、身份证类型、籍贯/户口均为选择控件
  - [x] SubTask 6.7: 运行 `npm run build` 与后端 pytest，确认无新增错误（`test_crawler.py` 既有失败除外）

# Task Dependencies

- Task 2 依赖 Task 1（后端自动判定完成后才能安全移除前端开关）
- Task 6 依赖 Task 1-5
- Task 3、Task 4、Task 5 可并行
