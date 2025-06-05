from typing import Any

from sqlalchemy import Column, String, Integer

from ..database import Base

class TravelDiary(Base):
    __tablename__ = "travel_diaries"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __init__(self, name: str, **kw: Any):
        super().__init__(**kw)
        self.name = name
