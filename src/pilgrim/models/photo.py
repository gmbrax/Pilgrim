from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from pilgrim.models.photo_in_entry import photo_entry_association
from ..database import Base


class Photo(Base):
    __tablename__ = "photo"
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
