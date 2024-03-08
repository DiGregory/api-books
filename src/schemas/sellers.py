from pydantic import BaseModel

from .books import ReturnedBook

__all__ = [
    "BaseSeller",
    "IncomingSeller",
    "ReturnedAllSellers",
    "ReturnedSeller",
    "ReturnedSellerWithoutPass",
    "ReturnedSellerWithBooks",
]


# Базовый класс "Продавец", содержащий поля, которые есть во всех классах-наследниках.
class BaseSeller(BaseModel):
    first_name: str
    last_name: str
    email: str


# Класс для регистрации
class IncomingSeller(BaseSeller):
    password: str


# Класс, валидирующий исходящие данные при регистрации
class ReturnedSeller(BaseSeller):
    id: int


# Класс, валидирующий исходящие данные для get
class ReturnedSellerWithoutPass(BaseSeller):
    id: int


# Класс для возврата массива объектов "продавец"
class ReturnedAllSellers(BaseModel):
    sellers: list[ReturnedSellerWithoutPass]


class ReturnedSellerWithBooks(ReturnedSellerWithoutPass):
    id: int
    books: list[ReturnedBook]
