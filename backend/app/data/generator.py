import random
from typing import Any

random.seed(42)

# 真实中国科技公司列表（替代 Faker 生成）
_REAL_COMPANIES: list[dict[str, str]] = [
    {"name": "字节跳动", "industry": "互联网", "size": "大型", "city": "北京"},
    {"name": "腾讯科技", "industry": "互联网", "size": "大型", "city": "深圳"},
    {"name": "阿里巴巴", "industry": "电子商务", "size": "大型", "city": "杭州"},
    {"name": "华为技术", "industry": "智能制造", "size": "大型", "city": "深圳"},
    {"name": "美团", "industry": "互联网", "size": "大型", "city": "北京"},
    {"name": "百度在线", "industry": "互联网", "size": "大型", "city": "北京"},
    {"name": "京东集团", "industry": "电子商务", "size": "大型", "city": "北京"},
    {"name": "网易", "industry": "互联网", "size": "大型", "city": "杭州"},
    {"name": "拼多多", "industry": "电子商务", "size": "大型", "city": "上海"},
    {"name": "滴滴出行", "industry": "汽车出行", "size": "大型", "city": "北京"},
    {"name": "小米科技", "industry": "智能制造", "size": "大型", "city": "北京"},
    {"name": "OPPO", "industry": "智能制造", "size": "大型", "city": "深圳"},
    {"name": "vivo", "industry": "智能制造", "size": "大型", "city": "深圳"},
    {"name": "大疆创新", "industry": "智能制造", "size": "中型", "city": "深圳"},
    {"name": "商汤科技", "industry": "人工智能", "size": "中型", "city": "上海"},
    {"name": "旷视科技", "industry": "人工智能", "size": "中型", "city": "北京"},
    {"name": "地平线机器人", "industry": "人工智能", "size": "中型", "city": "北京"},
    {"name": "思必驰", "industry": "人工智能", "size": "中型", "city": "苏州"},
    {"name": "蚂蚁集团", "industry": "金融科技", "size": "大型", "city": "杭州"},
    {"name": "微众银行", "industry": "金融科技", "size": "大型", "city": "深圳"},
    {"name": "陆金所", "industry": "金融科技", "size": "中型", "city": "上海"},
    {"name": "蔚来汽车", "industry": "汽车出行", "size": "中型", "city": "上海"},
    {"name": "理想汽车", "industry": "汽车出行", "size": "中型", "city": "北京"},
    {"name": "小鹏汽车", "industry": "汽车出行", "size": "中型", "city": "广州"},
    {"name": "比亚迪", "industry": "汽车出行", "size": "大型", "city": "深圳"},
    {"name": "B站", "industry": "文化传媒", "size": "中型", "city": "上海"},
    {"name": "快手", "industry": "互联网", "size": "大型", "city": "北京"},
    {"name": "小红书", "industry": "互联网", "size": "中型", "city": "上海"},
    {"name": "知乎", "industry": "互联网", "size": "中型", "city": "北京"},
    {"name": "携程旅行", "industry": "互联网", "size": "大型", "city": "上海"},
    {"name": "贝壳控股", "industry": "房地产", "size": "中型", "city": "北京"},
    {"name": "链家网", "industry": "房地产", "size": "中型", "city": "北京"},
    {"name": "好未来", "industry": "教育培训", "size": "中型", "city": "北京"},
    {"name": "猿辅导", "industry": "教育培训", "size": "中型", "city": "北京"},
    {"name": "作业帮", "industry": "教育培训", "size": "中型", "city": "北京"},
    {"name": "微医集团", "industry": "医疗健康", "size": "中型", "city": "杭州"},
    {"name": "平安好医生", "industry": "医疗健康", "size": "中型", "city": "深圳"},
    {"name": "京东健康", "industry": "医疗健康", "size": "大型", "city": "北京"},
    {"name": "三只松鼠", "industry": "消费品", "size": "中型", "city": "芜湖"},
    {"name": "完美日记", "industry": "消费品", "size": "中型", "city": "广州"},
    {"name": "SHEIN", "industry": "电子商务", "size": "大型", "city": "南京"},
    {"name": "安克创新", "industry": "消费品", "size": "中型", "city": "深圳"},
    {"name": "米哈游", "industry": "游戏", "size": "中型", "city": "上海"},
    {"name": "莉莉丝游戏", "industry": "游戏", "size": "中型", "city": "上海"},
    {"name": "叠纸游戏", "industry": "游戏", "size": "小型", "city": "上海"},
    {"name": "完美世界", "industry": "游戏", "size": "大型", "city": "北京"},
    {"name": "巨人网络", "industry": "游戏", "size": "中型", "city": "上海"},
    {"name": "猿力科技", "industry": "教育培训", "size": "中型", "city": "北京"},
    {"name": "声网Agora", "industry": "企业服务", "size": "中型", "city": "上海"},
]

