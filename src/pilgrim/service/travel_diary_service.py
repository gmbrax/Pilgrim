import os
import re
import shutil
from pathlib import Path

from pilgrim.models.entry import Entry
from pilgrim.utils import DirectoryManager
from sqlalchemy.exc import IntegrityError

from pilgrim.models.travel_diary import TravelDiary
from unidecode import unidecode

from pilgrim.service.photo_service import PhotoService
from pilgrim.service.entry_service import EntryService

class TravelDiaryService:
    def __init__(self, session):
        self.session = session

    def _sanitize_directory_name(self, name: str) -> str:
        """
        Sanitizes a diary name for use as a directory name.
        - Removes special characters
        - Replaces spaces with underscores
        - Ensures name is unique by adding a suffix if needed
        """
        transliterated_name = unidecode(name)

        # Remove special characters and replace spaces
        safe_name = re.sub(r'[^\w\s-]', '', transliterated_name)
        safe_name = safe_name.strip().replace(' ', '_').lower()

        # Ensure we have a valid name
        if not safe_name:
            safe_name = "unnamed_diary"

        # Check if name is already used in database
        base_name = safe_name
        counter = 1
        while self.session.query(TravelDiary).filter_by(directory_name=safe_name).first() is not None:
            safe_name = f"{base_name}_{counter}"
            counter += 1

        return safe_name

    def _get_diary_directory(self, diary: TravelDiary) -> Path:
        """Returns the directory path for a diary."""
        return DirectoryManager.get_diary_directory(diary.directory_name)

    def _get_diary_data_directory(self, diary: TravelDiary) -> Path:
        """Returns the data directory path for a diary."""
        return DirectoryManager.get_diary_data_directory(diary.directory_name)

    def _ensure_diary_directory(self, diary: TravelDiary) -> Path:
        """
        Creates and returns the directory structure for a diary:
        ~/.pilgrim/diaries/{directory_name}/data/
        """
        # Create diary directory
        diary_dir = self._get_diary_directory(diary)
        diary_dir.mkdir(exist_ok=True)
        os.chmod(diary_dir, 0o700)

        # Create data subdirectory
        data_dir = self._get_diary_data_directory(diary)
        data_dir.mkdir(exist_ok=True)
        os.chmod(data_dir, 0o700)

        return data_dir

    def _cleanup_diary_directory(self, diary: TravelDiary):
        """Removes the diary directory and all its contents."""
        diary_dir = self._get_diary_directory(diary)
        if diary_dir.exists():
            shutil.rmtree(diary_dir)

    async def async_create(self, name: str):
        # Generate safe directory name
        directory_name = self._sanitize_directory_name(name)

        # Create diary with directory name
        new_travel_diary = TravelDiary(name=name, directory_name=directory_name)

        try:
            self.session.add(new_travel_diary)
            self.session.commit()
            self.session.refresh(new_travel_diary)

            # Create directory structure for the new diary
            self._ensure_diary_directory(new_travel_diary)

            return new_travel_diary
        except IntegrityError:
            self.session.rollback()
            raise ValueError(f"Could not create diary: directory name '{directory_name}' already exists")

    def read_by_id(self, travel_id: int):
        diary = self.session.query(TravelDiary).get(travel_id)
        if diary:
            # Ensure directory exists when reading
            self._ensure_diary_directory(diary)
        return diary

    def read_all(self):
        diaries = self.session.query(TravelDiary).all()
        # Ensure directories exist for all diaries
        for diary in diaries:
            self._ensure_diary_directory(diary)
        return diaries

    def update(self, travel_diary_id: int, name: str):
        original = self.read_by_id(travel_diary_id)
        if original is not None:
            try:
                # Generate new directory name
                new_directory_name = self._sanitize_directory_name(name)
                old_directory = self._get_diary_directory(original)

                # Update diary
                original.name = name
                original.directory_name = new_directory_name
                self.session.commit()
                self.session.refresh(original)

                # Rename directory if it exists
                new_directory = self._get_diary_directory(original)
                if old_directory.exists() and old_directory != new_directory:
                    old_directory.rename(new_directory)

                return original
            except IntegrityError:
                self.session.rollback()
                raise ValueError(f"Could not update diary: directory name '{new_directory_name}' already exists")

        return None

    async def async_update(self, travel_diary_id: int, name: str):
        return self.update(travel_diary_id, name)

    def delete(self, travel_diary_id: TravelDiary):
        excluded = self.read_by_id(travel_diary_id.id)
        if excluded is not None:
            try:
                # First delete the directory
                self._cleanup_diary_directory(excluded)
                # Then delete from database
                self.session.delete(travel_diary_id)
                self.session.commit()
                return excluded
            except Exception as e:
                self.session.rollback()
                raise ValueError(f"Could not delete diary: {str(e)}")
        return None

    def delete_all_entries(self,travel_diary: TravelDiary):
        diary = self.read_by_id(travel_diary.id)
        if diary is not None:
           diary.entries = []
           self.session.commit()


           return True

        return False

    def delete_all_photos(self,travel_diary: TravelDiary):
        diary = self.read_by_id(travel_diary.id)
        photo_service = PhotoService(self.session)
        entry_service = EntryService(self.session)
        if diary is not None:

           for entry in list(diary.entries):
               entry_service.delete_all_photo_references(entry,commit=False)

           for photo in list(diary.photos):
               photo_service.delete(photo,commit=False)

           self.session.commit()

           return True

        return False
