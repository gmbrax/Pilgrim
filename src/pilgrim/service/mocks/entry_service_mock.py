from typing import List, Tuple
import asyncio
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
            4: Entry(title="Old Montreal", text="Exploring the historic district", date="29/07/2025",
                     travel_diary_id=1, id=4, photos=[]),
            5: Entry(title="Notre-Dame Basilica", text="Beautiful architecture", date="30/07/2025",
                     travel_diary_id=1, id=5, photos=[]),
            6: Entry(title="Parc Jean-Drapeau", text="Great views of the city", date="31/07/2025",
                     travel_diary_id=1, id=6, photos=[]),
            7: Entry(title="La Ronde", text="Amusement park fun", date="01/08/2025",
                     travel_diary_id=1, id=7, photos=[]),
            8: Entry(title="Biodome", text="Nature and science", date="02/08/2025",
                     travel_diary_id=1, id=8, photos=[]),
            9: Entry(title="Botanical Gardens", text="Peaceful walk", date="03/08/2025",
                     travel_diary_id=1, id=9, photos=[]),
            10: Entry(title="Olympic Stadium", text="Historic venue", date="04/08/2025",
                     travel_diary_id=1, id=10, photos=[]),
        }
        self._next_id = 11

    # Synchronous methods (kept for compatibility)
    def create(self, travel_diary_id: int, title: str, text: str, date: str) -> Entry:
        """Synchronous version"""
        new_entry = Entry(title, text, date, travel_diary_id, id=self._next_id)
        self.mock_data[self._next_id] = new_entry
        self._next_id += 1
        return new_entry

    def read_by_id(self, entry_id: int) -> Entry | None:
        """Synchronous version"""
        return self.mock_data.get(entry_id)

    def read_all(self) -> List[Entry]:
        """Synchronous version"""
        return list(self.mock_data.values())

    def read_by_travel_diary_id(self, travel_diary_id: int) -> List[Entry]:
        """Synchronous version - reads entries by diary"""
        return [entry for entry in self.mock_data.values() if entry.fk_travel_diary_id == travel_diary_id]

    def read_paginated(self, travel_diary_id: int, page: int = 1, page_size: int = 5) -> Tuple[List[Entry], int, int]:
        """Synchronous version - reads paginated entries by diary"""
        entries = self.read_by_travel_diary_id(travel_diary_id)
        entries.sort(key=lambda x: x.id, reverse=True)  # Most recent first
        
        total_entries = len(entries)
        total_pages = (total_entries + page_size - 1) // page_size
        
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        page_entries = entries[start_index:end_index]
        
        return page_entries, total_pages, total_entries

    def update(self, entry_src: Entry, entry_dst: Entry) -> Entry | None:
        """Synchronous version"""
        item_to_update = self.mock_data.get(entry_src.id)
        if item_to_update:
            item_to_update.title = entry_dst.title if entry_dst.title is not None else item_to_update.title
            item_to_update.text = entry_dst.text if entry_dst.text is not None else item_to_update.text
            item_to_update.date = entry_dst.date if entry_dst.date is not None else item_to_update.date
            item_to_update.fk_travel_diary_id = entry_dst.fk_travel_diary_id if (entry_dst.fk_travel_diary_id
                                                                                 is not None) else entry_dst.id
            item_to_update.photos.extend(entry_dst.photos)

            return item_to_update
        return None

    def delete(self, entry_src: Entry) -> Entry | None:
        """Synchronous version"""
        return self.mock_data.pop(entry_src.id, None)

    # Async methods (main)
    async def async_create(self, travel_diary_id: int, title: str, text: str, date: str) -> Entry:
        """Async version"""
        await asyncio.sleep(0.01)  # Simulates I/O
        return self.create(travel_diary_id, title, text, date)

    async def async_read_by_id(self, entry_id: int) -> Entry | None:
        """Async version"""
        await asyncio.sleep(0.01)  # Simulates I/O
        return self.read_by_id(entry_id)

    async def async_read_all(self) -> List[Entry]:
        """Async version"""
        await asyncio.sleep(0.01)  # Simulates I/O
        return self.read_all()

    async def async_read_by_travel_diary_id(self, travel_diary_id: int) -> List[Entry]:
        """Async version - reads entries by diary"""
        await asyncio.sleep(0.01)  # Simulates I/O
        return self.read_by_travel_diary_id(travel_diary_id)

    async def async_read_paginated(self, travel_diary_id: int, page: int = 1, page_size: int = 5) -> Tuple[List[Entry], int, int]:
        """Async version - reads paginated entries by diary"""
        await asyncio.sleep(0.01)  # Simulates I/O
        return self.read_paginated(travel_diary_id, page, page_size)

    async def async_update(self, entry_src: Entry, entry_dst: Entry) -> Entry | None:
        """Async version"""
        await asyncio.sleep(0.01)  # Simulates I/O
        return self.update(entry_src, entry_dst)

    async def async_delete(self, entry_src: Entry) -> Entry | None:
        """Async version"""
        await asyncio.sleep(0.01)  # Simulates I/O
        return self.delete(entry_src)