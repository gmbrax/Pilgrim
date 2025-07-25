from typing import Any

from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from pilgrim.database import Base



class TravelDiary(Base):
    __tablename__ = "travel_diaries"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    directory_name = Column(String, nullable=False, unique=True)
    entries = relationship("Entry", back_populates="travel_diary", cascade="all, delete-orphan")
    photos = relationship("Photo", back_populates="travel_diary", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('directory_name', name='uq_travel_diary_directory_name'),
    )

    def __init__(self, name: str, directory_name: str = None, **kw: Any):
        super().__init__(**kw)
        self.name = name
        self.directory_name = directory_name  # Será definido pelo service

    def __repr__(self):
        return f"<TravelDiary(id={self.id}, name='{self.name}', directory_name='{self.directory_name}')>"
