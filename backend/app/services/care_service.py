# ruff: noqa: E501
"""求职关怀服务：为毕业生提供鼓励语录、实用建议、求职进度追踪等关怀向功能。"""

import json
import logging
import random
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import Job, UserSkillProfile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 鼓励语录库（真实、有温度的求职鼓励）
# ---------------------------------------------------------------------------
ENCOURAGEMENT_QUOTES: list[dict[str, str]] = [
    {
        "text": "每一次被拒绝，都是在帮你筛选出最适合你的机会。别灰心，你的价值不是由一个面试结果定义的。",
        "category": "心态建设",
        "scene": "面试被拒",
    },
    {
        "text": "找工作就像谈恋爱，不是你不够好，是还没遇到对的公司。保持耐心，总会碰到双向奔赴的那个。",
        "category": "心态建设",
        "scene": "求职焦虑",
    },
    {
        "text": "你的简历不是在'求人给工作'，而是在'展示你能创造什么价值'。换一个角度，自信就来了。",
        "category": "简历优化",
        "scene": "投递无回应",
    },
    {
        "text": "没有人一毕业就什么都会。你现在缺的不是能力，是让你展示能力的舞台。先上车，再换座。",
        "category": "心态建设",
        "scene": "自我怀疑",
    },
    {
        "text": "面试不是考试，是对话。面试官也想找到你身上的亮点——你们是合作关系，不是对立关系。",
        "category": "面试技巧",
        "scene": "面试紧张",
    },
    {
        "text": "应届生最大的优势不是经验，而是学习速度和可塑性。大胆投，大胆面，成长比结果更重要。",
        "category": "心态建设",
        "scene": "经验不足",
    },
    {
        "text": "投了100份简历没有回应？不是你不行，是简历需要优化。把'我做过什么'改成'我做出了什么结果'。",
        "category": "简历优化",
        "scene": "投递无回应",
    },
    {
        "text": "空窗期不可怕，可怕的是空窗期里什么都没做。读一本书、做一个项目、学一门技术，都是你的故事。",
        "category": "心态建设",
        "scene": "空窗期焦虑",
    },
    {
        "text": "小公司有小公司的好：你能接触更多核心业务，成长更快。第一份工作选成长空间大的，不要只看title。",
        "category": "职业规划",
        "scene": "公司选择",
    },
    {
        "text": "你不是在跟985/211竞争，你是在跟'能解决问题的人'竞争。面试官要的是能干活的人，不是一纸文凭。",
        "category": "心态建设",
        "scene": "学历焦虑",
    },
    {
        "text": "技术面试答不上来很正常。诚实地说'这个我不太熟，但如果遇到我会这样去查和学习'，比硬编强一百倍。",
        "category": "面试技巧",
        "scene": "技术面试",
    },
    {
        "text": "拿到 offer 是结果，不是目的。面经复盘、技术积累、心态调节——这些过程才是你真正的收获。",
        "category": "心态建设",
        "scene": "面试复盘",
    },
    {
        "text": "你的第一份工作不需要完美，它只需要足够好到你愿意为之全力以赴。完美的工作永远不会出现在起点。",
        "category": "职业规划",
        "scene": "选择困难",
    },
    {
        "text": "求职是一场马拉松，不是百米冲刺。给自己设定每日小目标：今天投5份、改一段经历、学一个知识点。",
        "category": "行动指南",
        "scene": "行动建议",
    },
    {
        "text": "有时候不是你不优秀，而是你和岗位的匹配度不够。精准投递比海投更有效，研究JD再投递，命中率翻倍。",
        "category": "投递策略",
        "scene": "海投无效",
    },
]

