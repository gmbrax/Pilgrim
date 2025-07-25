import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from pilgrim.service.backup_service import BackupService
from pilgrim.utils.directory_manager import DirectoryManager
import pytest

@patch.object(DirectoryManager, 'get_diaries_root')
@patch.object(DirectoryManager, 'get_config_directory')
@patch.object(DirectoryManager, 'get_database_path')
def test_create_backup_success(mock_get_db_path, mock_get_config_dir, mock_get_diaries_root, backup_test_env_files_only):
    env = backup_test_env_files_only
    session = env["session"]
    mock_get_db_path.return_value = env["db_path"]
    mock_get_config_dir.return_value = env["config_dir"]
    mock_get_diaries_root.return_value = env["diaries_root"]

    service = BackupService(session)
    backup_zip_path = env["config_dir"] / "backup.zip"
    success, returned_path = service.create_backup()
    assert success is True
    assert returned_path == backup_zip_path
    assert backup_zip_path.exists()

    with zipfile.ZipFile(backup_zip_path, 'r') as zf:
        file_list = zf.namelist()
        assert "database.sql" in file_list
        assert "diaries/viagem_de_teste/images/foto1.jpg" in file_list
        sql_dump = zf.read("database.sql").decode('utf-8')
        assert "Viagem de Teste" in sql_dump

@patch.object(DirectoryManager, 'get_database_path')
def test_create_backup_fails_if_db_not_found(mock_get_db_path, tmp_path: Path):
    non_existent_db_path = tmp_path / "non_existent.db"
    mock_get_db_path.return_value = non_existent_db_path
    mock_session = MagicMock()
    service = BackupService(mock_session)
    with pytest.raises(FileNotFoundError, match="No Database Found"):
        service.create_backup()