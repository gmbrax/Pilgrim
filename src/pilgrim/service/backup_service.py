import sqlite3
import zipfile
from pathlib import Path


from pilgrim.utils.directory_manager import DirectoryManager


class BackupService:
    def __init__(self, session):
        self.session = session

    def create_backup(self):
        db_path = DirectoryManager.get_database_path()
        if not db_path.exists():
            raise FileNotFoundError("No Database Found")

        with self.session.connection() as conn:
            raw_conn = conn.connection
            dump =  dump = "\n".join(line for line in raw_conn.iterdump())

        filename = DirectoryManager.get_config_directory() / "backup.zip"
        diaries_root_path = DirectoryManager.get_diaries_root()

        try:
            with zipfile.ZipFile(filename, "w",zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr("database.sql", dump)
                if diaries_root_path.exists():
                    for file_path in diaries_root_path.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(diaries_root_path.parent)
                            zipf.write(file_path, arcname=arcname)
                return True, filename
        except Exception as e:
            return False, str(e)

