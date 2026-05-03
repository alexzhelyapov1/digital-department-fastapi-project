"""
Automated tests for the dictionary application.
"""
import io
import os
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db


# Use a separate test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SESSION_LOCAL_TEST = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override get_db for testing."""
    database = SESSION_LOCAL_TEST()
    try:
        yield database
    finally:
        database.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Setup and teardown test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture
def client():
    """Fixture for TestClient."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_client(client):
    """Fixture for an authenticated TestClient."""
    client.post(
        "/signup/",
        data={"username": "testuser", "email": "test@example.com", "password": "password"}
    )
    client.post(
        "/login/",
        data={"username": "testuser", "password": "password"}
    )
    return client


def test_signup_and_login(client):
    """Test user signup and login process."""
    # Test Signup
    response = client.post(
        "/signup/",
        data={"username": "user1", "email": "user1@example.com", "password": "password123"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "🔑 Вход" in response.text

    # Test Login
    response = client.post(
        "/login/",
        data={"username": "user1", "password": "password123"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "Мои болгарские слова" in response.text
    assert client.cookies.get("access_token") is not None


def test_logout(auth_client):
    """Test user logout."""
    response = auth_client.post("/logout/", follow_redirects=True)
    assert response.status_code == 200
    assert "Добре дошли" in response.text
    assert auth_client.cookies.get("access_token") is None


def test_unauthenticated_access(client):
    """Test access to protected URLs without authentication."""
    protected_urls = ["/words/", "/words/add/", "/quiz/", "/words/import/"]
    for url in protected_urls:
        response = client.get(url)
        assert response.status_code == 401


def test_word_lifecycle(auth_client):
    """Test the complete word lifecycle: add, list, edit."""
    # 1. Add word
    response = auth_client.post(
        "/words/add/",
        data={
            "bulgarian_word": "Котка",
            "russian_translation": "Кошка",
            "example_sentence": "Аз имам котка.",
            "is_learned": "false"
        },
        follow_redirects=False
    )
    assert response.status_code == 302

    # 2. Verify in list
    response = auth_client.get("/words/")
    assert "Котка" in response.text
    assert "Кошка" in response.text

    # 3. Edit word
    match = re.search(r'/words/(\d+)/edit/', response.text)
    assert match is not None
    word_id = match.group(1)

    response = auth_client.post(
        f"/words/{word_id}/edit/",
        data={
            "bulgarian_word": "Куче",
            "russian_translation": "Собака",
            "example_sentence": "Аз имам куче.",
            "is_learned": "true"
        },
        follow_redirects=True
    )
    assert "Куче" in response.text
    assert "Собака" in response.text
    assert "Изучено" in response.text


def test_quiz_logic(auth_client):
    """Test quiz answer validation."""
    # Add a word for the quiz
    auth_client.post(
        "/words/add/",
        data={"bulgarian_word": "Ябълка", "russian_translation": "Яблоко"}
    )

    # Get quiz page
    response = auth_client.get("/quiz/")
    assert "Ябълка" in response.text

    match = re.search(r'name="word_id" value="(\d+)"', response.text)
    word_id = match.group(1)

    # Test correct answer
    response = auth_client.post(
        "/quiz/",
        data={"word_id": word_id, "translation": "Яблоко"},
        follow_redirects=False
    )
    auth_client.cookies.update(response.cookies)
    response = auth_client.get("/quiz/")
    assert "Верно!" in response.text

    # Test wrong answer
    response = auth_client.post(
        "/quiz/",
        data={"word_id": word_id, "translation": "Груша"},
        follow_redirects=False
    )
    auth_client.cookies.update(response.cookies)
    response = auth_client.get("/quiz/")
    assert "Ошибка" in response.text


def test_import_csv(auth_client):
    """Test importing words from a CSV file."""
    csv_content = (
        "bulgarian_word,russian_translation,example_sentence\n"
        "Бира,Пиво,Една бира моля\n"
        "Вино,Вино,Червено вино"
    )
    file = io.BytesIO(csv_content.encode("utf-8"))

    response = auth_client.post(
        "/words/import/",
        files={"file": ("test.csv", file, "text/csv")},
        follow_redirects=False
    )
    auth_client.cookies.update(response.cookies)
    response = auth_client.get("/words/")
    assert "Бира" in response.text
    assert "Пиво" in response.text
    assert "Вино" in response.text
    assert "Успешно импортировано: 2" in response.text


def test_user_isolation(client):
    """Test that users can only see their own words."""
    # User 1 adds a word
    client.post("/signup/", data={
        "username": "u1", "email": "u1@e.com", "password": "p"
    })
    client.post("/login/", data={"username": "u1", "password": "p"})
    client.post("/words/add/", data={
        "bulgarian_word": "Скрипт", "russian_translation": "Скрипт"
    })
    client.post("/logout/")

    # User 2 should NOT see it
    client.post("/signup/", data={
        "username": "u2", "email": "u2@e.com", "password": "p"
    })
    client.post("/login/", data={"username": "u2", "password": "p"})
    response = client.get("/words/")
    assert "Скрипт" not in response.text
    assert "У вас еще нет слов в словаре" in response.text
