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
