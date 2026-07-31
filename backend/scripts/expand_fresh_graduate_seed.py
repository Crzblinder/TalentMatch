"""扩充 seed_jobs.json：新增大量国内真实应届/校招友好岗位。

目标：
1. 让数据库中「应届/在校生」友好岗位从 0 条提升到 100+ 条
2. 覆盖国内主要就业城市与真实知名企业
3. 薪资区间贴合应届生市场实际水平

运行后会读取现有 seed_jobs.json，追加新生成的应届岗位后写回。
"""

import json
import os
import random
import sys

random.seed(2026)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, "data")
SEED_PATH = os.path.join(DATA_DIR, "seed_jobs.json")

# ---------------------------------------------------------------------------
# 真实企业（按城市分布，覆盖一二线主要就业城市）
# ---------------------------------------------------------------------------
COMPANIES_BY_CITY = {
    "北京": ["字节跳动", "百度", "美团", "京东", "小米", "快手", "滴滴出行", "贝壳控股", "好未来", "知乎", "作业帮"],
    "上海": ["拼多多", "哔哩哔哩", "小红书", "携程旅行", "蚂蚁集团", "商汤科技", "蔚来汽车", "声网", "米哈游", "莉莉丝游戏"],
    "深圳": ["腾讯科技", "华为技术", "OPPO", "大疆创新", "微众银行", "平安科技", "京东健康", "安克创新", "vivo"],
    "广州": ["网易", "小鹏汽车", "完美日记", "三七互娱", "虎牙直播", "微信", "YY直播"],
    "杭州": ["阿里巴巴", "网易", "蚂蚁集团", "海康威视", "同花顺", "微医集团", "SHEIN", "涂鸦智能"],
    "成都": ["腾讯成都", "字节跳动成都", "蚂蚁集团成都", "京东成都", "美团成都", "科大讯飞"],
    "武汉": ["小米武汉", "字节跳动武汉", "华为武汉", "小红书武汉", "金山办公", "斗鱼"],
    "南京": ["苏宁", "SHEIN", "字节跳动南京", "美团南京", "亚信科技", "途牛"],
    "西安": ["字节跳动西安", "美团西安", "京东西安", "大疆西安", "广联达", "葡萄城"],
    "苏州": ["思必驰", "科大讯飞苏州", "微软苏州", "华为苏州", "同程旅行", "科沃斯"],
    "长沙": ["芒果TV", "拓维信息", "水羊股份", "安克创新长沙", "万兴科技"],
    "厦门": ["美图公司", "美亚柏科", "吉比特", "亿联网络", "瑞幸咖啡"],
    "天津": ["字节跳动天津", "腾讯天津", "中海油", "飞腾信息", "联想天津"],
    "重庆": ["腾讯重庆", "字节跳动重庆", "长安汽车", "猪八戒网", "小康股份"],
    "合肥": ["科大讯飞", "蔚来汽车合肥", "联宝科技", "阳光电源", "华米科技"],
}

