from typing import Any

from pilgrim.models.photo_in_entry import photo_entry_association
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from ..database import Base


class Entry(Base):
    __tablename__ = "entries"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    text = Column(String)
    date = Column(DateTime)
    photos = relationship(
        "Photo",
        secondary=photo_entry_association,
        back_populates="entries")
    fk_travel_diary_id = Column(Integer, ForeignKey("travel_diaries.id"), nullable=False)
    travel_diary = relationship("TravelDiary", back_populates="entries")

    def __init__(self, title: str, text: str, date: str, travel_diary_id: int, **kw: Any):
        super().__init__(**kw)
        self.title = title
        self.text = text
        self.date = date
        self.fk_travel_diary_id = travel_diary_id
