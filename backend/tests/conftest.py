import pytest

import database
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A Flask test client backed by a fresh, seeded, throwaway database per test.

    Points database.DB_PATH at a temp file before the app is created, so
    every test starts from the same known seed data and never touches
    the real backend/database.db.
    """
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    application = create_app(seed_db=True)
    return application.test_client()
