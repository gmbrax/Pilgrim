import pytest
from unittest.mock import Mock  # A ferramenta para criar nosso "dublê"
from pathlib import Path
from sqlalchemy import inspect, Column, Integer, String
from sqlalchemy.orm import Session

from src.pilgrim.database import Database,Base

class MockUser(Base):
    __tablename__ = 'mock_users'
    id = Column(Integer, primary_key=True)
    name = Column(String)

@pytest.fixture
def db_instance(tmp_path: Path):
    fake_db_path = tmp_path / "test_pilgrim.db"
    mock_config_manager = Mock()
    mock_config_manager.database_url = str(fake_db_path)
    db = Database(mock_config_manager)
    return db, fake_db_path

def test_create_database(db_instance):
    db, fake_db_path = db_instance
    db.create()
    assert fake_db_path.exists()

def test_table_creation(db_instance):
    db, _ = db_instance
    db.create()
    inspector = inspect(db.engine)
    assert "mock_users" in inspector.get_table_names()

def test_session_returned_corectly(db_instance):
    db, _ = db_instance
    session = db.session()
    assert isinstance(session, Session)
    session.close()



