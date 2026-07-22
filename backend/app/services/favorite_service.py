"""岗位收藏服务层：封装收藏记录的增删查操作。"""

from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from app.models import FavoriteJob, Job, UserSkillProfile


class FavoriteService:
    """处理用户画像与岗位之间的收藏关系。"""

    def __init__(self, db: Session):
        self.db = db

    def add_favorite(self, profile_id: int, job_id: int) -> FavoriteJob:
        """为指定画像添加岗位收藏；已存在时直接返回现有记录。"""
        existing = (
            self.db.query(FavoriteJob)
            .filter(FavoriteJob.profile_id == profile_id, FavoriteJob.job_id == job_id)
            .first()
        )
        if existing:
            return existing

        favorite = FavoriteJob(profile_id=profile_id, job_id=job_id)
        self.db.add(favorite)
        self.db.commit()
        self.db.refresh(favorite)
        return favorite

    def remove_favorite(self, profile_id: int, job_id: int) -> bool:
        """取消指定画像对岗位的收藏，返回是否成功删除。"""
        favorite = (
            self.db.query(FavoriteJob)
            .filter(FavoriteJob.profile_id == profile_id, FavoriteJob.job_id == job_id)
            .first()
        )
        if not favorite:
            return False
        self.db.delete(favorite)
        self.db.commit()
        return True

    def list_favorites(
        self,
        profile_id: int,
        page: int = 1,
        size: int = 100,
    ) -> dict:
        """分页获取指定画像的收藏列表，并预加载岗位与公司信息。"""
        query = (
            self.db.query(FavoriteJob)
            .options(joinedload(FavoriteJob.job).joinedload(Job.company))
            .filter(FavoriteJob.profile_id == profile_id)
            .order_by(FavoriteJob.created_at.desc())
        )
        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()
        return {
            "total": total,
            "page": page,
            "size": size,
            "items": items,
        }

    def is_favorite(self, profile_id: int, job_id: int) -> bool:
        """判断指定画像是否已收藏某岗位。"""
        return (
            self.db.query(FavoriteJob)
            .filter(FavoriteJob.profile_id == profile_id, FavoriteJob.job_id == job_id)
            .first()
            is not None
        )

    def get_profile(self, profile_id: int) -> UserSkillProfile | None:
        """根据 ID 获取用户画像。"""
        return self.db.query(UserSkillProfile).filter(UserSkillProfile.id == profile_id).first()

    def get_job(self, job_id: int) -> Job | None:
        """根据 ID 获取岗位。"""
        return self.db.query(Job).filter(Job.id == job_id).first()
