from sqlalchemy import String, func
from sqlalchemy import Column, ForeignKey, Numeric, Integer
from sqlalchemy.orm import relationship, Mapped

from .base import BaseModel
from .users import User


class Bill(BaseModel):
    __tablename__ = "bill"

    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="bills")
    amount = Column(Numeric, default=0.0)
    transactions = relationship("Transactions", back_populates="bill")
    # Задается автоматически с созданием счета, при захвате WebHook'a
    account_id = Column(
        Integer,
        comment="ID счета в сторонней платежной системе?",
        unique=True,
        index=True,
    )

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "account_id": self.account_id,
            "amount": self.amount,
        }


class Transactions(BaseModel):
    __tablename__ = "transaction"

    transaction_id = Column(String, unique=True)
    t_amount = Column(Numeric, nullable=False)

    bill_id = Column(Integer, ForeignKey("bill.id"))
    bill = relationship("Bill", back_populates="transactions")
