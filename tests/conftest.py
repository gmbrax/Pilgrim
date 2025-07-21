import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pilgrim.database import Base
from pilgrim.models.travel_diary import TravelDiary

# Todos os imports necessários para as fixtures devem estar aqui
# ...

@pytest.fixture(scope="function")
def db_session():
    """Esta fixture agora está disponível para TODOS os testes."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def populated_db_session(db_session):
    """Esta também fica disponível para todos."""
    travel_diary = TravelDiary(name="My Travel Diary", directory_name="viagem-teste")
    db_session.add(travel_diary)
    db_session.commit()
    return db_session

@pytest.fixture
def session_with_one_diary(db_session):
    diary = TravelDiary(name="Diário de Teste", directory_name="diario_de_teste")
    db_session.add(diary)
    db_session.commit()
    db_session.refresh(diary)
    return db_session, diary
