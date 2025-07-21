import shutil
from pathlib import Path
from unittest.mock import patch
import pytest

from pilgrim.utils.directory_manager import DirectoryManager

@patch('os.chmod')
@patch('pathlib.Path.home')
def test_get_config_directory_creates_dir_in_fake_home(mock_home, mock_chmod, tmp_path: Path):
    mock_home.return_value = tmp_path

    expected_config_dir = tmp_path / ".pilgrim"
    assert not expected_config_dir.exists()
    result_path = DirectoryManager.get_config_directory()
    assert result_path == expected_config_dir
    assert expected_config_dir.exists()
    mock_chmod.assert_called_once_with(expected_config_dir, 0o700)

@patch('shutil.copy2')
@patch('pathlib.Path.home')
def test_get_database_path_no_migration(mock_home, mock_copy, tmp_path: Path):
    mock_home.return_value = tmp_path
    expected_db_path = tmp_path / ".pilgrim" / "database.db"
    result_path = DirectoryManager.get_database_path()
    assert result_path == expected_db_path
    mock_copy.assert_not_called()

@patch('shutil.copy2')
@patch('pathlib.Path.home')
def test_get_database_path_with_migration(mock_home, mock_copy, tmp_path: Path, monkeypatch):
    fake_home_dir = tmp_path / "home"
    fake_project_dir = tmp_path / "project"
    fake_home_dir.mkdir()
    fake_project_dir.mkdir()

    (fake_project_dir / "database.db").touch()
    mock_home.return_value = fake_home_dir
    monkeypatch.chdir(fake_project_dir)
    result_path = DirectoryManager.get_database_path()
    expected_db_path = fake_home_dir / ".pilgrim" / "database.db"
    assert result_path == expected_db_path

    mock_copy.assert_called_once_with(
        Path("database.db"),
        expected_db_path
    )

@patch('os.chmod')
@patch('pathlib.Path.home')
def test_diary_path_methods_construct_correctly(mock_home, mock_chmod, tmp_path: Path):
    mock_home.return_value = tmp_path
    images_path = DirectoryManager.get_diary_images_directory("minha-viagem")
    expected_path = tmp_path / ".pilgrim" / "diaries" / "minha-viagem" / "data" / "images"
    assert images_path == expected_path
    assert (tmp_path / ".pilgrim" / "diaries").exists()

@patch('shutil.copy2')
@patch('pathlib.Path.home')
def test_get_database_path_handles_migration_error(mock_home, mock_copy, tmp_path: Path, monkeypatch):
    fake_home_dir = tmp_path / "home"
    fake_project_dir = tmp_path / "project"
    fake_home_dir.mkdir()
    fake_project_dir.mkdir()
    (fake_project_dir / "database.db").touch()
    mock_home.return_value = fake_home_dir
    mock_copy.side_effect = shutil.Error("O disco está cheio!")
    monkeypatch.chdir(fake_project_dir)
    with pytest.raises(RuntimeError, match="Failed to migrate database"):
        DirectoryManager.get_database_path()
    mock_copy.assert_called_once()
