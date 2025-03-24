from sqlalchemy import func
from sqlalchemy import Column, DateTime, INTEGER
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class BaseModel(Base, TimestampMixin):
    __abstract__ = True
    id = Column(INTEGER(), primary_key=True)
