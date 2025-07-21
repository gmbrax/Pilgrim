from unittest.mock import patch

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

def test_sanitize_directory_name_formats_string_correctly(db_session):
    service = TravelDiaryService(db_session)
    name1 = "Minha Primeira Viagem"
    assert service._sanitize_directory_name(name1) == "minha_primeira_viagem"
    name2 = "Viagem para o #Rio de Janeiro! @2025"
    assert service._sanitize_directory_name(name2) == "viagem_para_o_rio_de_janeiro_2025"
    name3 = "  Mochilão na Europa   "
    assert service._sanitize_directory_name(name3) == "mochilão_na_europa"

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