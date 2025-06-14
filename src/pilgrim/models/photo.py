from typing import Any

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from pilgrim.models.photo_in_entry import photo_entry_association
from ..database import Base


class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    filepath = Column(String)
    name = Column(String)
    addition_date = Column(String)
    caption = Column(String)
    entries = relationship(
        "Entry",
        secondary=photo_entry_association,
        back_populates="photos"
    )

    fk_travel_diary_id = Column(Integer, ForeignKey("travel_diaries.id"),nullable=False)

    def __init__(self, filepath, name, addition_date=None, caption=None, entries=None, **kw: Any):
        super().__init__(**kw)
        self.filepath = filepath
        self.name = name
        self.addition_date = addition_date
        self.caption = caption
        self.entries = entries
