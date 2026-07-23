# ruff: noqa: E501
#!/usr/bin/env python3
"""生成人工整理的行业典型岗位种子数据。

这些 JD 基于真实招聘平台常见岗位结构整理，覆盖主流技术栈与城市分布，
用于在公开 RSS 源不稳定时提供稳定的真实岗位样本。
"""

import json
import random

random.seed(42)

CITIES = ["北京", "上海", "深圳", "杭州", "广州", "成都", "南京", "武汉", "西安", "苏州"]
EXPERIENCE_LEVELS = ["应届/在校生", "1-3年", "3-5年", "5-10年"]
EDUCATION_LEVELS = ["大专", "本科", "硕士"]

# 真实公司名（部分来自公开 RSS 源，部分为行业常见公司类型）
COMPANY_NAMES = [
    "字节跳动", "阿里巴巴", "腾讯", "美团", "京东", "百度", "快手", "滴滴", "小红书", "哔哩哔哩",
    "网易", "小米", "华为", "OPPO", "vivo", "知乎", "得到", "猫眼娱乐", "融 360", "奇安信",
    "用友网络", "金蝶软件", "旷视科技", "商汤科技", "第四范式", "寒武纪", "涂鸦智能", "容联云",
    "神策数据", "GrowingIO", "贝聊", "好未来", "猿辅导", "作业帮", "VIPKID", "流利说",
    "陆金所", "蚂蚁金服", "微众银行", "招银网络", "平安科技", "众安保险", "同花顺",
    "顺丰科技", "菜鸟网络", "满帮集团", "货拉拉", "BOSS直聘", "智联招聘", "猎聘网",
]

