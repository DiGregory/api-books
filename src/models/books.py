from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .seller import Seller  # noqa


class Book(BaseModel):
    __tablename__ = "books_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("sellers_table.id"))
    year: Mapped[int]
    count_pages: Mapped[int]

    seller = relationship("Seller", back_populates="books")
