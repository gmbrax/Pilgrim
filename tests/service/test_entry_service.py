from re import search

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

@pytest.fixture
def session_with_an_entry(populated_db_session):
    session = populated_db_session
    initial_entry = Entry(
        title="Título Original",
        text="Texto original.",
        date=datetime(2025, 1, 1),
        travel_diary_id=1
    )
    session.add(initial_entry)
    session.commit()
    return session, initial_entry.id

@pytest.fixture
def session_with_multiple_entries(populated_db_session):
    """Fixture que cria um diário e duas entradas para ele."""
    session = populated_db_session

    entry1 = Entry(title="Entrada 1", text="Texto 1", date=datetime(2025, 1, 1), travel_diary_id=1)
    entry2 = Entry(title="Entrada 2", text="Texto 2", date=datetime(2025, 1, 2), travel_diary_id=1)

    session.add_all([entry1, entry2])
    session.commit()

    return session

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
def test_ready_by_id_successfully(session_with_an_entry):
    session,_ = session_with_an_entry
    service = EntryService(session)
    search_id = 1
    result = service.read_by_id(search_id)
    assert result is not None
def test_ready_by_id_fails_when_id_is_invalid(db_session):
    session = db_session
    service = EntryService(session)
    invalid_id = 666
    result = service.read_by_id(invalid_id)
    assert result is None

def test_read_all_returns_all_entries(session_with_multiple_entries):
    session = session_with_multiple_entries
    service = EntryService(session)
    all_entries = service.read_all()
    assert isinstance(all_entries, list)
    assert len(all_entries) == 2
    assert all_entries[0].title == "Entrada 1"
    assert all_entries[1].title == "Entrada 2"

def test_read_all_returns_empty_list_on_empty_db(db_session):
    session = db_session
    service = EntryService(session)
    all_entries = service.read_all()
    assert isinstance(all_entries, list)
    assert len(all_entries) == 0

def test_update_entry_successfully(session_with_an_entry):
    session, entry_id = session_with_an_entry
    service = EntryService(session)
    entry_src = session.query(Entry).filter_by(id=entry_id).one()
    new_date = datetime(2025, 1, 2)
    entry_dst = Entry(
        title="Título Atualizado",
        text="Texto atualizado.",
        date=new_date,
        travel_diary_id=1,  # Mantemos o mesmo travel_diary_id
        photos=[]
    )
    updated_entry = service.update(entry_src, entry_dst)
    assert updated_entry is not None
    assert updated_entry.id == entry_id
    assert updated_entry.title == "Título Atualizado"
    assert updated_entry.text == "Texto atualizado."
    entry_in_db = session.query(Entry).filter_by(id=entry_id).one()
    assert entry_in_db.title == "Título Atualizado"

def test_update_entry_fails_if_entry_does_not_exist(db_session):
    service = EntryService(db_session)
    non_existent_entry = Entry(
        title="dummy",
        text="dummy",
        date=datetime.now(),
        travel_diary_id=1)
    non_existent_entry.id = 999
    entry_with_new_data = Entry(title="Novo Título", text="Novo Texto", date=datetime.now(), travel_diary_id=1)
    result = service.update(non_existent_entry, entry_with_new_data)
    assert result is None

def test_update_fails_with_null_title(session_with_an_entry):
    session, entry_id = session_with_an_entry
    service = EntryService(session)
    entry_src = session.query(Entry).filter_by(id=entry_id).one()
    entry_dst = Entry(
        title=None,
        text="Texto atualizado.",
        date=datetime.now(),
        travel_diary_id=1,
        photos=[]
    )
    with pytest.raises(IntegrityError):
        service.update(entry_src, entry_dst)

def test_update_fails_with_null_date(session_with_an_entry):
    session, entry_id = session_with_an_entry
    service = EntryService(session)
    entry_src = session.query(Entry).filter_by(id=entry_id).one()
    entry_dst = Entry(
        title=entry_src.title,
        text="Texto atualizado.",
        date=None,
        travel_diary_id=1,
        photos=[]
    )
    with pytest.raises(IntegrityError):
        service.update(entry_src, entry_dst)

def test_update_fails_with_null_diary_id(session_with_an_entry):
    session, entry_id = session_with_an_entry
    service = EntryService(session)
    entry_src = session.query(Entry).filter_by(id=entry_id).one()
    entry_dst = Entry(
        title=entry_src.title,
        text="Texto atualizado.",
        date=datetime.now(),
        travel_diary_id=None,
        photos=[]
    )
    with pytest.raises(IntegrityError):
        service.update(entry_src, entry_dst)

def test_delete_successfully_removes_entry(session_with_an_entry):
    session, entry_id = session_with_an_entry
    service = EntryService(session)
    entry_to_delete = service.read_by_id(entry_id)
    assert entry_to_delete is not None
    deleted_entry = service.delete(entry_to_delete)
    assert deleted_entry is not None
    assert deleted_entry.id == entry_id
    entry_in_db = service.read_by_id(entry_id)
    assert entry_in_db is None

def test_delete_returns_none_if_entry_does_not_exist(db_session):
    service = EntryService(db_session)
    non_existent_entry = Entry(
        title="dummy",
        text="dummy",
        date=datetime.now(),
        travel_diary_id=1)
    non_existent_entry.id = 999
    result = service.delete(non_existent_entry)
    assert result is None
