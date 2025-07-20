import pytest
from datetime import datetime
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from pilgrim.database import Base
from pilgrim.models.travel_diary import TravelDiary
from pilgrim.models.entry import Entry
from pilgrim.models.photo import Photo

from pilgrim.service.entry_service import EntryService

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def populated_db_session(db_session):
    travel_diary = TravelDiary(name="My Travel Diary", directory_name="viagem-teste")
    db_session.add(travel_diary)
    db_session.commit()
    return db_session

def test_create_entry_successfully(populated_db_session):
    session = populated_db_session
    service = EntryService(session)
    diary_id = 1  # Sabemos que o ID é 1 por causa da nossa fixture
    title = "Primeiro Dia na Praia"
    text = "O dia foi ensolarado e o mar estava ótimo."
    date = datetime(2025, 7, 20)
    photos = [Photo(filepath="/path/to/photo1.jpg",name="Photo 1",photo_hash="hash_12345678",fk_travel_diary_id=diary_id), Photo(filepath="/path/to/photo2.jpg",name="Photo 1",photo_hash="hash_87654321",fk_travel_diary_id=diary_id)]
    created_entry = service.create(
        travel_diary_id=diary_id,
        title=title,
        text=text,
        date=date,
        photos=photos
    )
    assert created_entry is not None
    assert created_entry.id is not None  # Garante que foi salvo no BD e tem um ID
    assert created_entry.title == title
    assert created_entry.text == text
    assert len(created_entry.photos) == 2
    assert created_entry.photos[0].filepath == "/path/to/photo1.jpg"

    entry_in_db = session.query(Entry).filter_by(id=created_entry.id).one()
    assert entry_in_db.title == "Primeiro Dia na Praia"

def test_create_entry_fails_when_diary_id_is_invalid(db_session):
    session = db_session
    service = EntryService(session)
    invalid_id = 666

    result = service.create(
        travel_diary_id=invalid_id,
        title="Título de Teste",
        text="Texto de Teste",
        date=datetime(2025, 7, 20),
        photos=[]
    )

    assert result is None

def test_create_entry_successfully_without_photo(populated_db_session):
    session = populated_db_session
    service = EntryService(session)
    diary_id = 1  # Sabemos que o ID é 1 por causa da nossa fixture
    title = "Primeiro Dia na Praia"
    text = "O dia foi ensolarado e o mar estava ótimo."
    date = datetime(2025, 7, 20)
    photos = []
    created_entry = service.create(
        travel_diary_id=diary_id,
        title=title,
        text=text,
        date=date,
        photos=photos
    )
    assert created_entry is not None
    assert created_entry.id is not None  # Garante que foi salvo no BD e tem um ID
    assert created_entry.title == title
    assert created_entry.text == text
    assert len(created_entry.photos) == 0
    entry_in_db = session.query(Entry).filter_by(id=created_entry.id).one()
    assert entry_in_db.title == "Primeiro Dia na Praia"

def test_create_entry_fails_with_null_title(populated_db_session):
    session = populated_db_session
    service = EntryService(session)
    diary_id = 1
    with pytest.raises(IntegrityError):
        service.create(
            travel_diary_id=diary_id,
            title=None,
            text="Um texto qualquer.",
            date=datetime.now(),
            photos=[]
        )

def test_create_entry_fails_with_null_date(populated_db_session):
    session = populated_db_session
    service = EntryService(session)
    diary_id = 1
    with pytest.raises(IntegrityError):
        service.create(
            travel_diary_id=diary_id,
            title="Sabado de sol",
            text="Um texto qualquer.",
            date=None,
            photos=[]
        )

def test_create_entry_fails_with_null_diary_id(populated_db_session):
    session = populated_db_session
    service = EntryService(session)
    diary_id = 1
    result = service.create(
            travel_diary_id=None,
            title="Sabado de sol",
            text="Um texto qualquer.",
            date=datetime.now(),
            photos=[]
        )
    assert result is None