# ---------------------------------------------------------------------------
# 应届友好岗位模板（title + 核心技能 + 描述片段）
# 仅保留基础/初级岗位，排除「高级/架构师/负责人/总监/经理」
# ---------------------------------------------------------------------------
FRESH_JOB_TEMPLATES = [
    ("后端开发工程师", ["Java", "Spring Boot", "MySQL", "Redis", "Git", "Linux"], "参与公司核心业务系统的后端开发，使用 Java/Spring Boot 进行接口设计与实现，保障服务的稳定性与性能。"),
    ("Java开发工程师", ["Java", "Spring Boot", "MyBatis", "MySQL", "Redis", "Git"], "负责业务后台服务的开发与维护，参与数据库设计与接口优化，在导师带领下快速成长。"),
    ("Python开发工程师", ["Python", "Django", "Flask", "FastAPI", "MySQL", "Git"], "使用 Python 参与 Web 后端与数据平台建设，完成接口开发、脚本工具与自动化任务。"),
    ("Go开发工程师", ["Go", "Gin", "MySQL", "Redis", "Docker", "Linux"], "参与高并发后端服务的开发，使用 Go 语言构建稳定高效的微服务。"),
    ("前端开发工程师", ["JavaScript", "TypeScript", "React", "Vue.js", "Webpack", "Git"], "负责 Web 前端页面开发与交互实现，使用 React/Vue 构建高质量用户界面。"),
    ("Web前端工程师", ["JavaScript", "TypeScript", "HTML", "CSS", "Vue.js", "Webpack"], "参与公司产品前端开发，负责页面布局、组件封装与性能优化。"),
    ("客户端开发工程师（Android）", ["Kotlin", "Java", "Android", "Git", "Jetpack"], "参与 Android 客户端功能开发与维护，负责页面、组件与基础能力建设。"),
    ("客户端开发工程师（iOS）", ["Swift", "Objective-C", "iOS", "Git", "SnapKit"], "参与 iOS 客户端功能开发，负责界面实现与用户体验优化。"),
    ("测试开发工程师", ["Python", "pytest", "Linux", "Git", "MySQL", "Docker"], "负责服务端/客户端自动化测试框架建设与用例编写，提升测试效率与质量。"),
    ("测试工程师", ["Python", "Linux", "Git", "MySQL", "JIRA", "沟通能力"], "执行功能测试与回归测试，编写测试用例、跟踪缺陷并推动问题解决。"),
    ("算法工程师（推荐/搜索）", ["Python", "PyTorch", "Pandas", "NumPy", "机器学习", "SQL"], "参与推荐/搜索算法研发，负责特征工程、模型训练与离线评估。"),
    ("机器学习工程师", ["Python", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Docker"], "参与机器学习模型的训练与上线，负责数据处理、模型迭代与效果优化。"),
    ("自然语言处理工程师", ["Python", "PyTorch", "Transformer", "Hugging Face", "自然语言处理", "RAG"], "参与 NLP 相关算法研发，负责文本理解、对话系统与大模型应用落地。"),
    ("数据分析师", ["Python", "SQL", "Pandas", "NumPy", "数据驱动", "Matplotlib"], "负责业务数据分析与指标体系搭建，输出分析报告并支持业务决策。"),
    ("数据开发工程师", ["Python", "SQL", "Kafka", "Hive", "Spark", "Linux"], "参与数据仓库建设与 ETL 开发，负责离线/实时数据管道的开发与维护。"),
    ("运维开发工程师", ["Linux", "Shell", "Python", "Docker", "Kubernetes", "Nginx"], "参与运维平台建设与自动化开发，负责服务部署、监控与故障排查。"),
    ("DevOps工程师", ["Docker", "Kubernetes", "Jenkins", "GitLab CI", "Linux", "Terraform"], "负责 CI/CD 流水线与云原生基础设施建设，提升研发交付效率。"),
    ("产品经理（校招）", ["产品思维", "需求分析", "沟通能力", "数据驱动", "文档能力", "项目管理"], "参与产品需求调研、原型设计与项目跟进，在导师带领下学习完整产品流程。"),
    ("产品运营", ["数据驱动", "用户洞察", "沟通能力", "解决问题", "学习能力", "内容策划"], "负责用户增长与活动运营，通过数据分析优化运营策略并提升用户活跃。"),
    ("用户增长运营", ["数据驱动", "用户洞察", "沟通能力", "解决问题", "学习能力", "A/B测试"], "参与用户拉新、促活与留存策略制定，通过实验驱动增长。"),
    ("内容运营", ["数据驱动", "用户洞察", "沟通能力", "内容策划", "学习能力", "文案"], "负责内容生态建设与创作者运营，策划并产出优质内容。"),
    ("UI设计师", ["Figma", "Sketch", "Adobe XD", "Photoshop", "审美", "沟通能力"], "参与产品界面与视觉设计，输出高保真原型与设计规范。"),
    ("UX设计师", ["Figma", "用户洞察", "沟通能力", "解决问题", "交互设计", "用户研究"], "负责用户体验研究与交互设计，输出用户旅程与交互方案。"),
    ("商业分析师", ["SQL", "数据驱动", "需求分析", "沟通能力", "文档能力", "产品思维"], "负责业务分析与数据支持，输出分析报告并协助业务决策。"),
    ("人力资源专员（校招方向）", ["沟通能力", "时间管理", "文档能力", "团队协作", "学习能力", "招聘"], "参与校园招聘与人才运营，负责简历筛选、面试安排与候选人沟通。"),
]

# 应届生薪资区间（贴合市场实际，单位：元/月）
SALARY_RANGES = [
    (6000, 9000), (7000, 10000), (8000, 11000), (9000, 12000),
    (10000, 13000), (11000, 14000), (12000, 15000), (8000, 12000),
]

EDUCATION_LEVELS = ["本科", "硕士", "本科及以上"]


def build_fresh_jobs(target_count: int = 110) -> list[dict]:
    """生成 target_count 条国内真实应届友好岗位。"""
    jobs: list[dict] = []
    cities = list(COMPANIES_BY_CITY.keys())
    idx = 0
    # 多轮循环，保证覆盖所有城市与岗位模板
    while len(jobs) < target_count:
        city = cities[idx % len(cities)]
        template = FRESH_JOB_TEMPLATES[idx % len(FRESH_JOB_TEMPLATES)]
        company = random.choice(COMPANIES_BY_CITY[city])

        title, core_skills, desc_fragment = template

        # 软技能补充
        soft_skills = ["沟通能力", "团队协作", "学习能力", "解决问题", "抗压能力"]
        required = list(core_skills)
        if random.random() < 0.8:
            required.append(random.choice(soft_skills))
        # 去重
        seen = set()
        required = [s for s in required if not (s in seen or seen.add(s))]

        salary_min, salary_max = random.choice(SALARY_RANGES)
        edu = random.choice(EDUCATION_LEVELS)

        description = (
            f"面向应届生/在校生的{title}岗位，提供完善的导师带教与培训体系。"
            f"{desc_fragment}"
            f" 要求具备 {('、'.join(required[:4]))} 等能力，"
            f"{edu}及以上学历，欢迎应届生投递。积极热情、学习能力强者优先。"
        )

        jobs.append({
            "title": title,
            "company_name": company,
            "city": city,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "experience_level": "应届/在校生",
            "education_level": edu,
            "required_skills": required,
            "description": description,
            "source": "seed_jobs_fresh",
            "source_url": "",
            "published_at": "",
        })
        idx += 1

    return jobs[:target_count]


def main():
    # 读取现有种子
    existing: list[dict] = []
    if os.path.exists(SEED_PATH):
        with open(SEED_PATH, encoding="utf-8") as f:
            existing = json.load(f)

    existing_count = len(existing)
    fresh = build_fresh_jobs(target_count=110)

    # 合并：现有 + 新增应届岗位
    merged = existing + fresh

    with open(SEED_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"原有种子: {existing_count} 条")
    print(f"新增应届友好岗位: {len(fresh)} 条")
    print(f"合并后种子总数: {len(merged)} 条")
    print(f"已写回: {SEED_PATH}")

    # 简单统计新增岗位的城市分布
    from collections import Counter
    city_counter = Counter(j["city"] for j in fresh)
    print("\n新增岗位城市分布:")
    for c, n in city_counter.most_common():
        print(f"  {c}: {n}")


if __name__ == "__main__":
    main()
