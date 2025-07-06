import os
from pathlib import Path


class DirectoryManager:
    @staticmethod
    def get_config_directory() -> Path:
        """
        Get the ~/.pilgrim directory path.
        Creates it if it doesn't exist.
        """
        home = Path.home()
        config_dir = home / ".pilgrim"
        config_dir.mkdir(exist_ok=True)
        os.chmod(config_dir, 0o700)
        return config_dir

    @staticmethod
    def get_diaries_root() -> Path:
        """Returns the path to the diaries directory."""
        diaries_dir = DirectoryManager.get_config_directory() / "diaries"
        diaries_dir.mkdir(exist_ok=True)
        os.chmod(diaries_dir, 0o700)
        return diaries_dir

    @staticmethod
    def get_diary_directory(directory_name: str) -> Path:
        """Returns the directory path for a specific diary."""
        return DirectoryManager.get_diaries_root() / directory_name

    @staticmethod
    def get_diary_data_directory(directory_name: str) -> Path:
        """Returns the data directory path for a specific diary."""
        return DirectoryManager.get_diary_directory(directory_name) / "data"

    @staticmethod
    def get_diary_images_directory(directory_name: str) -> Path:
        """Returns the images directory path for a specific diary."""
        return DirectoryManager.get_diary_data_directory(directory_name) / "images"
