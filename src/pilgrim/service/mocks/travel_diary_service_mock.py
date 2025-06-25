from pilgrim.service.travel_diary_service import TravelDiaryService
from pilgrim.models.travel_diary import TravelDiary
import asyncio


class TravelDiaryServiceMock(TravelDiaryService):
    def __init__(self):
        super().__init__(None)
        self.mock_data = {
            1: TravelDiary(id=1, name="Montreal"),
            2: TravelDiary(id=2, name="Rio de Janeiro"),
        }
        self._next_id = 3

    # Synchronous methods (original)
    def create(self, name: str):
        """Synchronous version"""
        new_travel_diary = TravelDiary(id=self._next_id, name=name)
        self.mock_data[self._next_id] = new_travel_diary
        self._next_id += 1
        return new_travel_diary

    def read_by_id(self, travel_id: int):
        """Synchronous version"""
        return self.mock_data.get(travel_id)

    def read_all(self):
        """Synchronous version"""
        return list(self.mock_data.values())

    def update(self, travel_diary_id: int, name: str):
        """Synchronous version"""
        item_to_update = self.mock_data.get(travel_diary_id)
        if item_to_update:
            item_to_update.name = name
            return item_to_update
        return None

    def delete(self, travel_diary_id: int):
        """Synchronous version"""
        return self.mock_data.pop(travel_diary_id, None)

    # Async methods (new)
    async def async_create(self, name: str):
        """Async version"""
        await asyncio.sleep(0.01)  # Simulates I/O
        return self.create(name)

    async def async_read_by_id(self, travel_id: int):
        """Async version"""
        await asyncio.sleep(0.01)  # Simulates I/O
        return self.read_by_id(travel_id)

    async def async_read_all(self):
        """Async version"""
        await asyncio.sleep(0.01)  # Simulates I/O
        return self.read_all()

    async def async_update(self, travel_diary_id: int, name: str):
        """Async version"""
        await asyncio.sleep(0.01)  # Simulates I/O
        return self.update(travel_diary_id, name)

    async def async_delete(self, travel_diary_id: int):
        """Async version"""
        await asyncio.sleep(0.01)  # Simulates I/O
        return self.delete(travel_diary_id)