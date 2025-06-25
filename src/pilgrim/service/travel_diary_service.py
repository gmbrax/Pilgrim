from ..models.travel_diary import TravelDiary
import asyncio

class TravelDiaryService:
    def __init__(self,session):
        self.session = session
    async def async_create(self, name:str):
        new_travel_diary = TravelDiary(name)
        self.session.add(new_travel_diary)
        self.session.commit()
        self.session.refresh(new_travel_diary)

        return new_travel_diary

    def read_by_id(self, travel_id:int):
        return self.session.query(TravelDiary).get(travel_id)

    def read_all(self):
        return self.session.query(TravelDiary).all()

    def update(self, travel_diary_id: int, name: str):
        original = self.read_by_id(travel_diary_id)
        if original is not None:
            original.name = name
            self.session.commit()
            self.session.refresh(original)
        return original

    async def async_update(self, travel_diary_id: int, name: str):
        return self.update(travel_diary_id, name)

    def delete(self, travel_diary_id: TravelDiary):
        excluded = self.read_by_id(travel_diary_id.id)
        if excluded is not None:
            self.session.delete(travel_diary_id)
            self.session.commit()
            return excluded
        return None
