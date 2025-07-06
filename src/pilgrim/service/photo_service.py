import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from pilgrim.models.photo import Photo
from pilgrim.models.travel_diary import TravelDiary
from pilgrim.utils import DirectoryManager


class PhotoService:
    def __init__(self, session):
        self.session = session

    def _hash_file(self, filepath: Path) -> str:
        """Calculate hash of a file using SHA3-384."""
        hash_func = hashlib.new('sha3_384')
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def _ensure_images_directory(self, travel_diary: TravelDiary) -> Path:
        """
        Ensures the images directory exists for the given diary.
        Returns the path to the images directory.
        """
        images_dir = DirectoryManager.get_diary_images_directory(travel_diary.directory_name)

        if not images_dir.exists():
            images_dir.mkdir(parents=True)
            os.chmod(images_dir, 0o700)  # Ensure correct permissions

        return images_dir

    def _copy_photo_to_diary(self, source_path: Path, travel_diary: TravelDiary) -> Path:
        """
        Copies a photo to the diary's images directory.
        Returns the path to the copied file.
        """
        images_dir = self._ensure_images_directory(travel_diary)

        # Get original filename and extension
        original_name = Path(source_path).name

        # Create destination path
        dest_path = images_dir / original_name

        # If file with same name exists, add a number
        counter = 1
        while dest_path.exists():
            name_parts = original_name.rsplit('.', 1)
            if len(name_parts) > 1:
                dest_path = images_dir / f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                dest_path = images_dir / f"{original_name}_{counter}"
            counter += 1

        # Copy the file
        shutil.copy2(source_path, dest_path)
        os.chmod(dest_path, 0o600)  # Read/write for owner only

        return dest_path

    def create(self, filepath: Path, name: str, travel_diary_id: int, caption=None, addition_date=None) -> Photo | None:
        travel_diary = self.session.query(TravelDiary).filter(TravelDiary.id == travel_diary_id).first()
        if not travel_diary:
            return None

        # Copy photo to diary's images directory
        copied_path = self._copy_photo_to_diary(filepath, travel_diary)
        
        # Convert addition_date string to datetime if needed
        if isinstance(addition_date, str):
            try:
                addition_date = datetime.strptime(addition_date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                addition_date = None

        # Calculate hash from the copied file
        photo_hash = self._hash_file(copied_path)
        
        new_photo = Photo(
            filepath=str(copied_path),  # Store the path to the copied file
            name=name, 
            caption=caption, 
            fk_travel_diary_id=travel_diary_id,
            addition_date=addition_date,
            photo_hash=photo_hash
        )
        self.session.add(new_photo)
        self.session.commit()
        self.session.refresh(new_photo)

        return new_photo

    def read_by_id(self, photo_id:int) -> Photo:
        return self.session.query(Photo).get(photo_id)

    def read_all(self) -> List[Photo]:
        return self.session.query(Photo).all()

    def update(self, photo_src: Photo, photo_dst: Photo) -> Photo | None:
        original: Photo = self.read_by_id(photo_src.id)
        if original:
            # If filepath changed, need to copy new file
            if str(photo_dst.filepath) != str(original.filepath):
                travel_diary = self.session.query(TravelDiary).filter(
                    TravelDiary.id == original.fk_travel_diary_id).first()
                if travel_diary:
                    # Copy new photo
                    new_path = self._copy_photo_to_diary(Path(photo_dst.filepath), travel_diary)
                    # Delete old photo if it exists in our images directory
                    old_path = Path(original.filepath)
                    if old_path.exists() and str(DirectoryManager.get_diaries_root()) in str(old_path):
                        old_path.unlink()
                    original.filepath = str(new_path)
                    # Update hash based on the new copied file
                    original.photo_hash = self._hash_file(new_path)
            
            original.name = photo_dst.name
            original.addition_date = photo_dst.addition_date
            original.caption = photo_dst.caption

            if photo_dst.entries and len(photo_dst.entries) > 0:
                if original.entries is None:
                    original.entries = []
                original.entries = photo_dst.entries  # Replace instead of extend

            self.session.commit()
            self.session.refresh(original)
            return original
        return None

    def delete(self, photo_src: Photo) -> Photo | None:
        excluded = self.read_by_id(photo_src.id)
        if excluded:
            # Store photo data before deletion
            deleted_photo = Photo(
                filepath=excluded.filepath,
                name=excluded.name,
                addition_date=excluded.addition_date,
                caption=excluded.caption,
                fk_travel_diary_id=excluded.fk_travel_diary_id,
                id=excluded.id,
                photo_hash=excluded.photo_hash,
                entries=excluded.entries,
            )

            # Delete the physical file if it exists in our images directory
            file_path = Path(excluded.filepath)
            if file_path.exists() and str(DirectoryManager.get_diaries_root()) in str(file_path):
                file_path.unlink()
            
            self.session.delete(excluded)
            self.session.commit()
            
            return deleted_photo
        return None
