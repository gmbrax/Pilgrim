from typing import List
from pilgrim.service.entry_service import EntryService
from pilgrim.models.entry import Entry


class EntryServiceMock(EntryService):
    def __init__(self):
        super().__init__(None)

        self.mock_data = {
            1: Entry(title="The Adventure Begins", text="I'm hopping in the Plane to finally visit canadian lands",
                     date="26/07/2025", travel_diary_id=1, id=1,
                     photos=[]),
            2: Entry(title="The Landing", text="Finally on Canadian Soil", date="27/07/2025",
                     travel_diary_id=1, id=2,photos=[]),
            3: Entry(title="The Mount Royal", text="The Mount Royal is fucking awesome", date="28/07/2025",
                     travel_diary_id=1, id=3, photos=[]),
        }
        self._next_id = 4

    def create(self, travel_diary_id: int, title: str, text: str, date: str) -> Entry:
        new_entry = Entry(title, text, date, travel_diary_id, id=self._next_id)
        self.mock_data[self._next_id] = new_entry
        self._next_id += 1
        return new_entry

    def read_by_id(self, entry_id: int) -> Entry | None:
        return self.mock_data.get(entry_id)

    def read_all(self) -> List[Entry]:
        return list(self.mock_data.values())

    def update(self, entry_id: int, entry_dst: Entry) -> Entry | None:
        item_to_update = self.mock_data.get(entry_id)
        if item_to_update:
            item_to_update.title = entry_dst.title if entry_dst.title is not None else item_to_update.title
            item_to_update.text = entry_dst.text if entry_dst.text is not None else item_to_update.text
            item_to_update.date = entry_dst.date if entry_dst.date is not None else item_to_update.date
            item_to_update.fk_travel_diary_id = entry_dst.fk_travel_diary_id if (entry_dst.fk_travel_diary_id
                                                                                 is not None) else entry_dst.id
            item_to_update.photos.extend(entry_dst.photos)

            return item_to_update
        return None

    def delete(self, entry_id: int) -> Entry | None:
        return self.mock_data.pop(entry_id, None)