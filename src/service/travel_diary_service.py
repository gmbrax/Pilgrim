from src.models.travel_diary import TravelDiary


class TravelDiaryService:
    def __init__(self,session):
        self.session = session
    def create(self, name:str):
        new_travel_diary = TravelDiary(name)
        self.session.add(new_travel_diary)
        self.session.commit()
        self.session.refresh(new_travel_diary)

        return new_travel_diary

    def read_by_id(self, travel_id:int):
        return self.session.query(TravelDiary).get(travel_id)

    def read_all(self):
        return self.session.query(TravelDiary).all()

    def update(self, travel_diary_src:TravelDiary,travel_diary_dst:TravelDiary):
        original = self.read_by_id(travel_diary_src.id)
        if original is not None:
            original.name = travel_diary_dst.name
            self.session.commit()
            self.session.refresh(original)
        return original

    def delete(self, travel_diary_src:TravelDiary):
        excluded = self.read_by_id(travel_diary_src.id)
        if excluded is not None:
            self.session.delete(travel_diary_src)
            self.session.commit()
            return excluded
        return None
