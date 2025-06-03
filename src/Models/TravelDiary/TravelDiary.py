from sqlalchemy import Column, String, Integer

from src.Application.Application import Application

class TravelDiary(Application.database.Base):
    __tablename__ = "TravelDiary"
    id = Column(Integer, primary_key=True)
    name = Column(String)
