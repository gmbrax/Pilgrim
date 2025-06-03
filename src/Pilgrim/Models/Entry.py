from sqlalchemy import Column, Integer, String, ForeignKey

from Pilgrim import Base


class Entry(Base):
    __tablename__ = "Entry"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    text = Column(String)
    date = Column(String)
    fk_TravelDiary_id = Column(Integer, ForeignKey("TravelDiary.id"))
