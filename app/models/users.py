from sqlalchemy import func
import bcrypt
from sqlalchemy import INTEGER, Column, DateTime, ForeignKey, String, Boolean, Numeric, Integer
from sqlalchemy.orm import declarative_base, relationship, Mapped

from .base import BaseModel


class User(BaseModel):
    __tablename__ = "user"
    name = Column(String, index=True, nullable=False)
    email = Column(String(length=128), unique=True, nullable=False)
    password = Column(String(length=512), nullable=False)
    is_admin = Column(Boolean, default=False)
    bills = relationship("Bill", back_populates="user")

    def to_dict(self, fk_include: bool = False):
        res = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "is_admin": self.is_admin,
        }
        if fk_include:
            res["bills"] = self.bills
        return res

    def set_hash_password(self, password: str):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