SKILL_CATEGORIES = [
    "编程语言",
    "前端框架",
    "后端框架",
    "数据库",
    "AI/ML",
    "工具",
    "软技能",
]

_SKILL_DEFINITIONS: dict[str, str] = {
    "编程语言": "{name} 是一种编程语言，掌握它能够帮助工程师完成特定领域的软件开发任务。",
    "前端框架": "{name} 是前端开发中常用的框架或库，用于构建用户界面和交互体验。",
    "后端框架": "{name} 是服务端开发框架，用于构建高性能、可扩展的后端应用。",
    "数据库": "{name} 是数据存储与查询相关的技术，广泛应用于业务数据持久化与分析。",
    "AI/ML": "{name} 是人工智能或机器学习领域的技术/工具，用于模型训练、推理或数据处理。",
    "工具": "{name} 是研发与工程实践中常用的工具/平台，用于提升开发与协作效率。",
    "软技能": "{name} 是职场中重要的通用能力，有助于团队协作、项目推进与个人成长。",
}

_SKILL_POOL: list[tuple[str, str, list[str]]] = [
    # 编程语言
    ("Python", "编程语言", ["py", "python3"]),
    ("Java", "编程语言", ["java"]),
    ("JavaScript", "编程语言", ["js", "ES6"]),
    ("TypeScript", "编程语言", ["ts"]),
    ("Go", "编程语言", ["golang"]),
    ("C++", "编程语言", ["cpp"]),
    ("C#", "编程语言", ["csharp", "dotnet"]),
    ("Rust", "编程语言", ["rustlang"]),
    ("Ruby", "编程语言", ["ruby"]),
    ("PHP", "编程语言", ["php"]),
    ("Swift", "编程语言", ["swift"]),
    ("Kotlin", "编程语言", ["kt"]),
    ("Scala", "编程语言", ["scala"]),
    ("SQL", "编程语言", ["结构化查询语言"]),
    ("Shell", "编程语言", ["bash", "脚本"]),
    ("R", "编程语言", ["r语言"]),
    ("MATLAB", "编程语言", ["matlab"]),
    ("Objective-C", "编程语言", ["objc"]),
    ("Perl", "编程语言", ["perl"]),
    ("Lua", "编程语言", ["lua"]),
    ("Dart", "编程语言", ["dart"]),
    ("Julia", "编程语言", ["julia"]),
    ("Haskell", "编程语言", ["haskell"]),
    ("Erlang", "编程语言", ["erlang"]),
    ("Clojure", "编程语言", ["clojure"]),
    ("Groovy", "编程语言", ["groovy"]),
    # 前端框架
    ("React", "前端框架", ["reactjs"]),
    ("Vue.js", "前端框架", ["vue", "vue2", "vue3"]),
    ("Angular", "前端框架", ["angularjs"]),
    ("Svelte", "前端框架", ["svelte"]),
    ("Next.js", "前端框架", ["nextjs"]),
    ("Nuxt.js", "前端框架", ["nuxtjs"]),
    ("jQuery", "前端框架", ["jquery"]),
    ("Bootstrap", "前端框架", ["bootstrap"]),
    ("Tailwind CSS", "前端框架", ["tailwind"]),
    ("Ant Design", "前端框架", ["antd"]),
    ("Element UI", "前端框架", ["element"]),
    ("Webpack", "前端框架", ["webpack"]),
    ("Vite", "前端框架", ["vite"]),
    ("Rollup", "前端框架", ["rollup"]),
    ("Electron", "前端框架", ["electron"]),
    ("Flutter", "前端框架", ["flutter"]),
    ("React Native", "前端框架", ["rn"]),
    ("Taro", "前端框架", ["taro"]),
    ("Uni-app", "前端框架", ["uniapp"]),
    ("微信小程序", "前端框架", ["小程序", "mina"]),
    # 后端框架
    ("Spring Boot", "后端框架", ["springboot"]),
    ("Django", "后端框架", ["django"]),
    ("Flask", "后端框架", ["flask"]),
    ("FastAPI", "后端框架", ["fastapi"]),
    ("Express", "后端框架", ["expressjs"]),
    ("NestJS", "后端框架", ["nestjs"]),
    ("Ruby on Rails", "后端框架", ["rails"]),
    ("Laravel", "后端框架", ["laravel"]),
    ("ThinkPHP", "后端框架", ["tp"]),
    ("Gin", "后端框架", ["gin"]),
    ("Beego", "后端框架", ["beego"]),
    ("Echo", "后端框架", ["echo"]),
    ("ASP.NET Core", "后端框架", ["aspnet"]),
    ("Fastify", "后端框架", ["fastify"]),
    ("Koa", "后端框架", ["koa"]),
    ("Tornado", "后端框架", ["tornado"]),
    ("Quart", "后端框架", ["quart"]),
    ("Phoenix", "后端框架", ["phoenix"]),
    ("Actix", "后端框架", ["actix"]),
    ("Rocket", "后端框架", ["rocket"]),
    ("Micronaut", "后端框架", ["micronaut"]),
    # 数据库
    ("MySQL", "数据库", ["mysql"]),
    ("PostgreSQL", "数据库", ["postgres", "pg"]),
    ("MongoDB", "数据库", ["mongo"]),
    ("Redis", "数据库", ["redis"]),
    ("Elasticsearch", "数据库", ["es"]),
    ("ClickHouse", "数据库", ["clickhouse"]),
    ("TiDB", "数据库", ["tidb"]),
    ("Oracle", "数据库", ["oracle"]),
    ("SQL Server", "数据库", ["mssql"]),
    ("SQLite", "数据库", ["sqlite"]),
    ("DynamoDB", "数据库", ["dynamodb"]),
    ("Cassandra", "数据库", ["cassandra"]),
    ("Neo4j", "数据库", ["neo4j"]),
    ("InfluxDB", "数据库", ["influxdb"]),
    ("HBase", "数据库", ["hbase"]),
    ("MariaDB", "数据库", ["mariadb"]),
    ("Couchbase", "数据库", ["couchbase"]),
    ("Firebase", "数据库", ["firebase"]),
    ("Snowflake", "数据库", ["snowflake"]),
    ("Amazon RDS", "数据库", ["rds"]),
    # AI/ML
    ("TensorFlow", "AI/ML", ["tf"]),
    ("PyTorch", "AI/ML", ["pytorch"]),
    ("Scikit-learn", "AI/ML", ["sklearn"]),
    ("Keras", "AI/ML", ["keras"]),
    ("XGBoost", "AI/ML", ["xgboost"]),
    ("LightGBM", "AI/ML", ["lightgbm"]),
    ("Hugging Face", "AI/ML", ["huggingface"]),
    ("OpenAI API", "AI/ML", ["openai"]),
    ("LangChain", "AI/ML", ["langchain"]),
    ("LlamaIndex", "AI/ML", ["llamaindex"]),
    ("Pandas", "AI/ML", ["pandas"]),
    ("NumPy", "AI/ML", ["numpy"]),
    ("Matplotlib", "AI/ML", ["matplotlib"]),
    ("Seaborn", "AI/ML", ["seaborn"]),
    ("OpenCV", "AI/ML", ["opencv"]),
    ("NLTK", "AI/ML", ["nltk"]),
    ("spaCy", "AI/ML", ["spacy"]),
    ("Transformer", "AI/ML", ["transformer"]),
    ("CNN", "AI/ML", ["卷积神经网络"]),
    ("RNN", "AI/ML", ["循环神经网络"]),
    ("GAN", "AI/ML", ["生成对抗网络"]),
    ("强化学习", "AI/ML", ["reinforcement learning", "rl"]),
    ("计算机视觉", "AI/ML", ["cv"]),
    ("自然语言处理", "AI/ML", ["nlp"]),
    ("Prompt Engineering", "AI/ML", ["提示工程"]),
    ("RAG", "AI/ML", ["检索增强生成"]),
    # 工具
    ("Git", "工具", ["git", "版本控制"]),
    ("Docker", "工具", ["docker"]),
    ("Kubernetes", "工具", ["k8s"]),
    ("Jenkins", "工具", ["jenkins"]),
    ("GitLab CI", "工具", ["gitlab ci"]),
    ("GitHub Actions", "工具", ["github actions"]),
    ("Terraform", "工具", ["terraform"]),
    ("Ansible", "工具", ["ansible"]),
    ("Prometheus", "工具", ["prometheus"]),
    ("Grafana", "工具", ["grafana"]),
    ("ELK Stack", "工具", ["elk"]),
    ("Kafka", "工具", ["kafka"]),
    ("RabbitMQ", "工具", ["rabbitmq"]),
    ("Nginx", "工具", ["nginx"]),
    ("Linux", "工具", ["linux"]),
    ("Bash", "工具", ["bash"]),
    ("JIRA", "工具", ["jira"]),
    ("Confluence", "工具", ["confluence"]),
    ("Postman", "工具", ["postman"]),
    ("Swagger", "工具", ["swagger"]),
    ("Figma", "工具", ["figma"]),
    ("Sketch", "工具", ["sketch"]),
    ("Adobe XD", "工具", ["adobe xd"]),
    ("Markdown", "工具", ["markdown"]),
    # 软技能
    ("沟通能力", "软技能", ["沟通", "表达"]),
    ("团队协作", "软技能", ["团队合作"]),
    ("项目管理", "软技能", ["pm", "项目推进"]),
    ("需求分析", "软技能", ["需求理解"]),
    ("时间管理", "软技能", ["时间规划"]),
    ("领导力", "软技能", ["leadership"]),
    ("解决问题", "软技能", ["问题解决"]),
    ("抗压能力", "软技能", ["抗压"]),
    ("学习能力", "软技能", ["学习"]),
    ("演讲表达", "软技能", ["演讲"]),
    ("跨部门协作", "软技能", ["跨部门沟通"]),
    ("产品思维", "软技能", ["产品意识"]),
    ("用户洞察", "软技能", ["用户研究"]),
    ("数据驱动", "软技能", ["数据思维"]),
    ("敏捷开发", "软技能", ["scrum", "agile"]),
    ("文档能力", "软技能", ["技术文档"]),
    ("英语读写", "软技能", ["英语"]),
    ("商务谈判", "软技能", ["谈判"]),
    ("冲突管理", "软技能", ["冲突处理"]),
    ("教练辅导", "软技能", ["mentoring"]),
]


