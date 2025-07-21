import pytest
from pathlib import Path
from pilgrim.service.photo_service import PhotoService
import hashlib
from unittest.mock import patch
from pilgrim.models.photo import Photo

@patch.object(PhotoService, '_copy_photo_to_diary')
@patch.object(PhotoService, 'hash_file', return_value="fake_hash_123")
def test_create_photo_successfully(mock_hash, mock_copy, session_with_one_diary):
    session, diary = session_with_one_diary
    service = PhotoService(session)
    fake_source_path = Path("/path/original/imagem.jpg")
    fake_copied_path = Path(f"~/.pilgrim/diaries/{diary.directory_name}/images/imagem.jpg")
    mock_copy.return_value = fake_copied_path
    new_photo = service.create(
        filepath=fake_source_path,
        name="Foto da Praia",
        travel_diary_id=diary.id,
        caption="Pôr do sol")
    mock_hash.assert_called_once_with(fake_source_path)
    mock_copy.assert_called_once_with(fake_source_path, diary)
    assert new_photo is not None
    assert new_photo.name == "Foto da Praia"
    assert new_photo.photo_hash == "fake_hash_123"
    assert new_photo.filepath == str(fake_copied_path)

def test_hash_file_generates_correct_hash(tmp_path: Path):
    original_content_bytes = b"um conteudo de teste para o hash"
    file_on_disk = tmp_path / "test.jpg"
    file_on_disk.write_bytes(original_content_bytes)
    hash_from_file = PhotoService.hash_file(file_on_disk)
    expected_hash_func = hashlib.new('sha3_384')
    expected_hash_func.update(original_content_bytes)
    hash_from_memory = expected_hash_func.hexdigest()
    assert hash_from_file == hash_from_memory

@patch.object(PhotoService, '_copy_photo_to_diary')
@patch.object(PhotoService, 'hash_file', return_value="hash_ja_existente")
def test_create_photo_returns_none_if_hash_exists(mock_hash, mock_copy, session_with_one_diary):
    session, diary = session_with_one_diary
    existing_photo = Photo(
        filepath="/path/existente.jpg", name="Foto Antiga",
        photo_hash="hash_ja_existente", fk_travel_diary_id=diary.id
    )
    session.add(existing_photo)
    session.commit()

    service = PhotoService(session)
    new_photo = service.create(
        filepath=Path("/path/novo/arquivo.jpg"),
        name="Foto Nova",
        travel_diary_id=diary.id
    )
    assert new_photo is None
    mock_copy.assert_not_called()

def test_read_by_id_successfully(session_with_photos):
    session, photos = session_with_photos
    service = PhotoService(session)
    photo_to_find_id = photos[0].id
    found_photo = service.read_by_id(photo_to_find_id)
    assert found_photo is not None
    assert found_photo.id == photo_to_find_id
    assert found_photo.name == "Foto 1"

def test_read_by_id_returns_none_for_invalid_id(db_session):
    service = PhotoService(db_session)
    result = service.read_by_id(999)
    assert result is None

def test_read_all_returns_all_photos(session_with_photos):
    session, _ = session_with_photos
    service = PhotoService(session)
    all_photos = service.read_all()

    assert isinstance(all_photos, list)
    assert len(all_photos) == 2
    assert all_photos[0].name == "Foto 1"
    assert all_photos[1].name == "Foto 2"

def test_read_all_returns_empty_list_for_empty_db(db_session):
    service = PhotoService(db_session)
    all_photos = service.read_all()
    assert isinstance(all_photos, list)
    assert len(all_photos) == 0

def test_check_photo_by_hash_finds_existing_photo(session_with_photos):
    session, photos = session_with_photos
    service = PhotoService(session)
    existing_photo = photos[0]
    hash_to_find = existing_photo.photo_hash  # "hash1"
    diary_id = existing_photo.fk_travel_diary_id  # 1
    found_photo = service.check_photo_by_hash(hash_to_find, diary_id)
    assert found_photo is not None
    assert found_photo.id == existing_photo.id
    assert found_photo.photo_hash == hash_to_find

def test_check_photo_by_hash_returns_none_when_not_found(session_with_photos):
    session, photos = session_with_photos
    service = PhotoService(session)
    existing_hash = photos[0].photo_hash  # "hash1"
    existing_diary_id = photos[0].fk_travel_diary_id  # 1
    result1 = service.check_photo_by_hash("hash_inexistente", existing_diary_id)
    assert result1 is None
    invalid_diary_id = 999
    result2 = service.check_photo_by_hash(existing_hash, invalid_diary_id)
    assert result2 is None