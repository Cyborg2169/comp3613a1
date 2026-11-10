from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.models import AwardCategory, User
from app.utilities.security import encrypt_password


@pytest.fixture(scope="session")
def password_hash() -> str:
    return encrypt_password("test-password")


@pytest.fixture
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def seeded_data(test_engine, password_hash) -> dict[str, int]:
    with Session(test_engine) as session:
        users = {
            "bob": User(
                username="bob",
                email="bob@example.com",
                password=password_hash,
                role="regular_user",
            ),
            "teacher": User(
                username="teacher",
                email="teacher@example.com",
                password=password_hash,
                role="teacher",
            ),
            "admin": User(
                username="admin",
                email="admin@example.com",
                password=password_hash,
                role="admin",
            ),
        }
        bronze = AwardCategory(
            name="Bronze Service",
            description="Getting started",
            required_hours=20,
        )
        session.add_all([*users.values(), bronze])
        session.commit()
        for user in users.values():
            session.refresh(user)
        session.refresh(bronze)
        return {
            **{name: user.id for name, user in users.items()},
            "bronze": bronze.id,
        }


@pytest.fixture
def client(test_engine) -> Iterator[TestClient]:
    def get_test_session():
        with Session(test_engine) as session:
            yield session

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_session] = get_test_session
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
