from pathlib import Path
from typing import List


from pilgrim.models.photo import Photo
from pilgrim.models.travel_diary import TravelDiary

class PhotoService:
    def __init__(self, session):
        self.session = session

    def create(self, filepath:Path, name:str, travel_diary_id, addition_date=None, caption=None, ) -> Photo | None:
        travel_diary = self.session.query(TravelDiary).filter(TravelDiary.id == travel_diary_id).first()
        if not travel_diary:
            return None
        new_photo = Photo(filepath, name, addition_date=addition_date, caption=caption)
        self.session.add(new_photo)
        self.session.commit()
        self.session.refresh(new_photo)

        return new_photo
    def read_by_id(self, photo_id:int) -> Photo:
        return self.session.query(Photo).get(photo_id)

    def read_all(self) -> List[Photo]:
        return self.session.query(Photo).all()

    def update(self,photo_src:Photo,photo_dst:Photo) -> Photo | None:
        original:Photo = self.read_by_id(photo_src.id)
        if original:
            original.filepath = photo_dst.filepath
            original.name = photo_dst.name
            original.addition_date = photo_dst.addition_date
            original.caption = photo_dst.caption
            original.entries.extend(photo_dst.entries)
            self.session.commit()
            self.session.refresh(original)
            return original
        return None

    def delete(self, photo_src:Photo) -> Photo | None:
        excluded = self.read_by_id(photo_src.id)
        if excluded:
            self.session.delete(excluded)
            self.session.commit()
            self.session.refresh(excluded)
            return excluded
        return None