def get_skill_pool() -> list[tuple[str, str, list[str]]]:
    """返回完整技能词表。"""
    return _SKILL_POOL


def get_skill_names() -> list[str]:
    """返回所有技能名称列表。"""
    return [name for name, _category, _aliases in _SKILL_POOL]


INDUSTRIES = [
    "互联网",
    "电子商务",
    "金融科技",
    "企业服务",
    "人工智能",
    "医疗健康",
    "教育培训",
    "文化传媒",
    "游戏",
    "新能源",
    "智能制造",
    "物流运输",
    "消费品",
    "房地产",
    "汽车出行",
]

COMPANY_SIZES = ["小型", "中型", "大型"]

CITIES = [
    "北京",
    "上海",
    "广州",
    "深圳",
    "杭州",
    "成都",
    "武汉",
    "南京",
    "西安",
    "苏州",
    "天津",
    "重庆",
    "长沙",
    "厦门",
    "青岛",
]

EXPERIENCE_LEVELS = [
    "应届/在校生",
    "1-3年",
    "3-5年",
    "5-10年",
    "10年以上",
]

EDUCATION_LEVELS = ["大专", "本科", "硕士", "博士"]

_JOB_TITLE_POOL: list[tuple[str, list[str]]] = [
    ("Java后端工程师", ["Java", "Spring Boot", "MySQL", "Redis", "Git", "Linux", "Docker"]),
    (
        "高级Java后端工程师",
        ["Java", "Spring Boot", "MySQL", "Redis", "Kafka", "Elasticsearch", "Docker", "Kubernetes"],
    ),
    ("Python后端工程师", ["Python", "Django", "Flask", "FastAPI", "PostgreSQL", "Redis", "Docker"]),
    ("Go后端工程师", ["Go", "Gin", "MySQL", "Redis", "Kafka", "Docker", "Linux"]),
    ("Node.js后端工程师", ["JavaScript", "TypeScript", "Express", "MongoDB", "Redis"]),
    ("前端开发工程师", ["JavaScript", "TypeScript", "React", "Vue.js", "Webpack", "Git"]),
    (
        "高级前端工程师",
        ["JavaScript", "TypeScript", "React", "Next.js", "Webpack", "Vite", "Tailwind CSS"],
    ),
    ("全栈工程师", ["JavaScript", "TypeScript", "React", "Python", "MySQL", "Docker"]),
    ("移动端开发工程师", ["Swift", "Kotlin", "Flutter", "React Native"]),
    ("iOS开发工程师", ["Swift", "Objective-C", "Git"]),
    ("Android开发工程师", ["Kotlin", "Java", "Git"]),
    ("算法工程师", ["Python", "PyTorch", "TensorFlow", "Pandas", "NumPy"]),
    ("机器学习工程师", ["Python", "Scikit-learn", "XGBoost", "Pandas", "NumPy", "Docker"]),
    ("NLP工程师", ["Python", "PyTorch", "Transformer", "Hugging Face", "自然语言处理", "RAG"]),
    ("计算机视觉工程师", ["Python", "PyTorch", "OpenCV", "计算机视觉", "CNN"]),
    ("数据分析师", ["Python", "SQL", "Pandas", "NumPy", "Matplotlib", "数据驱动"]),
    ("数据工程师", ["Python", "SQL", "Kafka", "Redis", "MySQL", "Docker"]),
    ("大数据开发工程师", ["Java", "Python", "Kafka", "Redis", "MySQL", "Docker"]),
    ("数据产品经理", ["SQL", "数据驱动", "产品思维", "需求分析", "沟通能力"]),
    ("产品经理", ["产品思维", "需求分析", "沟通能力", "项目管理", "数据驱动"]),
    ("高级产品经理", ["产品思维", "用户洞察", "数据驱动", "跨部门协作", "项目管理"]),
    ("用户增长运营", ["数据驱动", "用户洞察", "沟通能力", "解决问题", "学习能力"]),
    ("内容运营", ["数据驱动", "用户洞察", "沟通能力", "解决问题", "学习能力"]),
    ("新媒体运营", ["数据驱动", "用户洞察", "沟通能力", "解决问题", "学习能力"]),
    ("电商运营", ["数据驱动", "用户洞察", "沟通能力", "解决问题", "学习能力"]),
    ("社群运营", ["数据驱动", "用户洞察", "沟通能力", "解决问题", "学习能力"]),
    ("产品经理助理", ["产品思维", "需求分析", "文档能力", "沟通能力"]),
    ("UI设计师", ["Figma", "Sketch", "Adobe XD"]),
    ("UX设计师", ["Figma", "Sketch", "用户洞察", "沟通能力", "解决问题"]),
    ("测试工程师", ["Python", "Postman", "Linux", "Git"]),
    ("自动化测试工程师", ["Python", "Jenkins", "Git", "Docker"]),
    ("运维工程师", ["Linux", "Shell", "Nginx", "Docker", "Kubernetes", "Prometheus"]),
    ("DevOps工程师", ["Docker", "Kubernetes", "Jenkins", "GitLab CI", "Terraform", "Linux"]),
    ("SRE工程师", ["Linux", "Kubernetes", "Prometheus", "Grafana", "Python", "Go"]),
    ("网络安全工程师", ["Linux", "Python", "Nginx", "Git", "Bash", "Docker"]),
    ("区块链开发工程师", ["Go", "Rust", "Docker", "Kubernetes", "Git"]),
    ("C++开发工程师", ["C++", "Linux", "Git", "Docker", "Python", "Bash"]),
    (".NET开发工程师", ["C#", "ASP.NET Core", "SQL Server", "Git", "Docker"]),
    ("PHP开发工程师", ["PHP", "Laravel", "ThinkPHP", "MySQL", "Redis", "Linux"]),
    ("Ruby开发工程师", ["Ruby", "Ruby on Rails", "PostgreSQL", "Git", "Linux"]),
    ("Java架构师", ["Java", "Spring Boot", "Kubernetes", "MySQL", "Redis", "Kafka", "Docker"]),
    ("前端架构师", ["JavaScript", "TypeScript", "React", "Webpack", "Vite", "Docker"]),
    ("后端负责人", ["Java", "Go", "Python", "MySQL", "Redis", "Kubernetes", "领导力"]),
    ("技术总监", ["领导力", "项目管理", "沟通能力", "解决问题", "学习能力", "时间管理"]),
    ("项目经理", ["项目管理", "敏捷开发", "JIRA", "沟通能力", "文档能力"]),
    ("Scrum Master", ["敏捷开发", "团队协作", "JIRA", "沟通能力", "教练辅导"]),
    ("人力资源专员", ["沟通能力", "时间管理", "文档能力", "团队协作", "学习能力"]),
    ("招聘专员", ["沟通能力", "时间管理", "文档能力", "团队协作", "学习能力"]),
    ("HRBP", ["沟通能力", "跨部门协作", "团队协作", "文档能力", "学习能力"]),
    ("财务分析师", ["SQL", "数据驱动", "沟通能力", "文档能力", "解决问题"]),
    ("商业分析师", ["SQL", "数据驱动", "需求分析", "沟通能力", "文档能力", "产品思维"]),
    ("法务专员", ["文档能力", "沟通能力", "解决问题", "时间管理", "学习能力"]),
    ("行政助理", ["时间管理", "沟通能力", "文档能力", "团队协作", "学习能力"]),
    ("客服主管", ["沟通能力", "解决问题", "抗压能力", "团队协作", "领导力"]),
    ("销售经理", ["商务谈判", "沟通能力", "抗压能力", "解决问题", "学习能力"]),
    ("客户经理", ["商务谈判", "沟通能力", "时间管理", "解决问题", "团队协作"]),
]

