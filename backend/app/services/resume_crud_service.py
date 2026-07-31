"""简历持久化与 CRUD 服务。"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.api.schemas import ResumeCreate, ResumeListParams, ResumeUpdate, UploadLogListParams
from app.models import Resume, UploadLog

logger = logging.getLogger(__name__)


def _dump_json(value: Any) -> str:
    """将对象序列化为 JSON 字符串。"""
    return json.dumps(value, ensure_ascii=False)


def create_resume(db: Session, payload: ResumeCreate) -> Resume:
    """创建简历记录。"""
    db_resume = Resume(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        file_name=payload.file_name,
        file_size=payload.file_size,
        basic_info=_dump_json(payload.basic_info.model_dump()),
        education=_dump_json([e.model_dump() for e in payload.education]),
        work_experience=_dump_json([e.model_dump() for e in payload.work_experience]),
        project_experience=_dump_json([e.model_dump() for e in payload.project_experience]),
        competition_experience=_dump_json([e.model_dump() for e in payload.competition_experience]),
        awards=_dump_json(payload.awards),
        certifications=_dump_json(payload.certifications),
        language_skills=_dump_json(payload.language_skills),
        self_evaluation=payload.self_evaluation,
        job_intention=_dump_json(payload.job_intention.model_dump()),
        publications=_dump_json([p.model_dump() for p in payload.publications]),
        portfolio=_dump_json([p.model_dump() for p in payload.portfolio]),
        skills=_dump_json(payload.skills),
        raw_text=payload.raw_text,
        experience_level=payload.experience_level,
        education_level=payload.education_level,
        fuzzy=payload.fuzzy,
        obstacles=_dump_json(payload.obstacles) if payload.obstacles else "",
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    logger.info("创建简历记录: id=%s, name=%s", db_resume.id, db_resume.name)
    return db_resume


def update_resume(db: Session, resume_id: int, payload: ResumeUpdate) -> Resume | None:
    """更新简历记录。"""
    db_resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not db_resume:
        return None

    update_data: dict[str, Any] = payload.model_dump(exclude_unset=True)
    json_fields = {
        "basic_info",
        "education",
        "work_experience",
        "project_experience",
        "competition_experience",
        "awards",
        "certifications",
        "language_skills",
        "job_intention",
        "publications",
        "portfolio",
        "skills",
        "obstacles",
    }

    for key, value in update_data.items():
        if key in json_fields and value is not None:
            if isinstance(value, BaseModel):
                value = value.model_dump()
            elif isinstance(value, list):
                value = [
                    item.model_dump() if isinstance(item, BaseModel) else item
                    for item in value
                ]
            value = _dump_json(value)
        setattr(db_resume, key, value)

    db.commit()
    db.refresh(db_resume)
    logger.info("更新简历记录: id=%s", resume_id)
    return db_resume


def get_resume(db: Session, resume_id: int) -> Resume | None:
    """获取简历记录。"""
    return db.query(Resume).filter(Resume.id == resume_id).first()


def delete_resume(db: Session, resume_id: int) -> bool:
    """删除（软删除）简历记录。"""
    db_resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not db_resume:
        return False
    db_resume.is_active = False
    db.commit()
    logger.info("删除简历记录: id=%s", resume_id)
    return True


def list_resumes(db: Session, params: ResumeListParams) -> tuple[list[Resume], int]:
    """分页查询简历记录。"""
    query = db.query(Resume).filter(Resume.is_active == True)  # noqa: E712

    if params.q:
        keyword = f"%{params.q}%"
        query = query.filter(
            or_(
                Resume.name.ilike(keyword),
                Resume.email.ilike(keyword),
                Resume.phone.ilike(keyword),
                Resume.skills.ilike(keyword),
            )
        )
    if params.education_level:
        query = query.filter(Resume.education_level == params.education_level)
    if params.experience_level:
        query = query.filter(Resume.experience_level == params.experience_level)
    if params.fuzzy is not None:
        query = query.filter(Resume.fuzzy == params.fuzzy)
    if params.is_active is not None:
        query = query.filter(Resume.is_active == params.is_active)

    total = query.with_entities(func.count(Resume.id)).scalar() or 0
    items = (
        query.order_by(desc(Resume.created_at))
        .offset((params.page - 1) * params.size)
        .limit(params.size)
        .all()
    )
    return items, total


def create_upload_log(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    file_name: str = "",
    file_size: int = 0,
    file_type: str = "",
    status: str = "success",
    message: str = "",
) -> UploadLog:
    """创建上传/操作日志。"""
    log = UploadLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        file_name=file_name,
        file_size=file_size,
        file_type=file_type,
        status=status,
        message=message,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_upload_logs(db: Session, params: UploadLogListParams) -> tuple[list[UploadLog], int]:
    """分页查询上传/操作日志。"""
    query = db.query(UploadLog)

    if params.action:
        query = query.filter(UploadLog.action == params.action)
    if params.entity_type:
        query = query.filter(UploadLog.entity_type == params.entity_type)
    if params.status:
        query = query.filter(UploadLog.status == params.status)
    if params.file_name:
        query = query.filter(UploadLog.file_name.ilike(f"%{params.file_name}%"))
    if params.start_date:
        query = query.filter(UploadLog.created_at >= params.start_date)
    if params.end_date:
        query = query.filter(UploadLog.created_at <= params.end_date)

    total = query.with_entities(func.count(UploadLog.id)).scalar() or 0
    items = (
        query.order_by(desc(UploadLog.created_at))
        .offset((params.page - 1) * params.size)
        .limit(params.size)
        .all()
    )
    return items, total
