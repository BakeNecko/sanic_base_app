import random
import uuid
import factory

from app.models import User, Bill, Transactions
from app.utils import hash_password


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = None 
        
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        session = kwargs.pop('session')  
        cls._meta.sqlalchemy_session = session
        return super()._create(model_class, *args, **kwargs) 

        
class UserFactory(BaseFactory):
    class Meta:
        model = User
    
    name = factory.Faker('name') 
    email = factory.Faker('email')
    password = factory.Faker('password')

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        password = kwargs.get('password')
        kwargs['password'] = hash_password(password)
        return super()._create(model_class, *args, **kwargs)
    
class BillFactory(BaseFactory):
    class Meta:
        model = Bill
        
    user = factory.SubFactory(UserFactory, session=factory.SelfAttribute('..session'))
    amount = 0
    account_id = factory.Sequence(lambda n: n)

class TransactionFactory(BaseFactory):
    class Meta:
        model = Transactions
    
    transaction_id = factory.LazyAttribute(lambda _: str(uuid.uuid4()))
    t_amount = factory.LazyAttribute(lambda _: random.randint(1, 100))
    bill = factory.SubFactory(
        BillFactory, 
        amount=factory.SelfAttribute('..t_amount'),
        session=factory.SelfAttribute('..session')
    )
    
