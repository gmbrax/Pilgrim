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