# ---------------------------------------------------------------------------
# 求职实用建议（针对毕业生实际困境）
# ---------------------------------------------------------------------------
PRACTICAL_TIPS: list[dict[str, Any]] = [
    {
        "title": "简历优化三板斧",
        "category": "简历",
        "content": "1. 用STAR法则描述经历（情境-任务-行动-结果）；2. 量化你的成果（如'优化后响应时间降低40%'）；3. 根据JD关键词调整简历，让HR一眼看到匹配点。",
        "difficulty": "easy",
        "estimated_time": "30分钟",
    },
    {
        "title": "面试自我介绍模板",
        "category": "面试",
        "content": "30秒版本：我是谁+我擅长什么+我想要什么。90秒版本：在此基础上加入一个最有亮点的项目经历。记住：自我介绍不是背简历，是讲你的'故事线'。",
        "difficulty": "easy",
        "estimated_time": "15分钟",
    },
    {
        "title": "技术面试准备清单",
        "category": "面试",
        "content": "1. 刷LeetCode高频题（目标岗位相关方向）；2. 准备2-3个项目的深度讲解（架构、难点、优化）；3. 了解目标公司技术栈和业务；4. 准备3-5个有深度的问题反问面试官。",
        "difficulty": "medium",
        "estimated_time": "1-2周",
    },
    {
        "title": "应届生薪资谈判指南",
        "category": "薪资",
        "content": "1. 查询行业应届生薪资范围（看准网、牛客、OfferShow）；2. 不要先报数字，让对方先给范围；3. 如果必须报，给一个比自己预期高10-15%的范围；4. 薪资不只是月薪，还要看年终奖、期权、补贴等总包。",
        "difficulty": "medium",
        "estimated_time": "1小时",
    },
    {
        "title": "投递策略优化",
        "category": "投递",
        "content": "1. 20%投冲刺岗（略高于当前水平）；2. 60%投匹配岗（符合当前技能和经验）；3. 20%投保底岗（确定能拿到offer的）。每天投递5-10份，保证质量和数量的平衡。",
        "difficulty": "easy",
        "estimated_time": "每日30分钟",
    },
    {
        "title": "空窗期应对策略",
        "category": "简历",
        "content": "1. 在简历中用'自主学习和项目实践'替代空窗期；2. 准备好面试时的解释话术（学习充电/考证/个人项目）；3. 空窗期做的事情要有产出（GitHub项目、技术博客、在线课程证书）。",
        "difficulty": "medium",
        "estimated_time": "2小时",
    },
    {
        "title": "无实习经历的简历写法",
        "category": "简历",
        "content": "1. 把课程设计/毕业设计当成项目经历来写；2. 突出竞赛获奖（数学建模、ACM、蓝桥杯等）；3. 展示开源贡献（GitHub PR/Issue）；4. 写一个有深度的个人项目并部署上线。",
        "difficulty": "medium",
        "estimated_time": "3-4小时",
    },
    {
        "title": "面试后复盘方法",
        "category": "面试",
        "content": "面试后立即记录：1. 被问到的问题及你的回答；2. 哪些回答得好/不好；3. 面试官关注的重点方向；4. 下次需要补充的知识点。建立面试复盘文档，持续迭代。",
        "difficulty": "easy",
        "estimated_time": "15分钟/次",
    },
]

# ---------------------------------------------------------------------------
# 求职阶段指南
# ---------------------------------------------------------------------------
JOB_SEARCH_STAGES: list[dict[str, Any]] = [
    {
        "stage": "准备期",
        "duration": "1-2周",
        "tasks": [
            "完成简历初稿并用STAR法则优化",
            "准备个人项目展示和GitHub整理",
            "确定目标岗位方向和目标公司列表",
            "刷目标岗位高频面试题",
        ],
        "tips": "这个阶段不要急着投递，磨刀不误砍柴工。好的准备能让后续投递效率翻倍。",
    },
    {
        "stage": "投递期",
        "duration": "2-4周",
        "tasks": [
            "每日投递5-10份，精准匹配JD",
            "根据反馈持续优化简历",
            "参加校招宣讲会和线上招聘会",
            "利用内推渠道提高简历通过率",
        ],
        "tips": "投递不是海投，每份简历都应该针对JD微调。保持投递记录，跟踪进度。",
    },
    {
        "stage": "面试期",
        "duration": "2-6周",
        "tasks": [
            "技术面试每日刷题保持手感",
            "每次面试后立即复盘记录",
            "准备3-5个有深度的问题反问面试官",
            "同步推进多个面试流程，不要all-in",
        ],
        "tips": "面试是双向选择，你也在考察公司。面试官的态度和问题往往能反映团队文化。",
    },
    {
        "stage": "决策期",
        "duration": "1-2周",
        "tasks": [
            "拿到offer后横向比较总包（薪资+年终+期权+福利）",
            "了解团队规模、技术氛围和晋升通道",
            "与HR确认入职时间和offer细节",
            "礼貌拒绝不选择的offer，保持良好关系",
        ],
        "tips": "第一份工作最重要的是成长空间，不是起薪。选一个让你能快速成长的平台。",
    },
]


