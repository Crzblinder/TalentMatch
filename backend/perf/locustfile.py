"""Locust 压力测试脚本：并发解析与匹配。

依赖 locust（未加入 requirements.txt，按需安装）：
    pip install locust

运行方式（需后端已启动并有种子数据）：
    cd backend
    locust -f perf/locustfile.py --host http://127.0.0.1:8000
"""

from __future__ import annotations

import importlib.util

JD_TEXT = """某科技公司招聘 Python 后端工程师
岗位职责：负责后端服务开发。
岗位要求：熟悉 Python、FastAPI、PostgreSQL，3-5 年经验，本科及以上学历。"""

RESUME_TEXT = """张三
手机：13812345678
邮箱：zhangsan@example.com

教育经历
2016.09-2020.06 北京大学 计算机科学与技术 本科

工作经历
2020.07-2023.03 某科技有限公司 Python后端工程师
负责后端服务开发，使用 Python、FastAPI 和 PostgreSQL。

技能
Python、FastAPI、PostgreSQL、Docker

求职意向
期望岗位：Python后端工程师
"""

# 延迟导入 locust，未安装时本文件仍可被安全 import
spec = importlib.util.find_spec("locust")
if spec is None:
    raise ImportError(
        "locust 未安装，请先执行 `pip install locust`，"
        "或改用 backend/perf/load_test.py 进行负载测试。"
    )

from locust import HttpUser, between, task  # type: ignore[import-not-found]  # noqa: E402


class TalentMatchUser(HttpUser):
    """模拟用户：解析 JD、解析简历、执行岗位匹配。"""

    wait_time = between(1, 3)
    profile_id: int | None = None
    job_id: int | None = None

    def on_start(self) -> None:
        """每个用户启动时创建画像并记录一个岗位 ID。"""
        profile_payload = {
            "name": f"LocustProfile-{self.user_instance_count}",
            "skills": ["Python", "FastAPI", "Docker"],
            "experience_level": "3-5年",
            "target_job_titles": ["Python 后端工程师"],
            "is_active": True,
        }
        with self.client.post(
            "/api/v1/profiles",
            json=profile_payload,
            catch_response=True,
            name="setup.create_profile",
        ) as resp:
            if resp.status_code == 200:
                self.profile_id = resp.json()["data"]["id"]
            else:
                resp.failure("创建画像失败")

        with self.client.get(
            "/api/v1/jobs",
            params={"size": 1},
            catch_response=True,
            name="setup.list_jobs",
        ) as resp:
            if resp.status_code == 200:
                items = resp.json()["data"]["items"]
                if items:
                    self.job_id = items[0]["id"]
                else:
                    resp.failure("岗位库为空")
            else:
                resp.failure("获取岗位列表失败")

    @task(3)
    def parse_jd(self) -> None:
        """并发 JD 解析。"""
        self.client.post(
            "/api/v1/jobs/parse",
            json={"jd_text": JD_TEXT},
            name="parse.jd",
        )

    @task(3)
    def parse_resume(self) -> None:
        """并发简历解析。"""
        self.client.post(
            "/api/v1/resumes/parse",
            json={"resume_text": RESUME_TEXT},
            name="parse.resume",
        )

    @task(2)
    def create_match(self) -> None:
        """并发岗位匹配。"""
        if self.profile_id is None or self.job_id is None:
            return
        self.client.post(
            "/api/v1/matches",
            json={"profile_id": self.profile_id, "job_id": self.job_id},
            name="match.create",
        )