_DESCRIPTION_TEMPLATES: list[str] = [
    "负责 {scope} 相关工作，使用 {primary_skill} 等核心技术完成产品需求开发与系统优化。",
    "参与 {scope} 设计与实现，深入掌握 {primary_skill}，能够独立完成模块开发与问题排查。",
    "承担 {scope} 任务，熟练使用 {primary_skill} 进行开发、调试与性能优化。",
    "负责公司 {scope} 的建设与维护，运用 {primary_skill} 提升业务效率与用户体验。",
    "主导 {scope} 方向的技术方案，精通 {primary_skill}，具备较强的问题解决能力。",
]

_SCOPE_MAP: dict[str, list[str]] = {
    "Java后端工程师": ["服务端系统", "后端业务模块", "高并发系统"],
    "高级Java后端工程师": ["核心后端架构", "分布式系统", "微服务平台"],
    "Python后端工程师": ["后端服务", "数据接口", "Web应用"],
    "Go后端工程师": ["高并发服务", "后端中间件", "云原生应用"],
    "Node.js后端工程师": ["后端服务", "BFF层", "实时应用"],
    "前端开发工程师": ["Web前端", "用户界面", "前端交互"],
    "高级前端工程师": ["前端架构", "组件库", "前端工程化"],
    "全栈工程师": ["全栈Web应用", "前后端一体化", "产品功能闭环"],
    "移动端开发工程师": ["移动应用", "跨端开发", "App功能"],
    "iOS开发工程师": ["iOS客户端", "移动端应用", "Apple生态应用"],
    "Android开发工程师": ["Android客户端", "移动应用", "Android生态应用"],
    "算法工程师": ["算法模型", "推荐系统", "机器学习应用"],
    "机器学习工程师": ["机器学习平台", "模型工程化", "智能应用"],
    "NLP工程师": ["自然语言处理模型", "文本理解", "智能对话系统"],
    "计算机视觉工程师": ["图像识别", "视觉算法", "视频分析"],
    "数据分析师": ["数据分析", "业务指标", "数据报告"],
    "数据工程师": ["数据平台", "数据仓库", "ETL流程"],
    "大数据开发工程师": ["大数据平台", "离线/实时计算", "数据架构"],
    "数据产品经理": ["数据产品", "指标平台", "数据应用"],
    "产品经理": ["产品功能", "需求落地", "用户体验"],
    "高级产品经理": ["产品战略", "产品线规划", "商业化"],
    "用户增长运营": ["用户增长", "拉新促活", "增长实验"],
    "内容运营": ["内容生态", "内容策划", "创作者运营"],
    "新媒体运营": ["新媒体矩阵", "社交平台运营", "内容传播"],
    "电商运营": ["电商业务", "品类运营", "活动运营"],
    "社群运营": ["社群生态", "用户运营", "私域流量"],
    "产品经理助理": ["产品支持", "需求整理", "项目跟进"],
    "UI设计师": ["界面设计", "视觉设计", "设计规范"],
    "UX设计师": ["用户体验设计", "交互流程", "设计研究"],
    "测试工程师": ["功能测试", "质量保障", "测试流程"],
    "自动化测试工程师": ["自动化测试", "测试平台", "持续集成"],
    "运维工程师": ["系统运维", "基础设施", "服务稳定性"],
    "DevOps工程师": ["DevOps平台", "CI/CD", "云原生基础设施"],
    "SRE工程师": ["站点可靠性", "系统可用性", "故障响应"],
    "网络安全工程师": ["安全防护", "漏洞管理", "安全运营"],
    "区块链开发工程师": ["区块链应用", "去中心化系统", "智能合约"],
    "C++开发工程师": ["高性能服务", "系统软件", "底层模块"],
    ".NET开发工程师": ["企业级应用", "后台服务", "管理系统"],
    "PHP开发工程师": ["Web后端", "内容系统", "电商平台"],
    "Ruby开发工程师": ["Web应用", "敏捷开发", "后端服务"],
    "Java架构师": ["系统架构", "技术中台", "企业级架构"],
    "前端架构师": ["前端技术架构", "工程化体系", "性能优化"],
    "后端负责人": ["后端团队", "服务端体系", "技术管理"],
    "技术总监": ["技术战略", "研发团队", "技术管理"],
    "项目经理": ["项目交付", "跨团队协调", "进度管理"],
    "Scrum Master": ["敏捷团队", "Scrum流程", "团队效能"],
    "人力资源专员": ["人事管理", "员工服务", "HR流程"],
    "招聘专员": ["人才招聘", "渠道运营", "面试安排"],
    "HRBP": ["业务伙伴", "组织与人才", "员工发展"],
    "财务分析师": ["财务分析", "预算管理", "经营分析"],
    "商业分析师": ["商业分析", "业务策略", "数据分析支持"],
    "法务专员": ["法律事务", "合同审核", "合规管理"],
    "行政助理": ["行政支持", "会议安排", "办公管理"],
    "客服主管": ["客服团队", "客户满意度", "服务流程"],
    "销售经理": ["销售业务", "客户拓展", "业绩达成"],
    "客户经理": ["客户管理", "关系维护", "商务合作"],
}


