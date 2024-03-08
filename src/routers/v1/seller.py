from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.models.books import Book
from src.models.seller import Seller
from src.schemas import (
    BaseSeller,
    IncomingSeller,
    ReturnedAllSellers,
    ReturnedBook,
    ReturnedSeller,
    ReturnedSellerWithBooks,
    ReturnedSellerWithoutPass,
)

from .authorization import get_current_user

seller_router = APIRouter(tags=["seller"], prefix="/seller")

# Больше не симулируем хранилище данных. Подключаемся к реальному, через сессию.
DBSession = Annotated[AsyncSession, Depends(get_async_session)]


# Ручка для создания записи о продавце в БД. Возвращает созданную книгу.
@seller_router.post(
    "/", response_model=ReturnedSeller, status_code=status.HTTP_201_CREATED
)  # Прописываем модель ответа
async def create_seller(
    seller: IncomingSeller, session: DBSession
):  # прописываем модель валидирующую входные данные и сессию как зависимость.
    # это - бизнес логика. Обрабатываем данные, сохраняем, преобразуем и т.д.
    new_seller = Seller(
        first_name=seller.first_name,
        last_name=seller.last_name,
        email=seller.email,
        password=seller.password,
    )
    session.add(new_seller)
    await session.flush()

    return new_seller


# Ручка, возвращающая всех продавцов
@seller_router.get("/", response_model=ReturnedAllSellers)
async def get_all_sellers(session: DBSession):
    query = select(Seller)
    res = await session.execute(query)
    sellers = res.scalars().all()
    return {"sellers": sellers}


# Ручка для получения продавца по его ИД
@seller_router.get("/{seller_id}", response_model=ReturnedSellerWithBooks)
async def get_seller(seller_id: int, session: DBSession, curr_user=Depends(get_current_user)):
    # Получение данных о продавце
    seller_result = await session.execute(select(Seller).filter(Seller.id == seller_id))
    seller = seller_result.scalars().first()

    if seller is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")

    # Получение данных о книгах продавца
    books_result = await session.execute(select(Book).filter(Book.seller_id == seller_id))
    books = books_result.scalars().all()

    returned_books = [
        ReturnedBook(
            id=book.id,
            title=book.title,
            author=book.author,
            year=book.year,
            count_pages=book.count_pages,
            seller_id=book.seller_id,
        )
        for book in books
    ]

    # Формируем итоговый ответ
    seller_response = ReturnedSellerWithBooks(
        id=seller.id, first_name=seller.first_name, last_name=seller.last_name, email=seller.email, books=returned_books
    )
    return seller_response


# Ручка для обновления данных о продацве
@seller_router.put("/{seller_id}")
async def update_seller(seller_id: int, new_data: BaseSeller, session: DBSession):

    if updated_seller := await session.get(Seller, seller_id):
        updated_seller.id = seller_id
        updated_seller.first_name = new_data.first_name
        updated_seller.last_name = new_data.last_name
        updated_seller.email = new_data.email

        await session.flush()
        seller_response = ReturnedSellerWithoutPass(
            id=updated_seller.id,
            first_name=updated_seller.first_name,
            last_name=updated_seller.last_name,
            email=updated_seller.email,
        )

        return seller_response

    return Response(status_code=status.HTTP_404_NOT_FOUND)


# Ручка для удаления продавца
@seller_router.delete("/{seller_id}")
async def delete_seller(seller_id: int, session: DBSession):
    # Находим и удаляем все книги, принадлежащие продавцу
    books_to_delete = await session.execute(select(Book).filter(Book.seller_id == seller_id))
    books = books_to_delete.scalars().all()
    for book in books:
        await session.delete(book)

    # После удаления книг, находим и удаляем самого продавца
    deleted_seller = await session.get(Seller, seller_id)
    if not deleted_seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")

    await session.delete(deleted_seller)

    # Сохраняем изменения в базе данных
    await session.commit()

    # Возвращаем ответ без контента, но с соответствующим статус-кодом
    return Response(status_code=status.HTTP_204_NO_CONTENT)
