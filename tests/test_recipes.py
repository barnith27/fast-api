import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db
from app.models import Base
from app.database import SQLALCHEMY_DATABASE_URL

TEST_DATABASE_URL = "sqlite:///./test_recipes.db"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Добро пожаловать в Кулинарную книку!"}


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_recipe():
    recipe_data = {
        "name": "Тестовый рецепт",
        "cooking_time": 30,
        "ingredients": "Ингредиент 1, Ингредиент 2",
        "description": "Описание тестового рецепта"
    }
    response = client.post("/recipes", json=recipe_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == recipe_data["name"]
    assert data["cooking_time"] == recipe_data["cooking_time"]
    assert data["id"] is not None
    assert data["views"] == 0

def test_get_recipes_empty():
    response = client.get("/recipes")
    assert response.status_code == 200
    assert response.json() == []

def test_get_recipe_not_found():
    response = client.get("/recipes/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Рецепт не найден"


def test_full_recipe_flow():
    recipe_data = {
        "name": "Борщ",
        "cooking_time": 60,
        "ingredients": "Свекла, капуста, мясо",
        "description": "Классический борщ"
    }
    create_response = client.post("/recipes", json=recipe_data)
    assert create_response.status_code == 200
    recipe_id = create_response.json()["id"]
    get_response = client.get(f"/recipes/{recipe_id}")
    assert get_response.status_code == 200
    assert get_response.json()["views"] == 1
    list_response = client.get("/recipes")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == recipe_id