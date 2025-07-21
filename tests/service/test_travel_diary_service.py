from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

from pilgrim import TravelDiary
from pilgrim.service.travel_diary_service import TravelDiaryService

@patch.object(TravelDiaryService, '_ensure_diary_directory')
@pytest.mark.asyncio # Marca o teste para rodar código assíncrono
async def test_create_diary_successfully(mock_ensure_dir, db_session):
    service = TravelDiaryService(db_session)
    new_diary = await service.async_create("Viagem para a Serra")
    assert new_diary is not None
    assert new_diary.id is not None
    assert new_diary.name == "Viagem para a Serra"
    assert new_diary.directory_name == "viagem_para_a_serra"

@patch.object(TravelDiaryService, '_ensure_diary_directory')
@patch.object(TravelDiaryService, '_sanitize_directory_name', return_value="nome_existente")
@pytest.mark.asyncio
async def test_create_diary_handles_integrity_error(mock_sanitize, mock_ensure_dir, db_session):
    existing_diary = TravelDiary(name="Diário Antigo", directory_name="nome_existente")
    db_session.add(existing_diary)
    db_session.commit()
    service = TravelDiaryService(db_session)
    with pytest.raises(ValueError, match="Could not create diary"):
        await service.async_create("Qualquer Nome Novo")
    mock_ensure_dir.assert_not_called()

@patch.object(TravelDiaryService, '_ensure_diary_directory')
def test_read_by_id_successfully(mock_ensure_dir, session_with_one_diary):
    session, diary_to_find = session_with_one_diary
    service = TravelDiaryService(session)
    found_diary = service.read_by_id(diary_to_find.id)
    assert found_diary is not None
    assert found_diary.id == diary_to_find.id
    assert found_diary.name == "Diário de Teste"
    mock_ensure_dir.assert_called_once_with(found_diary)

@patch.object(TravelDiaryService, '_ensure_diary_directory')
def test_read_by_id_returns_none_for_invalid_id(mock_ensure_dir, db_session):
    service = TravelDiaryService(db_session)
    result = service.read_by_id(999)
    assert result is None
    mock_ensure_dir.assert_not_called()

@patch.object(TravelDiaryService, '_ensure_diary_directory')
def test_read_all_returns_all_diaries(mock_ensure_dir, db_session):
    d1 = TravelDiary(name="Diário 1", directory_name="d1")
    d2 = TravelDiary(name="Diário 2", directory_name="d2")
    db_session.add_all([d1, d2])
    db_session.commit()
    service = TravelDiaryService(db_session)
    diaries = service.read_all()
    assert isinstance(diaries, list)
    assert len(diaries) == 2
    assert mock_ensure_dir.call_count == 2

@patch.object(TravelDiaryService, '_ensure_diary_directory')
def test_read_all_returns_empty_list_for_empty_db(mock_ensure_dir, db_session):
    service = TravelDiaryService(db_session)
    diaries = service.read_all()
    assert isinstance(diaries, list)
    assert len(diaries) == 0
    mock_ensure_dir.assert_not_called()

@patch.object(TravelDiaryService, '_ensure_diary_directory')
@patch('pathlib.Path.rename')
@patch.object(TravelDiaryService, '_get_diary_directory')
def test_update_diary_successfully(mock_get_dir, mock_path_rename, mock_ensure, session_with_one_diary):
    session, diary_to_update = session_with_one_diary
    service = TravelDiaryService(session)
    old_path = MagicMock(spec=Path)  # Um mock que se parece com um objeto Path
    old_path.exists.return_value = True  # Dizemos que o diretório antigo "existe"
    new_path = Path("/fake/path/diario_atualizado")
    mock_get_dir.side_effect = [old_path, new_path]
    updated_diary = service.update(diary_to_update.id, "Diário Atualizado")
    assert updated_diary is not None
    assert updated_diary.name == "Diário Atualizado"
    assert updated_diary.directory_name == "diario_atualizado"
    old_path.rename.assert_called_once_with(new_path)

def test_update_returns_none_for_invalid_id(db_session):
    service = TravelDiaryService(db_session)
    result = service.update(travel_diary_id=999, name="Nome Novo")
    assert result is None

@patch.object(TravelDiaryService, '_cleanup_diary_directory')
def test_delete_diary_successfully(mock_cleanup, session_with_one_diary):
    session, diary_to_delete = session_with_one_diary
    service = TravelDiaryService(session)
    result = service.delete(diary_to_delete)
    assert result is not None
    assert result.id == diary_to_delete.id
    mock_cleanup.assert_called_once_with(diary_to_delete)
    diary_in_db = service.read_by_id(diary_to_delete.id)
    assert diary_in_db is None

@patch.object(TravelDiaryService, '_cleanup_diary_directory')
def test_delete_returns_none_for_non_existent_diary(mock_cleanup, db_session):
    service = TravelDiaryService(db_session)
    non_existent_diary = TravelDiary(name="dummy", directory_name="dummy")
    non_existent_diary.id = 999
    result = service.delete(non_existent_diary)
    assert result is None
    mock_cleanup.assert_not_called()

@patch.object(TravelDiaryService, '_sanitize_directory_name')
def test_update_raises_value_error_on_name_collision(mock_sanitize, db_session):

    d1 = TravelDiary(name="Diário A", directory_name="diario_a")
    d2 = TravelDiary(name="Diário B", directory_name="diario_b")
    db_session.add_all([d1, d2])
    db_session.commit()
    db_session.refresh(d1)
    mock_sanitize.return_value = "diario_b"
    service = TravelDiaryService(db_session)
    with pytest.raises(ValueError, match="Could not update diary"):
        service.update(d1.id, "Diário B")

def test_sanitize_directory_name_formats_string_correctly(db_session):
    service = TravelDiaryService(db_session)
    name1 = "Minha Primeira Viagem"
    assert service._sanitize_directory_name(name1) == "minha_primeira_viagem"
    name2 = "Viagem para o #Rio de Janeiro! @2025"
    assert service._sanitize_directory_name(name2) == "viagem_para_o_rio_de_janeiro_2025"
    name3 = "  Mochilão na Europa   "
    assert service._sanitize_directory_name(name3) == "mochilao_na_europa"

def test_sanitize_directory_name_handles_uniqueness(db_session):
    existing_diary = TravelDiary(name="Viagem para a Praia", directory_name="viagem_para_a_praia")
    db_session.add(existing_diary)
    db_session.commit()
    service = TravelDiaryService(db_session)
    new_sanitized_name = service._sanitize_directory_name("Viagem para a Praia")
    assert new_sanitized_name == "viagem_para_a_praia_1"
    another_diary = TravelDiary(name="Outra Viagem", directory_name="viagem_para_a_praia_1")
    db_session.add(another_diary)
    db_session.commit()

    third_sanitized_name = service._sanitize_directory_name("Viagem para a Praia")
    assert third_sanitized_name == "viagem_para_a_praia_2"