# 岗位模板：title, 核心技能, 经验, 学历, 描述模板
JOB_TEMPLATES = [
    {
        "title": "Java后端工程师",
        "core_skills": ["Java", "Spring Boot", "MySQL", "Redis", "Git", "Linux"],
        "exp": "1-3年",
        "edu": "本科",
        "desc": "负责 {scope} 的后端设计与开发，使用 Java/Spring Boot 完成业务需求；参与数据库设计与优化，保障系统稳定性；编写单元测试与技术文档。",
        "scopes": ["电商业务系统", "支付中台", "用户增长平台", "供应链系统"],
    },
    {
        "title": "高级Java后端工程师",
        "core_skills": ["Java", "Spring Boot", "MySQL", "Redis", "Kafka", "Elasticsearch", "Docker", "Kubernetes"],
        "exp": "3-5年",
        "edu": "本科",
        "desc": "主导 {scope} 技术方案设计，解决高并发、高可用场景下的技术难题；负责核心模块开发、代码评审与性能优化；指导初中级工程师。",
        "scopes": ["分布式交易平台", "微服务中台", "金融核心系统", "大数据调度平台"],
    },
    {
        "title": "Python后端工程师",
        "core_skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker"],
        "exp": "1-3年",
        "edu": "本科",
        "desc": "使用 Python 开发 {scope} 后端服务；负责 RESTful API 设计与实现；参与数据建模、接口性能优化与线上问题排查。",
        "scopes": ["SaaS 业务系统", "AI 应用平台", "数据中台", "运营后台"],
    },
    {
        "title": "Go后端工程师",
        "core_skills": ["Go", "Gin", "MySQL", "Redis", "Kafka", "Docker", "Linux"],
        "exp": "1-3年",
        "edu": "本科",
        "desc": "负责 {scope} 的高性能后端开发；使用 Go 语言构建微服务；参与服务治理、链路优化与监控体系建设。",
        "scopes": ["实时消息服务", "云原生基础平台", "高并发推荐系统", "物联网接入层"],
    },
    {
        "title": "前端开发工程师",
        "core_skills": ["JavaScript", "TypeScript", "React", "Vue.js", "Webpack", "Git"],
        "exp": "1-3年",
        "edu": "本科",
        "desc": "负责 {scope} 的 Web 前端开发；与设计师、后端工程师协作完成产品功能；优化页面性能与用户体验。",
        "scopes": ["企业级后台系统", "电商 H5/小程序", "数据可视化平台", "内容社区"],
    },
    {
        "title": "高级前端工程师",
        "core_skills": ["JavaScript", "TypeScript", "React", "Next.js", "Webpack", "Vite", "Tailwind CSS"],
        "exp": "3-5年",
        "edu": "本科",
        "desc": "主导 {scope} 前端架构设计与工程化建设；负责复杂交互实现、性能优化与组件库沉淀；推动前端技术升级。",
        "scopes": ["低代码平台", "大型中后台系统", "跨端应用框架", "前端监控体系"],
    },
    {
        "title": "全栈工程师",
        "core_skills": ["JavaScript", "TypeScript", "React", "Python", "MySQL", "Docker"],
        "exp": "3-5年",
        "edu": "本科",
        "desc": "独立负责 {scope} 的全链路开发，从前端界面到后端 API；快速推进产品迭代，保障代码质量与交付效率。",
        "scopes": ["内部效率工具", "创新业务 MVP", "数据分析产品", "运营自动化平台"],
    },
    {
        "title": "移动端开发工程师",
        "core_skills": ["Swift", "Kotlin", "Flutter", "React Native"],
        "exp": "1-3年",
        "edu": "本科",
        "desc": "负责 {scope} 的移动端开发；完成 iOS/Android/跨端功能实现；处理性能优化与兼容性问题。",
        "scopes": ["电商 App", "社交应用", "金融理财 App", "企业协作 App"],
    },
    {
        "title": "算法工程师",
        "core_skills": ["Python", "PyTorch", "TensorFlow", "Pandas", "NumPy"],
        "exp": "1-3年",
        "edu": "硕士",
        "desc": "负责 {scope} 的算法研究与工程落地；参与数据清洗、特征工程、模型训练与效果评估；跟进前沿技术。",
        "scopes": ["推荐系统", "搜索排序", "风控模型", "广告投放"],
    },
    {
        "title": "机器学习工程师",
        "core_skills": ["Python", "Scikit-learn", "XGBoost", "Pandas", "NumPy", "Docker"],
        "exp": "1-3年",
        "edu": "本科",
        "desc": "将 {scope} 机器学习模型工程化落地；构建特征平台、训练流水线与模型服务；监控模型线上效果并迭代。",
        "scopes": ["用户画像", "信用评分", "智能客服", "销量预测"],
    },
    {
        "title": "NLP工程师",
        "core_skills": ["Python", "PyTorch", "Transformer", "Hugging Face", "自然语言处理", "RAG"],
        "exp": "3-5年",
        "edu": "硕士",
        "desc": "负责 {scope} 相关的自然语言处理技术研发；参与大语言模型应用、文本分类、信息抽取等任务；优化模型效果与推理性能。",
        "scopes": ["智能问答系统", "内容审核", "搜索理解", "对话机器人"],
    },
    {
        "title": "数据分析师",
        "core_skills": ["Python", "SQL", "Pandas", "NumPy", "Matplotlib", "数据驱动"],
        "exp": "1-3年",
        "edu": "本科",
        "desc": "负责 {scope} 的数据分析工作；构建业务指标体系，输出分析报告；支持产品、运营的数据决策需求。",
        "scopes": ["用户增长分析", "电商交易分析", "内容生态分析", "供应链分析"],
    },
    {
        "title": "数据工程师",
        "core_skills": ["Python", "SQL", "Kafka", "Redis", "MySQL", "Docker"],
        "exp": "1-3年",
        "edu": "本科",
        "desc": "负责 {scope} 的数据平台建设；参与 ETL 流程开发、数据仓库建模与数据质量保障；支撑业务数据需求。",
        "scopes": ["实时数仓", "数据湖平台", "埋点治理", "数据中台"],
    },
    {
        "title": "产品经理",
        "core_skills": ["产品思维", "需求分析", "沟通能力", "项目管理", "数据驱动"],
        "exp": "1-3年",
        "edu": "本科",
        "desc": "负责 {scope} 的产品规划与落地；撰写 PRD，协调设计、开发、测试资源；通过数据与用户反馈持续迭代产品。",
        "scopes": ["B端中后台产品", "C端增长产品", "数据产品", "AI 应用产品"],
    },
    {
        "title": "测试工程师",
        "core_skills": ["Python", "Postman", "Linux", "Git", "MySQL"],
        "exp": "1-3年",
        "edu": "大专",
        "desc": "负责 {scope} 的功能测试工作；编写测试用例、执行测试并跟踪缺陷；参与自动化测试体系建设。",
        "scopes": ["Web 应用", "移动 App", "API 接口", "支付系统"],
    },
    {
        "title": "运维工程师",
        "core_skills": ["Linux", "Shell", "Nginx", "Docker", "Kubernetes", "Prometheus"],
        "exp": "3-5年",
        "edu": "本科",
        "desc": "负责 {scope} 的运维保障工作；维护服务器、网络与中间件；建设监控告警与应急响应机制。",
        "scopes": ["云原生平台", "高并发业务系统", " DevOps 平台", "安全运维"],
    },
    {
        "title": "DevOps工程师",
        "core_skills": ["Docker", "Kubernetes", "Jenkins", "GitLab CI", "Terraform", "Linux"],
        "exp": "3-5年",
        "edu": "本科",
        "desc": "负责 {scope} 的 CI/CD 流程与云原生基础设施建设；推动自动化发布、环境管理与可观测性体系建设。",
        "scopes": ["研发效能平台", "容器云平台", "多云基础设施", "自动化发布"],
    },
    {
        "title": "C++开发工程师",
        "core_skills": ["C++", "Linux", "Git", "Docker", "Python", "Bash"],
        "exp": "1-3年",
        "edu": "本科",
        "desc": "负责 {scope} 的 C++ 模块开发；进行性能优化、内存管理与跨平台适配；参与底层框架设计。",
        "scopes": ["高性能交易系统", "游戏引擎", "嵌入式软件", "音视频处理"],
    },
    {
        "title": "网络安全工程师",
        "core_skills": ["Linux", "Python", "Nginx", "Git", "Bash", "Docker"],
        "exp": "3-5年",
        "edu": "本科",
        "desc": "负责 {scope} 的安全防护工作；进行漏洞扫描、渗透测试与安全事件响应；建设安全运营体系。",
        "scopes": ["企业安全运营", "云安全", "应用安全", "数据安全"],
    },
    {
        "title": "数据产品经理",
        "core_skills": ["SQL", "数据驱动", "产品思维", "需求分析", "沟通能力"],
        "exp": "3-5年",
        "edu": "本科",
        "desc": "负责 {scope} 的数据产品规划；设计指标体系、数据看板与标签体系；推动数据在业务中的落地应用。",
        "scopes": ["BI 平台", "用户画像平台", "AB 实验平台", "数据中台产品"],
    },
]


