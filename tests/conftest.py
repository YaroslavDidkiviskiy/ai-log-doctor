import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override

    from app.config import settings
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_log_file():
    content = """\
2026-03-08 12:00:01 INFO app.server Application started
2026-03-08 12:00:05 ERROR app.auth Failed to validate token for user 183 from IP 192.168.1.14
2026-03-08 12:00:07 ERROR app.auth Failed to validate token for user 742 from IP 10.0.0.22
2026-03-08 12:00:10 WARNING app.db Connection pool running low: 45/50
2026-03-08 12:00:12 ERROR app.api Timeout while calling external service
Traceback (most recent call last):
  File "/app/api/client.py", line 22, in call_service
    response = requests.get(url, timeout=5)
TimeoutError: Connection timed out after 5s
2026-03-08 12:00:15 INFO app.server Health check OK
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name
    yield path
    os.unlink(path)
