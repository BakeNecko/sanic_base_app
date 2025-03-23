from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class CreateUserReqeuest(LoginRequest):
    is_admin: bool = False
    name: str

class UsersListIDs(BaseModel):
    user_ids: list[int]
    
class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None

class UpdateUsersList(UpdateUserRequest, UsersListIDs):
    ...

class IDserializer(BaseModel):
    id: int

class TransactionRetrieve(IDserializer):
    transaction_id: str
    t_amount: float 
    bill_id: int
    
    model_config = ConfigDict(
        title="Модель Транзакции",
        validate_assignment=True,
        from_attributes=True,
    )

class BillBaseSerializer(IDserializer):
    amount: float
    user_id: int
    account_id: int 
    
    model_config = ConfigDict(
        title="Модель счета",
        description='Без дополнительных моделей',
        validate_assignment=True,
        from_attributes=True,
    )
    
class BillSerializer(BillBaseSerializer):
    transactions: list[TransactionRetrieve]
    
    model_config = ConfigDict(
        title="Полная Модель счета",
        validate_assignment=True,
        from_attributes=True,
    )

class UserBaseRetrieve(IDserializer):
    name: str
    is_admin: bool
 
    model_config = ConfigDict(
        title="Урезанная Модель пользователя",
        description='Без дополнительных моделей',
        validate_assignment=True,
        from_attributes=True,
    )
    
class UserRetrieve(UserBaseRetrieve):
    bills: list[BillBaseSerializer] = []
 
    model_config = ConfigDict(
        title="Полная Модель пользователя",
        validate_assignment=True,
        from_attributes=True,
    )
    
class ExternalPayWH(BaseModel):
    transaction_id: str
    user_id: int
    account_id: int
    amount: Decimal
    signature: str