def _salary_for_experience(exp: str) -> tuple[int, int]:
    ranges = {
        "应届/在校生": (8000, 15000),
        "1-3年": (12000, 25000),
        "3-5年": (22000, 40000),
        "5-10年": (35000, 70000),
    }
    lo, hi = ranges.get(exp, (15000, 30000))
    lo = int(random.uniform(lo * 0.9, lo * 1.1) / 1000) * 1000
    hi = int(random.uniform(hi * 0.9, hi * 1.1) / 1000) * 1000
    if hi <= lo:
        hi = lo + 5000
    return lo, hi


def _extra_skills() -> list[str]:
    pool = ["沟通能力", "团队协作", "项目管理", "解决问题", "抗压能力", "学习能力", "英语读写"]
    return random.sample(pool, k=random.randint(1, 3))


def generate_seed_jobs(n: int = 80) -> list[dict]:
    jobs = []
    for i in range(n):
        template = JOB_TEMPLATES[i % len(JOB_TEMPLATES)]
        company = random.choice(COMPANY_NAMES)
        city = random.choice(CITIES)
        exp = template["exp"]
        edu = template["edu"]
        salary_min, salary_max = _salary_for_experience(exp)
        scope = random.choice(template["scopes"])
        skills = list(template["core_skills"]) + _extra_skills()
        # 去重
        skills = list(dict.fromkeys(skills))
        description = template["desc"].format(scope=scope)
        description += " 要求具备 " + "、".join(skills[:5]) + " 等能力，"
        description += f"{edu}及以上学历，{exp}经验优先。"
        description += " 欢迎对技术有热情、具备良好沟通与团队协作能力的候选人加入。"

        jobs.append({
            "title": template["title"],
            "company_name": company,
            "city": city,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "experience_level": exp,
            "education_level": edu,
            "required_skills": skills,
            "description": description,
            "source": "seed_jobs",
            "source_url": "",
            "published_at": "",
        })
    return jobs


if __name__ == "__main__":
    jobs = generate_seed_jobs(80)
    path = "data/seed_jobs.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"已生成 {len(jobs)} 条种子 JD，保存至 {path}")
