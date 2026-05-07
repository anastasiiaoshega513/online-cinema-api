import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.main import app
from db.engine import Base
from db.dependencies import get_db

from app.accounts.models import UserGroup, UserGroupEnum

from app.accounts import models as accounts_models
from app.movies import models as movies_models
from app.carts import models as carts_models
from app.orders import models as orders_models


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)


TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="module", autouse=True)
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(bind=sync_conn))
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(bind=sync_conn))

    async with TestingSessionLocal() as session:
        session.add_all(
            [
                UserGroup(name=UserGroupEnum.USER),
                UserGroup(name=UserGroupEnum.MODERATOR),
                UserGroup(name=UserGroupEnum.ADMIN),
            ]
        )
        await session.commit()

    yield


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()
