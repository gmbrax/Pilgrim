from sqlalchemy import Column, String, Integer

from Pilgrim import Application, Base


class TravelDiary(Base):
    __tablename__ = "TravelDiary"
    id = Column(Integer, primary_key=True)
    name = Column(String)