# 核心技能必须出现在生成的技能池中，用于保证技能关系与演示路径可用
_CORE_SKILL_NAMES: set[str] = {
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "Go",
    "C#",
    "PHP",
    "Ruby",
    "SQL",
    "React",
    "Vue.js",
    "Angular",
    "Spring Boot",
    "Django",
    "Flask",
    "FastAPI",
    "Gin",
    "ASP.NET Core",
    "Laravel",
    "ThinkPHP",
    "Ruby on Rails",
    "NestJS",
    "MySQL",
    "PostgreSQL",
    "Redis",
    "MongoDB",
    "Git",
    "Docker",
    "Kubernetes",
    "PyTorch",
    "TensorFlow",
    "Pandas",
    "NumPy",
}


def generate_skills(n: int = 80) -> list[dict[str, Any]]:
    """生成技能实体数据，优先确保核心技能在样本中。"""
    if n > len(_SKILL_POOL):
        n = len(_SKILL_POOL)

    pool_by_name = {item[0]: item for item in _SKILL_POOL}
    core_items = [pool_by_name[name] for name in _CORE_SKILL_NAMES if name in pool_by_name]
    remaining_pool = [item for item in _SKILL_POOL if item[0] not in _CORE_SKILL_NAMES]

    needed = n - len(core_items)
    if needed < 0:
        selected = core_items[:n]
    else:
        selected = core_items + random.sample(remaining_pool, k=min(needed, len(remaining_pool)))

    # 保持结果顺序随机但稳定
    random.shuffle(selected)
    skills = []
    for idx, (name, category, aliases) in enumerate(selected, start=1):
        definition = _SKILL_DEFINITIONS[category].format(name=name)
        skills.append({
            "id": idx,
            "name": name,
            "category": category,
            "aliases": aliases,
            "definition": definition,
        })
    return skills


