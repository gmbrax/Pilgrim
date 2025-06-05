from typing import Any

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from pilgrim.models.photo_in_entry import photo_entry_association
from ..database import Base


class Entry(Base):
    __tablename__ = "Entry"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    text = Column(String)
    date = Column(String)
    photos = relationship(
        "Photo",
        secondary=photo_entry_association,
        back_populates="entries")
    fk_TravelDiary_id = Column(Integer, ForeignKey("TravelDiary.id"))
    def __init__(self, title: str, text: str, date: str, travel_diary_id: int, **kw: Any):
        super().__init__(**kw)
        self.title = title
        self.text = text
        self.date = date
        self.fk_TravelDiary_id = travel_diary_id


