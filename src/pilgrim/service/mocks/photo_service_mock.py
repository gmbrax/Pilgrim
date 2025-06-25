from pathlib import Path
from typing import List

from pilgrim.models.photo import Photo
from pilgrim.service.photo_service import PhotoService


class PhotoServiceMock(PhotoService):
    def __init__(self):
        super().__init__(None)
        self.mock_data = {}
        self._next_id = 1

    def create(self, filepath: Path, name: str, travel_diary_id, addition_date=None, caption=None) -> Photo | None:
        new_photo = Photo(filepath, name, addition_date=addition_date, caption=caption)
        self.mock_data[self._next_id] = new_photo
        self._next_id += 1
        return new_photo


    def read_by_id(self, photo_id: int) -> Photo:
        return self.mock_data.get(photo_id)

    def read_all(self) -> List[Photo]:
        return list(self.mock_data.values())

    def update(self, photo_id: Photo, photo_dst: Photo) -> Photo | None:
        item_to_update:Photo = self.mock_data.get(photo_id)
        if item_to_update:
            item_to_update.filepath = photo_dst.filepath if photo_dst.filepath else item_to_update.filepath
            item_to_update.name = photo_dst.name if photo_dst.name else item_to_update.name
            item_to_update.caption = photo_dst.caption if photo_dst.caption else item_to_update.caption
            item_to_update.addition_date = photo_dst.addition_date if photo_dst.addition_date\
                else item_to_update.addition_date
            item_to_update.fk_travel_diary_id = photo_dst.fk_travel_diary_id if photo_dst.fk_travel_diary_id \
                else item_to_update.fk_travel_diary_id
            item_to_update.entries.extend(photo_dst.entries)
            return item_to_update
        return None

    def delete(self, photo_id: int) -> Photo | None:
        return self.mock_data.pop(photo_id, None)