def generate_companies(n: int = 40) -> list[dict[str, Any]]:
    """从真实公司列表中选取公司数据（替代 Faker 生成）。"""
    n = max(1, min(n, len(_REAL_COMPANIES)))
    # 随机选取 n 个真实公司
    selected = random.sample(_REAL_COMPANIES, n)
    companies = []
    for idx, company in enumerate(selected, start=1):
        companies.append({
            "id": idx,
            "name": company["name"],
            "industry": company["industry"],
            "size": company["size"],
            "city": company["city"],
        })
    return companies


def _salary_range_for_experience(exp: str) -> tuple[int, int]:
    ranges = {
        "应届/在校生": (6000, 12000),
        "1-3年": (10000, 20000),
        "3-5年": (18000, 35000),
        "5-10年": (30000, 60000),
        "10年以上": (50000, 100000),
    }
    return ranges.get(exp, (10000, 30000))


def generate_jobs(
    companies: list[dict[str, Any]],
    skills: list[dict[str, Any]],
    n: int = 250,
) -> list[dict[str, Any]]:
    """生成岗位 JD 数据。"""
    n = max(1, min(n, 300))
    skill_map = {s["name"]: s for s in skills}
    jobs = []

    for idx in range(1, n + 1):
        company = random.choice(companies)
        title, core_skills = random.choice(_JOB_TITLE_POOL)

        exp = random.choice(EXPERIENCE_LEVELS)
        edu = random.choice(EDUCATION_LEVELS)
        salary_min, salary_max = _salary_range_for_experience(exp)
        # 添加随机波动
        salary_min = int(random.uniform(salary_min * 0.9, salary_min * 1.1) / 1000) * 1000
        salary_max = int(random.uniform(salary_max * 0.9, salary_max * 1.1) / 1000) * 1000
        if salary_max <= salary_min:
            salary_max = salary_min + 5000

        # 构建 required_skills：核心技能 + 随机补充 + 软技能
        required = list(core_skills)
        # 软技能池
        soft_skills = [s["name"] for s in skills if s["category"] == "软技能"]
        # 工具/数据库补充
        supplement_pool = [s["name"] for s in skills if s["category"] in ("工具", "数据库")]
        if random.random() < 0.7:
            required.append(random.choice(soft_skills))
        extra_count = random.randint(1, 3)
        required.extend(random.sample(supplement_pool, min(extra_count, len(supplement_pool))))
        # 去重并保证存在于技能表中
        required = [r for r in dict.fromkeys(required) if r in skill_map]
        if len(required) < 3:
            more = [s["name"] for s in random.sample(skills, k=5) if s["name"] not in required]
            required.extend(more[: 3 - len(required)])

        # 岗位描述
        scope = random.choice(_SCOPE_MAP.get(title, ["业务"]))
        primary = required[0] if required else core_skills[0]
        desc_template = random.choice(_DESCRIPTION_TEMPLATES)
        description = desc_template.format(scope=scope, primary_skill=primary)
        description += " 要求具备 " + "、".join(required[:4]) + " 等能力，"
        description += f"{edu}及以上学历，{exp}经验优先。"
        description += " 欢迎对技术有热情、具备良好沟通与团队协作能力的候选人加入。"

        city = company["city"] if random.random() < 0.6 else random.choice(CITIES)

        jobs.append({
            "id": idx,
            "title": title,
            "company_id": company["id"],
            "city": city,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "experience_level": exp,
            "education_level": edu,
            "required_skills": required,
            "description": description,
        })

    return jobs


