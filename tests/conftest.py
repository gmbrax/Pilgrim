import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pilgrim.database import Base
from pilgrim.models.travel_diary import TravelDiary
from pilgrim.models.photo import Photo

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


@pytest.fixture
def session_with_photos(session_with_one_diary):
    session, diary = session_with_one_diary

    # Usamos a mesma raiz de diretório que o mock do teste espera
    diaries_root = "/fake/diaries_root"

    photo1 = Photo(
        # CORREÇÃO: O caminho agora inclui a raiz e a subpasta 'images'
        filepath=f"{diaries_root}/{diary.directory_name}/images/p1.jpg",
        name="Foto 1",
        photo_hash="hash1",
        fk_travel_diary_id=diary.id
    )
    photo2 = Photo(
        filepath=f"{diaries_root}/{diary.directory_name}/images/p2.jpg",
        name="Foto 2",
        photo_hash="hash2",
        fk_travel_diary_id=diary.id
    )

    session.add_all([photo1, photo2])
    session.commit()

    return session, [photo1, photo2]