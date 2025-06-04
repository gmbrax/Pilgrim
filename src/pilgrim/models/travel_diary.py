from sqlalchemy import Column, String, Integer

from ..database import Base

class TravelDiary(Base):
    __tablename__ = "TravelDiary"
    id = Column(Integer, primary_key=True)
    name = Column(String)