def infer_missing_fields(
    job: dict[str, Any],
    skills: list[dict[str, Any]],
    experience_levels: list[str] | None = None,
    education_levels: list[str] | None = None,
) -> dict[str, Any]:
    """为真实 JD 补全缺失字段，使用规则模板作为 fallback。

    返回值是填充后的新字典，不会修改原字典。
    """
    if experience_levels is None:
        experience_levels = EXPERIENCE_LEVELS
    if education_levels is None:
        education_levels = EDUCATION_LEVELS

    filled = dict(job)
    filled.setdefault("title", "未命名岗位")
    filled.setdefault("city", "未知")

    if not filled.get("experience_level"):
        filled["experience_level"] = random.choice(experience_levels)
    if not filled.get("education_level"):
        filled["education_level"] = random.choice(education_levels)

    exp = filled["experience_level"]
    salary_min = filled.get("salary_min")
    salary_max = filled.get("salary_max")
    if salary_min is None or salary_max is None:
        s_min, s_max = _salary_range_for_experience(exp)
        filled["salary_min"] = int(random.uniform(s_min * 0.9, s_min * 1.1) / 1000) * 1000
        filled["salary_max"] = int(random.uniform(s_max * 0.9, s_max * 1.1) / 1000) * 1000
        if filled["salary_max"] <= filled["salary_min"]:
            filled["salary_max"] = filled["salary_min"] + 5000

    required = filled.get("required_skills") or []
    if not required and filled.get("description"):
        # 从描述中简单匹配技能名称
        desc = filled["description"]
        skill_names = {s["name"] for s in skills}
        required = [
            name for name in skill_names
            if name.lower() in desc.lower() or name in desc
        ]
    if not required:
        required = ["沟通能力", "团队协作", "学习能力"]
    filled["required_skills"] = required

    if not filled.get("description"):
        filled["description"] = f"{filled['title']}，工作地点 {filled['city']}。"

    return filled


def generate_all_data(
    n_skills: int = 80,
    n_companies: int = 40,
    n_jobs: int = 250,
) -> dict[str, list[dict[str, Any]]]:
    """一次性生成技能、公司与岗位三类结构化数据。"""
    skills = generate_skills(n_skills)
    companies = generate_companies(n_companies)
    jobs = generate_jobs(companies, skills, n_jobs)
    return {
        "skills": skills,
        "companies": companies,
        "jobs": jobs,
    }