def get_encouragement_quote(
    scene: str | None = None,
    category: str | None = None,
) -> dict[str, str]:
    """获取一条鼓励语录，可按场景和分类筛选。"""
    pool = ENCOURAGEMENT_QUOTES
    if scene:
        filtered = [q for q in pool if q["scene"] == scene]
        if filtered:
            pool = filtered
    if category:
        filtered = [q for q in pool if q["category"] == category]
        if filtered:
            pool = filtered
    return random.choice(pool)


def get_encouragement_quotes(
    count: int = 5,
    scene: str | None = None,
    category: str | None = None,
) -> list[dict[str, str]]:
    """获取多条鼓励语录。"""
    pool = ENCOURAGEMENT_QUOTES
    if scene:
        filtered = [q for q in pool if q["scene"] == scene]
        if filtered:
            pool = filtered
    if category:
        filtered = [q for q in pool if q["category"] == category]
        if filtered:
            pool = filtered
    count = min(count, len(pool))
    return random.sample(pool, count)


def get_practical_tips(
    category: str | None = None,
    difficulty: str | None = None,
) -> list[dict[str, Any]]:
    """获取实用建议列表。"""
    pool = PRACTICAL_TIPS
    if category:
        pool = [t for t in pool if t["category"] == category]
    if difficulty:
        pool = [t for t in pool if t["difficulty"] == difficulty]
    return pool


def get_job_search_stages() -> list[dict[str, Any]]:
    """获取求职阶段指南。"""
    return JOB_SEARCH_STAGES


def get_care_dashboard(
    db: Session,
    profile_id: int | None = None,
) -> dict[str, Any]:
    """生成求职关怀仪表盘数据。"""
    # 获取今日鼓励语
    daily_quote = get_encouragement_quote()

    # 获取随机3条实用建议
    tips = get_practical_tips()
    random.shuffle(tips)
    selected_tips = tips[:3]

    # 获取求职阶段指南
    stages = get_job_search_stages()

    # 统计数据
    total_jobs = db.query(Job).count()
    fresh_friendly_jobs = db.query(Job).filter(
        Job.experience_level == "应届/在校生"
    ).count()

    # 如果有 profile_id，获取个性化推荐
    profile_data = None
    if profile_id:
        profile = db.query(UserSkillProfile).filter(
            UserSkillProfile.id == profile_id
        ).first()
        if profile:
            skills = json.loads(profile.skills) if isinstance(
                profile.skills, str
            ) else profile.skills
            target_titles = json.loads(profile.target_job_titles) if isinstance(
                profile.target_job_titles, str
            ) else profile.target_job_titles
            profile_data = {
                "name": profile.name,
                "skills_count": len(skills),
                "target_job_titles": target_titles,
                "experience_level": profile.experience_level,
            }

    # 应届生友好岗位数量
    stats = {
        "total_jobs": total_jobs,
        "fresh_friendly_jobs": fresh_friendly_jobs,
        "fresh_friendly_ratio": round(fresh_friendly_jobs / max(total_jobs, 1) * 100, 1),
    }

    return {
        "daily_quote": daily_quote,
        "tips": selected_tips,
        "stages": stages,
        "stats": stats,
        "profile": profile_data,
        "generated_at": datetime.now().isoformat(),
    }
