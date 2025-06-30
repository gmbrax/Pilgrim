from typing import Any
from datetime import datetime
from pathlib import Path

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from pilgrim.models.photo_in_entry import photo_entry_association
from ..database import Base


class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    filepath = Column(String)
    name = Column(String)
    addition_date = Column(DateTime, default=datetime.now)
    caption = Column(String)
    entries = relationship(
        "Entry",
        secondary=photo_entry_association,
        back_populates="photos"
    )

    fk_travel_diary_id = Column(Integer, ForeignKey("travel_diaries.id"),nullable=False)

    def __init__(self, filepath, name, addition_date=None, caption=None, entries=None, fk_travel_diary_id=None, **kw: Any):
        super().__init__(**kw)
        # Convert Path to string if needed
        if isinstance(filepath, Path):
            self.filepath = str(filepath)
        else:
            self.filepath = filepath
        self.name = name
        self.addition_date = addition_date if addition_date is not None else datetime.now()
        self.caption = caption
        self.entries = entries if entries is not None else []
        if fk_travel_diary_id is not None:
            self.fk_travel_diary_id = fk_travel_diary_id
