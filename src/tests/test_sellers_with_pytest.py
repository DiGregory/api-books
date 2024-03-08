import pytest
from fastapi import status
from sqlalchemy import select

from src.models import books
from src.models.seller import Seller


# Тест на ручку создающую продавца
@pytest.mark.asyncio
async def test_create_seller(async_client):
    data = {"first_name": "John", "last_name": "Doe", "email": "email@gmail.com", "password": "qwerty123"}

    response = await async_client.post("/api/v1/seller/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    assert result_data["first_name"] == "John"
    assert result_data["last_name"] == "Doe"
    assert result_data["email"] == "email@gmail.com"


# # Тест на ручку получения списка всех продавцов
@pytest.mark.asyncio
async def test_get_all_sellers(db_session, async_client):
    seller = Seller(first_name="John", last_name="Doe", email="email@gmail.com", password="qwerty123")
    seller_2 = Seller(first_name="John1", last_name="Doe1", email="email@gmail1.com", password="qwerty1234")

    db_session.add_all([seller, seller_2])
    await db_session.flush()

    response = await async_client.get("/api/v1/seller/")
    assert response.status_code == status.HTTP_200_OK

    sellers_response = response.json()["sellers"]

    # Проверяем, что каждый созданный продавец есть в списке продавцов, возвращаемых API
    expected_sellers = [
        {"first_name": "John", "last_name": "Doe", "email": "email@gmail.com", "id": seller.id},
        {"first_name": "John1", "last_name": "Doe1", "email": "email@gmail1.com", "id": seller_2.id},
    ]

    # Для каждого ожидаемого продавца проверяем, что он есть в списке продавцов из ответа
    for expected_seller in expected_sellers:
        assert any(
            seller
            for seller in sellers_response
            if seller["id"] == expected_seller["id"]
            and seller["first_name"] == expected_seller["first_name"]
            and seller["last_name"] == expected_seller["last_name"]
            and seller["email"] == expected_seller["email"]
        )


# # Тест на ручку получения конкретного продавца
@pytest.mark.asyncio
async def test_get_single_seller(db_session, async_client):
    seller = Seller(first_name="John", last_name="Doe", email="email123@gmail.com", password="qwerty123")
    db_session.add_all([seller])
    await db_session.flush()

    id: int = seller.id

    book = books.Book(author="Pushkin", title="Eugeny Onegin", year=2005, count_pages=104, seller_id=id)
    book_1 = books.Book(author="Pushkin1", title="Eugeny Onegin1", year=2005, count_pages=104, seller_id=id)
    db_session.add_all([book, book_1])
    await db_session.commit()

    response = await async_client.post(
        "/api/v1/token/", data={"username": "email123@gmail.com", "password": "qwerty123"}
    )
    token = response.json()["access_token"]

    response = await async_client.get(f"/api/v1/seller/{id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_200_OK

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "id": id,
        "first_name": "John",
        "last_name": "Doe",
        "email": "email123@gmail.com",
        "books": [
            {
                "id": book.id,
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2005,
                "count_pages": 104,
                "seller_id": id,
            },
            {
                "id": book_1.id,
                "title": "Eugeny Onegin1",
                "author": "Pushkin1",
                "year": 2005,
                "count_pages": 104,
                "seller_id": id,
            },
        ],
    }


# Тест на ручку обновления одного продавца
@pytest.mark.asyncio
async def test_update_seller(db_session, async_client):
    seller = Seller(first_name="John", last_name="Doe", email="email1@gmail.com", password="qwerty1")
    db_session.add_all([seller])
    await db_session.flush()
    # Создаем книги вручную
    book = books.Book(author="Pushkin", title="Eugeny Onegin", year=2001, count_pages=104, seller_id=seller.id)

    db_session.add(book)
    await db_session.commit()

    response = await async_client.put(
        f"/api/v1/seller/{seller.id}",
        json={"first_name": "john2", "last_name": "Doe2", "email": "email2@gmail.com"},
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # Проверяем, что обновились все поля
    res = await db_session.get(Seller, seller.id)
    assert res.first_name == "john2"
    assert res.last_name == "Doe2"
    assert res.email == "email2@gmail.com"


# # Тест на ручку удаления книги
@pytest.mark.asyncio
async def test_delete_seller(db_session, async_client):
    seller = Seller(first_name="John", last_name="Doe", email="email1@gmail.com", password="qwerty1")
    db_session.add_all([seller])
    await db_session.flush()
    # Создаем книги вручную,
    book = books.Book(author="Pushkin", title="Eugeny Onegin", year=2001, count_pages=104, seller_id=seller.id)
    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/seller/{seller.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # проверка что удалили продавца
    db_seller = await db_session.get(Seller, seller.id)
    assert db_seller is None

    # проверка что удалили его книги
    db_books = (await db_session.execute(select(books.Book).filter(books.Book.seller_id == seller.id))).scalars().all()
    assert not db_books
