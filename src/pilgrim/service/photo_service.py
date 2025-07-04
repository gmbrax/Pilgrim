from pathlib import Path
from typing import List
from datetime import datetime
import hashlib


from pilgrim.models.photo import Photo
from pilgrim.models.travel_diary import TravelDiary

class PhotoService:
    def __init__(self, session):
        self.session = session
    def _hash_file(self,filepath):
        hash_func = hashlib.new('sha3_384')
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def create(self, filepath: Path, name: str, travel_diary_id: int, caption=None, addition_date=None) -> Photo | None:
        travel_diary = self.session.query(TravelDiary).filter(TravelDiary.id == travel_diary_id).first()
        if not travel_diary:
            return None
        
        # Convert addition_date string to datetime if needed
        if isinstance(addition_date, str):
            try:
                addition_date = datetime.strptime(addition_date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                addition_date = None
        
        new_photo = Photo(
            filepath=filepath, 
            name=name, 
            caption=caption, 
            fk_travel_diary_id=travel_diary_id,
            addition_date=addition_date,
            photo_hash=self._hash_file(filepath)
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
            original.filepath = photo_dst.filepath
            original.name = photo_dst.name
            original.addition_date = photo_dst.addition_date
            original.caption = photo_dst.caption
            original.photo_hash = original.photo_hash
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
            
            self.session.delete(excluded)
            self.session.commit()
            
            return deleted_photo
        return None
