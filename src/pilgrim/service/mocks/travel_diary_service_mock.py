from pilgrim.service.travel_diary_service import TravelDiaryService
from pilgrim.models.travel_diary import TravelDiary


class TravelDiaryServiceMock(TravelDiaryService):
    def __init__(self):
        super().__init__(None)
        self.mock_data = {
            1:TravelDiary(id=1,name="Montreal"),
            2:TravelDiary(id=2,name="Rio de Janeiro"),
        }
        self._next_id = 3

    def create(self, name: str):
        new_travel_diary = TravelDiary(id=self._next_id,name=name)
        self.mock_data[self._next_id] = new_travel_diary
        self._next_id += 1
        return new_travel_diary

    def read_by_id(self, travel_id: int):
        return self.mock_data[travel_id]

    def read_all(self):
        return list(self.mock_data.values())

    def update(self, travel_diary_id: int, travel_diary_dst: TravelDiary):
        item_to_update = self.mock_data.get(travel_diary_id)
        if item_to_update:
            item_to_update.name = travel_diary_dst.name if travel_diary_dst.name is not None else item_to_update.name
            return item_to_update
        return None

    def delete(self, travel_diary_id: int):
        return self.mock_data.pop(travel_diary_id, None)
