from datetime import datetime
from typing import List

from ..models.entry import Entry
from ..models.travel_diary import TravelDiary


class EntryService:
    def __init__(self,session):
        self.session = session

    def create(self, travel_diary_id:int, title: str, text: str, date: datetime, ):
        travel_diary = self.session.query(TravelDiary).filter(TravelDiary.id == travel_diary_id).first()
        if not travel_diary:
            return None
        new_entry = Entry(title,text,date,travel_diary_id)
        self.session.add(new_entry)
        self.session.commit()
        self.session.refresh(new_entry)
        return new_entry

    def read_by_id(self,entry_id:int)->Entry:
        entry = self.session.query(Entry).filter(Entry.id == entry_id).first()
        return entry

    def read_all(self)-> List[Entry]:
        entries = self.session.query(Entry).all()
        return entries

    def update(self,entry_src:Entry,entry_dst:Entry) -> Entry | None:
        original:Entry = self.read_by_id(entry_src.id)
        if original:
            original.title = entry_dst.title
            original.text = entry_dst.text
            original.date = entry_dst.date
            original.fk_travel_diary_id = entry_dst.fk_travel_diary_id
            original.photos = entry_dst.photos
            self.session.commit()
            self.session.refresh(original)
            return original
        return None

    def delete(self,entry_src:Entry)-> Entry | None:
        excluded = self.read_by_id(entry_src.id)
        if excluded is not None:
            self.session.delete(excluded)
            self.session.commit()
            return excluded
        return None
